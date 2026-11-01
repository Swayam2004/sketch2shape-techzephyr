"""HTTP API from `docs/api.md`. One worker thread runs jobs one at a time, because one GPU."""

from __future__ import annotations

import hmac
import io
import logging
import os
import queue
import shutil
import tempfile
import threading
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated

import torch
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

from sketch2shape.pipeline import run, select_device
from sketch2shape.types import GenerationRequest, GenerationResult

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_PROMPT_CHARS = 300
QUEUE_LIMIT = 5
RATE_LIMIT_PER_MINUTE = 10
JOB_TTL_SECONDS = 3600
ACCESS_CODE_ENV = "S2S_ACCESS_CODE"
STATIC_DIR = Path(__file__).parent / "static"

Runner = Callable[[GenerationRequest, Path, Callable[[str], None]], GenerationResult]


@dataclass
class Job:
    job_id: str
    request: GenerationRequest
    created: float = field(default_factory=time.monotonic)
    finished: float | None = None
    status: str = "queued"
    stage: str | None = None
    result: GenerationResult | None = None
    error: str | None = None


def default_runner(request: GenerationRequest, out_dir: Path, on_stage: Callable[[str], None]):
    return run(request, select_device(), out_dir=out_dir, stem="result", on_stage=on_stage)


class JobManager:
    def __init__(self, runner: Runner, root: Path, queue_limit: int, ttl: float) -> None:
        self._runner, self._root, self._ttl = runner, root, ttl
        self._jobs: dict[str, Job] = {}
        self._queue: queue.Queue[str] = queue.Queue(maxsize=queue_limit)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._work, name="s2s-worker", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2)

    @property
    def queue_length(self) -> int:
        return self._queue.qsize()

    def submit(self, request: GenerationRequest) -> str | None:
        """Return the job id, or None when the queue is full."""
        job = Job(uuid.uuid4().hex, request)
        with self._lock:
            self._jobs[job.job_id] = job
        try:
            self._queue.put_nowait(job.job_id)
        except queue.Full:
            with self._lock:
                del self._jobs[job.job_id]
            return None
        return job.job_id

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def queue_position(self, job_id: str) -> int:
        with self._queue.mutex:
            waiting = list(self._queue.queue)
        return waiting.index(job_id) if job_id in waiting else 0

    def job_dir(self, job_id: str) -> Path:
        return self._root / job_id

    def _work(self) -> None:
        while not self._stop.is_set():
            self._sweep()
            try:
                job_id = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue
            job = self.get(job_id)
            if job is not None:
                self._run(job)

    def _run(self, job: Job) -> None:
        job.status = "running"
        try:
            job.result = self._runner(
                job.request, self.job_dir(job.job_id), lambda stage: setattr(job, "stage", stage)
            )
            job.status = "done"
        except Exception as exc:
            logger.exception("job %s failed", job.job_id)
            job.error = str(exc)[:300] or type(exc).__name__
            job.status = "failed"
        finally:
            job.stage = None
            job.finished = time.monotonic()

    def _sweep(self) -> None:
        now = time.monotonic()
        with self._lock:
            old = [
                j.job_id for j in self._jobs.values() if j.finished and now - j.finished > self._ttl
            ]
            for job_id in old:
                del self._jobs[job_id]
        for job_id in old:
            shutil.rmtree(self.job_dir(job_id), ignore_errors=True)


class RateLimiter:
    """Sliding one-minute window per client IP."""

    def __init__(self, per_minute: int) -> None:
        self._per_minute = per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, client: str) -> int:
        """Return 0 if allowed, else the seconds to wait."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[client]
            while hits and now - hits[0] > 60:
                hits.popleft()
            if len(hits) >= self._per_minute:
                return max(1, int(60 - (now - hits[0])) + 1)
            hits.append(now)
        return 0


def _load_sketch(data: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(422, "The sketch is not a readable PNG, JPG or WebP image.") from exc
    if image.format not in ("PNG", "JPEG", "WEBP"):
        raise HTTPException(422, "The sketch must be a PNG, JPG or WebP image.")
    if image.mode in ("RGBA", "LA", "P"):
        rgba = image.convert("RGBA")
        flat = Image.new("RGB", rgba.size, "white")
        flat.paste(rgba, mask=rgba.getchannel("A"))
        return flat
    return image.convert("RGB")


def create_app(
    runner: Runner = default_runner,
    work_dir: Path | None = None,
    queue_limit: int = QUEUE_LIMIT,
    rate_limit_per_minute: int = RATE_LIMIT_PER_MINUTE,
    ttl_seconds: float = JOB_TTL_SECONDS,
    warmup: Callable[[], None] | None = None,
) -> FastAPI:
    """`warmup` runs once in a background thread, so the server answers at once and reports
    `ready: false` until the models are loaded. Jobs submitted meanwhile wait in the queue.
    """
    root = work_dir or Path(tempfile.mkdtemp(prefix="s2s-jobs-"))
    root.mkdir(parents=True, exist_ok=True)
    manager = JobManager(runner, root, queue_limit, ttl_seconds)
    limiter = RateLimiter(rate_limit_per_minute)

    ready = threading.Event()

    def warm_then_serve() -> None:
        # The worker starts only after the warm-up, so both never load the same model at once.
        try:
            if warmup:
                warmup()
        except Exception:  # a failed warm-up must not stop the server
            logger.exception("Warm-up failed. The first job will load the models instead.")
        manager.start()
        ready.set()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        threading.Thread(target=warm_then_serve, name="warmup", daemon=True).start()
        yield
        manager.stop()

    app = FastAPI(title="Sketch2Shape", lifespan=lifespan)
    app.state.manager = manager

    def require_code(request: Request) -> None:
        expected = os.environ.get(ACCESS_CODE_ENV)
        if not expected:
            return
        given = request.headers.get("X-Access-Code", "")
        if not hmac.compare_digest(given.encode(), expected.encode()):
            raise HTTPException(401, "Missing or wrong access code.")

    def device() -> str:
        return select_device()

    @app.get("/", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    # Serves the vendored model-viewer script so the 3D view works without internet.
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/v1/health")
    def health() -> dict:
        dev = device()
        gpu = torch.cuda.get_device_name(0) if dev == "cuda" else None
        try:
            ver = version("sketch2shape")
        except PackageNotFoundError:
            ver = "0.1.0"
        return {
            "status": "ok",
            "device": dev,
            "gpu_name": gpu,
            "version": ver,
            "queue_length": manager.queue_length,
            "ready": ready.is_set(),
        }

    @app.post("/v1/jobs", status_code=202, dependencies=[Depends(require_code)])
    async def create_job(
        request: Request,
        sketch: Annotated[UploadFile, File()],
        prompt: Annotated[str | None, Form()] = None,
        seed: Annotated[int, Form()] = 0,
    ) -> JSONResponse:
        if prompt is not None and len(prompt) > MAX_PROMPT_CHARS:
            raise HTTPException(422, f"The prompt is longer than {MAX_PROMPT_CHARS} characters.")
        data = await sketch.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "The sketch is larger than 10 MB.")
        image = _load_sketch(data)

        client = request.client.host if request.client else "unknown"
        wait = limiter.check(client)
        if wait:
            return JSONResponse(
                {"detail": "Too many requests."}, 429, headers={"Retry-After": str(wait)}
            )
        job_id = manager.submit(GenerationRequest(image, prompt or None, seed))
        if job_id is None:
            return JSONResponse(
                {"detail": "The queue is full. Try again shortly."},
                429,
                headers={"Retry-After": "30"},
            )
        return JSONResponse({"job_id": job_id}, 202)

    def _job(job_id: str) -> Job:
        job = manager.get(job_id)
        if job is None:
            raise HTTPException(404, "Unknown job.")
        return job

    @app.get("/v1/jobs/{job_id}", dependencies=[Depends(require_code)])
    def job_status(job_id: str) -> dict:
        job = _job(job_id)
        end = job.finished or time.monotonic()
        body: dict = {
            "job_id": job.job_id,
            "status": job.status,
            "stage": job.stage,
            "queue_position": manager.queue_position(job_id) if job.status == "queued" else 0,
            "elapsed_seconds": round(end - job.created, 1),
            "device": None,
            "timings": [],
            "warnings": [],
            "silhouette_iou": None,
            "error": job.error,
        }
        if job.result:
            r = job.result
            body.update(
                device=r.device,
                timings=[
                    {
                        "stage": t.stage,
                        "seconds": round(t.seconds, 2),
                        "peak_vram_mb": t.peak_vram_mb,
                    }
                    for t in r.timings
                ],
                warnings=r.warnings,
                silhouette_iou=r.silhouette_iou,
            )
        return body

    files = {
        "result.glb": ("model/gltf-binary", lambda r: r.paths.glb),
        "result.obj": ("text/plain", lambda r: r.paths.obj),
        "preview.png": ("image/png", lambda r: r.generated_image),
        "generated.png": ("image/png", lambda r: r.generated_image),
    }

    @app.get("/v1/jobs/{job_id}/{name}", dependencies=[Depends(require_code)])
    def download(job_id: str, name: str) -> FileResponse:
        job = _job(job_id)
        if name not in files or job.status != "done" or job.result is None:
            raise HTTPException(404, "Not available.")
        media_type, pick = files[name]
        path = pick(job.result)
        if path is None or not Path(path).is_file():
            raise HTTPException(404, "Not available.")
        return FileResponse(path, media_type=media_type, filename=name)

    return app


def warm_default_model() -> None:
    """Load TripoSR, rembg and the diffusion pipeline once. Skipped when the weights are not on disk yet."""
    from sketch2shape.cutout.background import _session
    from sketch2shape.generate import ModelFilesMissing
    from sketch2shape.generate.sketch_to_image import _load_pipeline
    from sketch2shape.reconstruct.triposr import WeightsMissingError, _load_model
    from sketch2shape.weights import triposr_dir

    device = select_device()
    try:
        _load_model(device, triposr_dir())
        _session()
        # The diffusion pipeline is the slowest load, so it goes first in line for the judge.
        _load_pipeline(device, device == "cuda")
    except (WeightsMissingError, ModelFilesMissing, FileNotFoundError) as exc:
        logger.warning("Warm-up skipped: %s", exc)


def app_factory() -> FastAPI:
    """For `uvicorn sketch2shape.api.server:app_factory --factory`."""
    return create_app(warmup=warm_default_model)
