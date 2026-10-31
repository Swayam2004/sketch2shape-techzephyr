import io
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from sketch2shape.api import create_app
from sketch2shape.types import (
    ExportPaths,
    GenerationResult,
    StageTiming,
    ValidationReport,
)


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), "white").save(buf, "PNG")
    return buf.getvalue()


def _fake_runner(request, device, out_dir: Path, stem, on_stage=None) -> GenerationResult:
    for stage in ("preprocess", "generate"):
        if on_stage:
            on_stage(stage)
    out_dir.mkdir(parents=True, exist_ok=True)
    glb, png = out_dir / "result.glb", out_dir / "result_generated.png"
    glb.write_bytes(b"glTF")
    png.write_bytes(b"png")
    return GenerationResult(
        paths=ExportPaths(glb=glb, obj=None),
        generated_image=png,
        seed=request.seed,
        device=device,
        timings=[StageTiming("generate", 1.234, None)],
        validation=ValidationReport(True, 3, 1, True, True),
        silhouette_iou=0.8,
        warnings=["Running on CPU."],
    )


def _client(tmp_path, **kwargs) -> TestClient:
    kwargs.setdefault("runner", _fake_runner)
    app = create_app(device="cpu", work_dir=tmp_path / "jobs", **kwargs)
    return TestClient(app)


def _submit(client, headers=None, **form):
    return client.post(
        "/v1/jobs", files={"sketch": ("s.png", _png(), "image/png")}, data=form, headers=headers
    )


def _wait_done(client, job_id, headers=None):
    for _ in range(100):
        body = client.get(f"/v1/jobs/{job_id}", headers=headers).json()
        if body["status"] in ("done", "failed"):
            return body
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def test_job_roundtrip(tmp_path) -> None:
    with _client(tmp_path) as client:
        resp = _submit(client, prompt="a chair", seed="4")
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]
        body = _wait_done(client, job_id)
        assert body["status"] == "done" and body["silhouette_iou"] == 0.8
        assert body["warnings"] == ["Running on CPU."]
        assert body["timings"][0]["stage"] == "generate"
        assert client.get(f"/v1/jobs/{job_id}/result.glb").content == b"glTF"
        assert client.get(f"/v1/jobs/{job_id}/preview.png").status_code == 200
        assert client.get(f"/v1/jobs/{job_id}/result.obj").status_code == 404


def test_result_before_done_is_404(tmp_path) -> None:
    release = threading.Event()

    def slow(request, device, out_dir, stem, on_stage=None):
        release.wait(5)
        return _fake_runner(request, device, out_dir, stem, on_stage)

    with _client(tmp_path, runner=slow) as client:
        job_id = _submit(client).json()["job_id"]
        assert client.get(f"/v1/jobs/{job_id}/result.glb").status_code == 404
        release.set()
        _wait_done(client, job_id)


def test_failed_job_reports_error(tmp_path) -> None:
    def boom(*args, **kwargs):
        raise RuntimeError("weights missing")

    with _client(tmp_path, runner=boom) as client:
        body = _wait_done(client, _submit(client).json()["job_id"])
        assert body["status"] == "failed" and body["error"] == "weights missing"
        # The worker survives a failure.
        assert client.get("/v1/health").json()["status"] == "ok"


def test_access_code(tmp_path) -> None:
    with _client(tmp_path, access_code="letmein") as client:
        assert _submit(client).status_code == 401
        assert _submit(client, headers={"X-Access-Code": "nope"}).status_code == 401
        assert client.get("/v1/health").status_code == 200
        ok = _submit(client, headers={"X-Access-Code": "letmein"})
        assert ok.status_code == 202


def test_queue_limit_returns_429(tmp_path) -> None:
    release = threading.Event()

    def blocked(request, device, out_dir, stem, on_stage=None):
        release.wait(5)
        return _fake_runner(request, device, out_dir, stem, on_stage)

    with _client(tmp_path, runner=blocked, queue_limit=2) as client:
        assert _submit(client).status_code == 202
        assert _submit(client).status_code == 202
        full = _submit(client)
        assert full.status_code == 429 and "Retry-After" in full.headers
        release.set()


def test_rate_limit_per_ip(tmp_path) -> None:
    with _client(tmp_path, rate_limit=2) as client:
        assert _submit(client).status_code == 202
        assert _submit(client).status_code == 202
        assert _submit(client).status_code == 429


@pytest.mark.parametrize(
    ("files", "data", "code"),
    [
        ({"sketch": ("s.png", b"not an image", "image/png")}, {}, 422),
        ({"sketch": ("s.png", _png(), "image/png")}, {"prompt": "x" * 301}, 422),
    ],
)
def test_bad_input(tmp_path, files, data, code) -> None:
    with _client(tmp_path) as client:
        assert client.post("/v1/jobs", files=files, data=data).status_code == code


def test_unknown_job_is_404(tmp_path) -> None:
    with _client(tmp_path) as client:
        assert client.get("/v1/jobs/nope").status_code == 404


def test_finished_jobs_expire(tmp_path) -> None:
    with _client(tmp_path, ttl=0.0) as client:
        job_id = _submit(client).json()["job_id"]
        _wait_done(client, job_id)
        time.sleep(0.05)
        client.app.state.manager.expire()
        assert client.get(f"/v1/jobs/{job_id}").status_code == 404
        assert not (tmp_path / "jobs" / job_id).exists()


def test_warm_runs_at_startup(tmp_path) -> None:
    calls: list[str] = []
    with _client(tmp_path, warm=calls.append):
        pass
    assert calls == ["cpu"]
