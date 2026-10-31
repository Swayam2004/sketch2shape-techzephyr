"""HTTP API from `docs/api.md`. Submit a job, poll it, download the mesh.

One worker thread runs jobs one at a time because a single GPU cannot overlap two TripoSR runs.
Finished jobs and their files are deleted an hour after they end.
"""

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
from PIL import Image, UnidentifiedImageError

from sketch2shape import pipeline
from sketch2shape.types import Device, GenerationRequest, GenerationResult

logger = logging.getLogger(__name__)

ACCESS_CODE_ENV = "S2S_ACCESS_CODE"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_PROMPT_CHARS = 300
QUEUE_LIMIT = 5
RATE_LIMIT = 10  # job submissions per IP per window
RATE_WINDOW_SECONDS = 60.0
JOB_TTL_SECONDS = 3600.0

# Runner signature. Tests pass a fake, production uses `pipeline.run`.
Runner = Callable[..., GenerationResult]


@dataclass
class Job:
    job_id: str
    request: GenerationRequest
    out_dir: Path
    created: float = field(default_factory=time.monotonic)
    started: float | None = None
    finished: float | None = None
    status: str = "queued"
    stage: str | None = None
    result: GenerationResult | None = None
    error: str | None = None


def _package_version() -> str:
    try:
        return version("sketch2shape")
    except PackageNotFoundError:
        return "0.0.0"


def _gpu_name() -> str | None:
    return torch.cuda.get_device_name(0) if torch.cuda.is_available() else None


class JobManager:
    """Holds jobs, runs them on one thread, and expires old ones."""

    def __init__(
        self,
        runner: Runner,
        device: Device,
        work_dir: Path,
        queue_limit: int = QUEUE_LIMIT,
        ttl: float = JOB_TTL_SECONDS,
    ) -> None:
        self.runner = runner
        self.device = device
        self.work_dir = work_dir
        self.queue_limit = queue_limit
        self.ttl = ttl
        self.jobs: dict[str, Job] = {}
        self._pending: queue.Queue[str] = queue.Queue()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._worker, name="s2s-worker", daemon=True)

    def start(self) -> None:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._pending.put("")  # wake the worker
        self._thread.join(timeout=5)

    def queue_length(self) -> int:
        with self._lock:
            return sum(1 for j in self.jobs.values() if j.status in ("queued", "running"))

    def submit(self, request: GenerationRequest) -> Job | None:
        """Return the new job, or None when the queue is full."""
        self.expire()
        with self._lock:
            active = sum(1 for j in self.jobs.values() if j.status in ("queued", "running"))
            if active >= self.queue_limit:
                return None
            job_id = uuid.uuid4().hex
            job = Job(job_id, request, self.work_dir / job_id)
            self.jobs[job_id] = job
        self._pending.put(job_id)
        return job

    def queue_position(self, job: Job) -> int:
        if job.status != "queued":
            return 0
        with self._lock:
            ahead = [
                j for j in self.jobs.values() if j.status == "queued" and j.created < job.created
            ]
            running = any(j.status == "running" for j in self.jobs.values())
        return len(ahead) + (1 if running else 0)

    def expire(self) -> None:
        now = time.monotonic()
        with self._lock:
            old = [
                jid
                for jid, j in self.jobs.items()
                if j.finished is not None and now - j.finished > self.ttl
            ]
            gone = [self.jobs.pop(jid) for jid in old]
        for job in gone:
            shutil.rmtree(job.out_dir, ignore_errors=True)

    def _worker(self) -> None:
        while not self._stop.is_set():
            job_id = self._pending.get()
            if not job_id or self._stop.is_set():
                continue
            job = self.jobs.get(job_id)
            if job is None:
                continue
            job.status, job.started = "running", time.monotonic()

            def set_stage(stage: str, job: Job = job) -> None:
                job.stage = stage

            try:
                job.result = self.runner(
                    job.request, self.device, job.out_dir, "result", on_stage=set_stage
                )
                job.status = "done"
            except Exception as exc:
                logger.exception("job %s failed", job.job_id)
                job.error = _user_message(exc)
                job.status = "failed"
            finally:
                job.finished = time.monotonic()
                job.stage = None


def _user_message(exc: Exception) -> str:
    text = str(exc).strip() or exc.__class__.__name__
    return text if len(text) <= 300 else text[:297] + "..."


class RateLimiter:
    """Sliding window per client IP."""

    def __init__(self, limit: int, window: float) -> None:
        self.limit, self.window = limit, window
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, client: str) -> float | None:
        """Return None if allowed, else the seconds to wait."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[client]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return max(1.0, self.window - (now - hits[0]))
            hits.append(now)
            return None


def create_app(
    runner: Runner | None = None,
    device: Device | None = None,
    work_dir: Path | None = None,
    access_code: str | None = None,
    queue_limit: int = QUEUE_LIMIT,
    rate_limit: int = RATE_LIMIT,
    warm: Callable[[Device], None] | None = None,
    ttl: float = JOB_TTL_SECONDS,
) -> FastAPI:
    """Build the app. Production calls `create_app()`, tests inject a fake runner."""
    chosen_device = device or pipeline.select_device()
    code = access_code if access_code is not None else os.environ.get(ACCESS_CODE_ENV) or None
    manager = JobManager(
        runner or pipeline.run,
        chosen_device,
        work_dir or Path(tempfile.gettempdir()) / "sketch2shape-jobs",
        queue_limit,
        ttl,
    )
    limiter = RateLimiter(rate_limit, RATE_WINDOW_SECONDS)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if warm is not None:
            warm(chosen_device)
        manager.start()
        yield
        manager.stop()

    app = FastAPI(title="Sketch2Shape AI", version=_package_version(), lifespan=lifespan)
    app.state.manager = manager

    def require_code(request: Request) -> None:
        if code is None:
            return
        given = request.headers.get("X-Access-Code", "")
        if not hmac.compare_digest(given.encode(), code.encode()):
            raise HTTPException(status_code=401, detail="Missing or wrong access code.")

    def get_job(job_id: str) -> Job:
        job = manager.jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Unknown or expired job.")
        return job

    @app.get("/v1/health")
    def health() -> dict:
        return {
            "status": "ok",
            "device": chosen_device,
            "gpu_name": _gpu_name(),
            "version": _package_version(),
            "queue_length": manager.queue_length(),
        }

    @app.post("/v1/jobs", status_code=202, dependencies=[Depends(require_code)])
    async def create_job(
        request: Request,
        sketch: Annotated[UploadFile, File()],
        prompt: Annotated[str | None, Form()] = None,
        seed: Annotated[int, Form()] = 0,
    ):
        client = request.client.host if request.client else "unknown"
        wait = limiter.check(client)
        if wait is not None:
            return JSONResponse(
                {"detail": "Too many requests."}, 429, headers={"Retry-After": str(int(wait))}
            )
        if prompt is not None and len(prompt) > MAX_PROMPT_CHARS:
            raise HTTPException(422, f"Prompt is longer than {MAX_PROMPT_CHARS} characters.")
        data = await sketch.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "Sketch is larger than 10 MB.")
        try:
            image = Image.open(io.BytesIO(data))
            image.load()
        except (UnidentifiedImageError, OSError) as exc:
            raise HTTPException(422, "Sketch is not a readable PNG, JPG or WebP image.") from exc
        job = manager.submit(GenerationRequest(image, prompt or None, seed))
        if job is None:
            return JSONResponse(
                {"detail": "The queue is full. Try again shortly."},
                429,
                headers={"Retry-After": "30"},
            )
        return {"job_id": job.job_id}

    @app.get("/v1/jobs/{job_id}", dependencies=[Depends(require_code)])
    def job_status(job_id: str) -> dict:
        job = get_job(job_id)
        end = job.finished or time.monotonic()
        start = job.started if job.started is not None else job.created
        body: dict = {
            "job_id": job.job_id,
            "status": job.status,
            "stage": job.stage,
            "queue_position": manager.queue_position(job),
            "elapsed_seconds": round(end - start, 1) if job.status != "queued" else 0.0,
            "device": chosen_device,
            "timings": [],
            "warnings": [],
            "silhouette_iou": None,
            "error": job.error,
        }
        if job.result is not None:
            body["timings"] = [
                {"stage": t.stage, "seconds": round(t.seconds, 2), "peak_vram_mb": t.peak_vram_mb}
                for t in job.result.timings
            ]
            body["warnings"] = job.result.warnings
            body["silhouette_iou"] = job.result.silhouette_iou
        return body

    def artifact(job_id: str, which: str) -> FileResponse:
        job = get_job(job_id)
        result = job.result
        if job.status != "done" or result is None:
            raise HTTPException(404, "The result is not ready.")
        path = {
            "glb": result.paths.glb,
            "obj": result.paths.obj,
            "png": result.generated_image,
        }[which]
        if path is None or not Path(path).is_file():
            raise HTTPException(404, f"This job has no {which} file.")
        media = {
            "glb": "model/gltf-binary",
            "obj": "text/plain",
            "png": "image/png",
        }[which]
        return FileResponse(path, media_type=media, filename=Path(path).name)

    @app.get("/v1/jobs/{job_id}/result.glb", dependencies=[Depends(require_code)])
    def result_glb(job_id: str) -> FileResponse:
        return artifact(job_id, "glb")

    @app.get("/v1/jobs/{job_id}/result.obj", dependencies=[Depends(require_code)])
    def result_obj(job_id: str) -> FileResponse:
        return artifact(job_id, "obj")

    @app.get("/v1/jobs/{job_id}/preview.png", dependencies=[Depends(require_code)])
    def preview_png(job_id: str) -> FileResponse:
        return artifact(job_id, "png")

    @app.get("/v1/jobs/{job_id}/generated.png", dependencies=[Depends(require_code)])
    def generated_png(job_id: str) -> FileResponse:
        return artifact(job_id, "png")

    return app


def _warm_default(device: Device) -> None:
    from sketch2shape.reconstruct import warm_up

    warm_up(device)


def app_factory() -> FastAPI:
    """Entry point for `uvicorn sketch2shape.api.server:app_factory --factory`."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    return create_app(warm=_warm_default)
