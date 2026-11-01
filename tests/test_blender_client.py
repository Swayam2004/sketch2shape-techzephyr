"""Tests for the Blender add-on's HTTP client. Loaded by path because blender_addon is not a package."""

import importlib.util
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

CLIENT_PATH = (
    Path(__file__).resolve().parents[1] / "blender_addon" / "sketch2shape_addon" / "client.py"
)
spec = importlib.util.spec_from_file_location("s2s_blender_client", CLIENT_PATH)
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)


class FakeServer:
    """Minimal stand-in for the API in docs/api.md. Records POSTs for the assertions."""

    def __init__(self, statuses: list[dict], access_code: str = "") -> None:
        self.statuses = statuses
        self.access_code = access_code
        self.posts: list[tuple[dict, bytes]] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args) -> None:
                pass

            def _reply(self, code: int, body: bytes, ctype: str = "application/json") -> None:
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _authorised(self) -> bool:
                ok = not outer.access_code or self.headers.get("X-Access-Code") == outer.access_code
                if not ok:
                    self._reply(401, b'{"detail": "bad code"}')
                return ok

            def do_POST(self) -> None:
                body = self.rfile.read(int(self.headers["Content-Length"]))
                if not self._authorised():
                    return
                outer.posts.append((dict(self.headers), body))
                self._reply(202, json.dumps({"job_id": "job1"}).encode())

            def do_GET(self) -> None:
                if not self._authorised():
                    return
                if self.path.endswith("result.glb"):
                    self._reply(200, b"glTF-bytes", "model/gltf-binary")
                else:
                    status = outer.statuses.pop(0) if len(outer.statuses) > 1 else outer.statuses[0]
                    self._reply(200, json.dumps(status).encode())

        self.httpd = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def make_server():
    servers: list[FakeServer] = []

    def make(statuses: list[dict], access_code: str = "") -> FakeServer:
        servers.append(FakeServer(statuses, access_code))
        return servers[-1]

    yield make
    for server in servers:
        server.close()


def _png(tmp_path: Path) -> Path:
    sketch = tmp_path / "chair.png"
    sketch.write_bytes(b"\x89PNGfake")
    return sketch


def test_poll_interval_follows_the_api_rules() -> None:
    assert client.poll_interval(0) == 1.0
    assert client.poll_interval(9.9) == 1.0
    assert client.poll_interval(10) == 3.0
    assert client.poll_interval(500) == 3.0


def test_submit_sends_sketch_prompt_seed_and_access_code(make_server, tmp_path) -> None:
    server = make_server([{"status": "done"}], access_code="letmein")
    job_id = client.submit_job(server.url, _png(tmp_path), "a wooden chair", 7, "letmein")
    assert job_id == "job1"
    headers, body = server.posts[0]
    assert b'name="prompt"' in body and b"a wooden chair" in body
    assert b'name="seed"' in body and b"\r\n7\r\n" in body
    assert b'name="sketch"; filename="chair.png"' in body and b"\x89PNGfake" in body
    assert headers["Content-Type"].startswith("multipart/form-data; boundary=")


def test_empty_prompt_is_left_out(make_server, tmp_path) -> None:
    server = make_server([{"status": "done"}])
    client.submit_job(server.url, _png(tmp_path), "   ", 0)
    assert b'name="prompt"' not in server.posts[0][1]


def test_wrong_access_code_gives_a_readable_error(make_server, tmp_path) -> None:
    server = make_server([{"status": "done"}], access_code="right")
    with pytest.raises(client.ClientError, match="access code"):
        client.submit_job(server.url, _png(tmp_path), "", 0, "wrong")


def test_server_not_running_says_how_to_start_it(tmp_path) -> None:
    with pytest.raises(client.ClientError, match="sketch2shape serve"):
        client.submit_job("http://127.0.0.1:9", _png(tmp_path), "", 0)


def test_wait_polls_until_done_and_reports_updates(make_server) -> None:
    server = make_server(
        [
            {"status": "queued", "stage": None},
            {"status": "running", "stage": "generate"},
            {"status": "done", "stage": None, "warnings": ["Running on CPU."]},
        ]
    )
    seen: list[str] = []
    sleeps: list[float] = []
    job = client.wait_for_job(
        server.url, "job1", on_update=lambda j: seen.append(j["status"]), sleep=sleeps.append
    )
    assert job["warnings"] == ["Running on CPU."]
    assert seen == ["queued", "running", "done"]
    assert sleeps == [1.0, 1.0]


def test_failed_job_raises_with_the_server_message(make_server) -> None:
    server = make_server([{"status": "failed", "error": "Sketch is blank."}])
    with pytest.raises(client.ClientError, match="Sketch is blank"):
        client.wait_for_job(server.url, "job1", sleep=lambda s: None)


def test_wait_gives_up_after_the_timeout(make_server) -> None:
    server = make_server([{"status": "running"}])
    now = [0.0]

    def fake_sleep(seconds: float) -> None:
        now[0] += seconds

    with pytest.raises(client.ClientError, match="Gave up after 15 minutes"):
        client.wait_for_job(server.url, "job1", sleep=fake_sleep, clock=lambda: now[0])
    assert now[0] >= 900


def test_download_writes_the_glb(make_server, tmp_path) -> None:
    server = make_server([{"status": "done"}])
    path = client.download_result(server.url, "job1", tmp_path / "out")
    assert path.read_bytes() == b"glTF-bytes"
    assert path.suffix == ".glb"
