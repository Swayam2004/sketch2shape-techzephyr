import io
import threading
import time
from pathlib import Path

import pytest
import trimesh
from fastapi.testclient import TestClient
from PIL import Image

from sketch2shape.api import create_app
from sketch2shape.export import save_mesh, validate_mesh
from sketch2shape.types import GenerationRequest, GenerationResult, StageTiming


def _png(mode: str = "RGB", size: int = 32) -> bytes:
    buf = io.BytesIO()
    Image.new(mode, (size, size), "white").save(buf, format="PNG")
    return buf.getvalue()


def fake_runner(request: GenerationRequest, out_dir: Path, on_stage) -> GenerationResult:
    on_stage("reconstruct")
    box = trimesh.creation.box()
    box.visual.vertex_colors = [200, 50, 50, 255]
    paths = save_mesh(box, out_dir, "result")
    gen = out_dir / "result_generated.png"
    request.sketch.save(gen)
    return GenerationResult(
        paths,
        gen,
        request.seed,
        "cpu",
        [StageTiming("reconstruct", 0.1)],
        validate_mesh(paths.glb),
        0.8,
        ["Running on CPU."],
    )


def _wait(client: TestClient, job_id: str, headers=None) -> dict:
    for _ in range(100):
        body = client.get(f"/v1/jobs/{job_id}", headers=headers).json()
        if body["status"] in ("done", "failed"):
            return body
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def _post(client: TestClient, data: bytes | None = None, headers=None, **form):
    return client.post(
        "/v1/jobs",
        files={"sketch": ("s.png", data or _png(), "image/png")},
        data=form,
        headers=headers,
    )


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(fake_runner, tmp_path)) as c:
        yield c


def test_health(client) -> None:
    body = client.get("/v1/health").json()
    assert body["status"] == "ok" and body["device"] in ("cuda", "cpu")


def test_job_lifecycle_and_downloads(client) -> None:
    response = _post(client, prompt="a red box", seed="7")
    assert response.status_code == 202
    body = _wait(client, response.json()["job_id"])
    assert body["status"] == "done"
    assert body["device"] == "cpu" and body["warnings"] == ["Running on CPU."]
    assert body["silhouette_iou"] == 0.8 and body["timings"][0]["stage"] == "reconstruct"
    job = body["job_id"]
    for name, kind in [("result.glb", "model/gltf-binary"), ("preview.png", "image/png")]:
        r = client.get(f"/v1/jobs/{job}/{name}")
        assert r.status_code == 200 and r.headers["content-type"].startswith(kind)
    assert client.get(f"/v1/jobs/{job}/secret.txt").status_code == 404


def test_results_404_before_done(tmp_path) -> None:
    gate = threading.Event()

    def slow(request, out_dir, on_stage):
        gate.wait(5)
        return fake_runner(request, out_dir, on_stage)

    with TestClient(create_app(slow, tmp_path)) as c:
        job = _post(c).json()["job_id"]
        assert c.get(f"/v1/jobs/{job}/result.glb").status_code == 404
        gate.set()
        assert _wait(c, job)["status"] == "done"


def test_failed_job_reports_error(tmp_path) -> None:
    def boom(request, out_dir, on_stage):
        raise RuntimeError("TripoSR produced an empty mesh.")

    with TestClient(create_app(boom, tmp_path)) as c:
        body = _wait(c, _post(c).json()["job_id"])
    assert body["status"] == "failed" and "empty mesh" in body["error"]


def test_access_code(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("S2S_ACCESS_CODE", "letmein")
    with TestClient(create_app(fake_runner, tmp_path)) as c:
        assert c.get("/v1/health").status_code == 200
        assert _post(c).status_code == 401
        assert _post(c, headers={"X-Access-Code": "wrong"}).status_code == 401
        ok = _post(c, headers={"X-Access-Code": "letmein"})
        assert ok.status_code == 202
        job = ok.json()["job_id"]
        assert c.get(f"/v1/jobs/{job}").status_code == 401


def test_queue_full_returns_429(tmp_path) -> None:
    gate = threading.Event()

    def slow(request, out_dir, on_stage):
        gate.wait(5)
        return fake_runner(request, out_dir, on_stage)

    with TestClient(create_app(slow, tmp_path, queue_limit=1, rate_limit_per_minute=100)) as c:
        codes = [_post(c).status_code for _ in range(4)]
        gate.set()
    assert 429 in codes and codes[0] == 202


def test_rate_limit_returns_429_with_retry_after(tmp_path) -> None:
    with TestClient(create_app(fake_runner, tmp_path, rate_limit_per_minute=2)) as c:
        assert [_post(c).status_code for _ in range(2)] == [202, 202]
        r = _post(c)
    assert r.status_code == 429 and int(r.headers["Retry-After"]) >= 1


@pytest.mark.parametrize(
    ("data", "form", "code"),
    [(b"not an image", {}, 422), (None, {"prompt": "x" * 301}, 422)],
)
def test_bad_input_is_422(client, data, form, code) -> None:
    assert _post(client, data, **form).status_code == code


def test_oversize_upload_is_413(client) -> None:
    assert _post(client, b"\0" * (10 * 1024 * 1024 + 2)).status_code == 413


def test_transparent_png_is_accepted(client) -> None:
    assert _post(client, _png("RGBA")).status_code == 202


def test_old_jobs_are_removed(tmp_path) -> None:
    with TestClient(create_app(fake_runner, tmp_path, ttl_seconds=0.1)) as c:
        job = _post(c).json()["job_id"]
        _wait(c, job)
        time.sleep(1.5)
        assert c.get(f"/v1/jobs/{job}").status_code == 404
        assert not (tmp_path / job).exists()


def test_dashboard_is_served(client) -> None:
    r = client.get("/")
    assert r.status_code == 200 and "Sketch2Shape dashboard" in r.text


def test_server_answers_while_warming_and_runs_queued_jobs_after(tmp_path) -> None:
    release = threading.Event()
    with TestClient(create_app(fake_runner, tmp_path, warmup=release.wait)) as c:
        assert c.get("/v1/health").json()["ready"] is False
        job_id = _post(c).json()["job_id"]
        time.sleep(0.2)
        assert c.get(f"/v1/jobs/{job_id}").json()["status"] == "queued"
        release.set()
        assert _wait(c, job_id)["status"] == "done"
        assert c.get("/v1/health").json()["ready"] is True


def test_failed_warmup_does_not_block_jobs(tmp_path) -> None:
    def broken() -> None:
        raise RuntimeError("no weights")

    with TestClient(create_app(fake_runner, tmp_path, warmup=broken)) as c:
        job_id = _post(c).json()["job_id"]
        assert _wait(c, job_id)["status"] == "done"
        assert c.get("/v1/health").json()["ready"] is True
