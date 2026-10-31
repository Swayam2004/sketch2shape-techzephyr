# HTTP API contract

Owner. Swayam builds the server in `src/sketch2shape/api/`. Disha's UI and Udit's Blender add-on are clients. Until the server exists, clients code against this file and a stub.

Why jobs and polling. The hosted proxies cut a single request at 100 to 150 seconds, and CPU generation can take minutes. A client submits a job, then polls.

## Auth

Every request except `/v1/health` carries the header `X-Access-Code: <code>` when the server has `S2S_ACCESS_CODE` set. A missing or wrong code returns 401. The code is a throwaway string that goes in the README and the submission form, never a cloud credential.

## Endpoints

### POST /v1/jobs

Multipart form.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `sketch` | file (PNG, JPG, WebP) | yes | Up to 10 MB. Transparent PNGs are fine. |
| `prompt` | string | no | Up to 300 characters. |
| `seed` | integer | no | Default 0. |

Returns `202` with `{"job_id": "<uuid>"}`. Returns `429` when the queue is full or the caller is rate limited, with a `Retry-After` header.

### GET /v1/jobs/{job_id}

```json
{
  "job_id": "…",
  "status": "queued | running | done | failed",
  "stage": "preprocess | generate | cutout | reconstruct | export | null",
  "queue_position": 0,
  "elapsed_seconds": 12.4,
  "device": "cuda | cpu",
  "timings": [{"stage": "generate", "seconds": 8.1, "peak_vram_mb": 3900}],
  "warnings": ["Running on CPU. Results may be slow."],
  "silhouette_iou": 0.82,
  "error": null
}
```

`error` is a short message a user can read. `silhouette_iou` appears only when `done`.

### GET /v1/jobs/{job_id}/result.glb, result.obj, preview.png, generated.png

Available when `status` is `done`. `404` before that. `preview.png` is the generated image (not a render of the mesh). `generated.png` is the same image at full size.

### GET /v1/health

```json
{"status": "ok", "device": "cuda | cpu", "gpu_name": "NVIDIA L4 | null", "version": "0.1.0", "queue_length": 0}
```

## Client rules

- Poll every 1 second for the first 10 seconds, then every 3 seconds.
- Stop polling after 15 minutes and show a timeout message.
- Show `warnings` in the UI. A CPU warning is required.
- Never assume `obj` exists. Read the download links from the job response, once the server adds them. Until then use the fixed paths above.

## Stub for client work

`GenerationClient` in `src/sketch2shape/app/client.py` has two implementations behind one interface, `HttpClient` (this API) and `StubClient` (returns a bundled sample `.glb` after a fake delay). `S2S_API_URL` unset means stub.
