"""HTTP client for the local Sketch2Shape server. Standard library only, because Blender ships its
own Python without requests or httpx. Contract: docs/api.md.

This file has no bpy import, so the repo tests run it outside Blender.
"""

from __future__ import annotations

import json
import mimetypes
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable
from pathlib import Path

DEFAULT_URL = "http://127.0.0.1:7860"
POLL_FAST_SECONDS = 1.0
POLL_SLOW_SECONDS = 3.0
FAST_PHASE_SECONDS = 10.0
TIMEOUT_SECONDS = 15 * 60
REQUEST_TIMEOUT_SECONDS = 30


class ClientError(RuntimeError):
    """Something a user can act on, such as a wrong access code or a server that is not running."""


def poll_interval(elapsed: float) -> float:
    """1 s for the first 10 s, then 3 s, as docs/api.md asks."""
    return POLL_FAST_SECONDS if elapsed < FAST_PHASE_SECONDS else POLL_SLOW_SECONDS


def build_multipart(
    fields: dict[str, str], file_field: str, filename: str, content: bytes, content_type: str
) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    parts: list[bytes] = []
    for name, value in fields.items():
        parts += [
            f"--{boundary}".encode(),
            f'Content-Disposition: form-data; name="{name}"'.encode(),
            b"",
            value.encode("utf-8"),
        ]
    parts += [
        f"--{boundary}".encode(),
        f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"'.encode(),
        f"Content-Type: {content_type}".encode(),
        b"",
        content,
        f"--{boundary}--".encode(),
        b"",
    ]
    return b"\r\n".join(parts), f"multipart/form-data; boundary={boundary}"


def _open(request: urllib.request.Request) -> bytes:
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:200]
        if exc.code == 401:
            raise ClientError(
                "The server rejected the access code. Check it in the panel."
            ) from exc
        if exc.code == 429:
            wait = exc.headers.get("Retry-After", "a few")
            raise ClientError(f"The server is busy. Try again in {wait} seconds.") from exc
        raise ClientError(f"Server error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ClientError(
            f"Cannot reach {request.full_url}. Start the server with `uv run sketch2shape serve`."
        ) from exc


def _headers(access_code: str) -> dict[str, str]:
    return {"X-Access-Code": access_code} if access_code else {}


def submit_job(base_url: str, sketch: Path, prompt: str, seed: int, access_code: str = "") -> str:
    content_type = mimetypes.guess_type(sketch.name)[0] or "application/octet-stream"
    fields = {"seed": str(seed)}
    if prompt.strip():
        fields["prompt"] = prompt.strip()
    body, header = build_multipart(fields, "sketch", sketch.name, sketch.read_bytes(), content_type)
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/jobs",
        data=body,
        method="POST",
        headers={"Content-Type": header, **_headers(access_code)},
    )
    return json.loads(_open(request))["job_id"]


def get_job(base_url: str, job_id: str, access_code: str = "") -> dict:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/jobs/{job_id}", headers=_headers(access_code)
    )
    return json.loads(_open(request))


def download_result(
    base_url: str, job_id: str, dest_dir: Path, name: str = "result.glb", access_code: str = ""
) -> Path:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/jobs/{job_id}/{name}", headers=_headers(access_code)
    )
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{job_id}_{name}"
    path.write_bytes(_open(request))
    return path


def wait_for_job(
    base_url: str,
    job_id: str,
    access_code: str = "",
    on_update: Callable[[dict], None] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    timeout: float = TIMEOUT_SECONDS,
) -> dict:
    """Poll until the job is done. Raises ClientError on failure or after the timeout."""
    started = clock()
    while True:
        job = get_job(base_url, job_id, access_code)
        if on_update:
            on_update(job)
        if job["status"] == "done":
            return job
        if job["status"] == "failed":
            raise ClientError(job.get("error") or "The job failed without a message.")
        elapsed = clock() - started
        if elapsed >= timeout:
            raise ClientError(
                f"Gave up after {int(timeout // 60)} minutes. The server may be stuck."
            )
        sleep(poll_interval(elapsed))
