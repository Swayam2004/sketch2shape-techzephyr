"""Image to 3D with TripoSR (vendored under `sketch2shape.vendor.tsr`)."""

from __future__ import annotations

import logging
import time
from functools import lru_cache
from pathlib import Path

import numpy as np
import torch
import trimesh
from PIL import Image

from sketch2shape.types import Device
from sketch2shape.vendor.tsr.system import TSR
from sketch2shape.weights import triposr_dir

logger = logging.getLogger(__name__)

# Same code path on both devices. Only the grid size differs, to keep CPU time usable (task
# S2). Revisit with the team if the CPU number in EXPERIMENTS.md says otherwise. Override with
# the `resolution` argument.
MC_RESOLUTION: dict[str, int] = {"cuda": 256, "cpu": 192}
# Density level of the surface. 25 is the upstream default.
MC_THRESHOLD = 25.0
# TripoSR was trained on objects composited over mid grey.
BACKGROUND_GREY = 0.5
# Grid points per MLP call. Upstream defaults to 8192 in its CLI, the library default of 0 sends
# all resolution^3 points at once. Chunking is exact, it only bounds peak memory.
CHUNK_SIZE = 8192


class WeightsMissingError(FileNotFoundError):
    """Raised when the TripoSR files are not on disk yet."""


@lru_cache(maxsize=2)
def _load_model(device: str, weights: Path) -> TSR:
    config, ckpt = weights / "config.yaml", weights / "model.ckpt"
    missing = [p.name for p in (config, ckpt) if not p.is_file()]
    if missing:
        raise WeightsMissingError(
            f"TripoSR files {missing} not found in {weights}. "
            "Run `uv run python scripts/download_weights.py` first. The download is about 7 GB in total."
        )
    started = time.perf_counter()
    model = TSR.from_pretrained(str(weights), config_name="config.yaml", weight_name="model.ckpt")
    model.to(device).eval()
    logger.info("Loaded TripoSR on %s in %.1fs", device, time.perf_counter() - started)
    return model


def _composite_on_grey(rgba: Image.Image) -> Image.Image:
    arr = np.asarray(rgba, dtype=np.float32) / 255.0
    alpha = arr[..., 3:4]
    rgb = arr[..., :3] * alpha + BACKGROUND_GREY * (1.0 - alpha)
    return Image.fromarray((rgb * 255.0).round().astype(np.uint8))


def image_to_mesh(
    rgba: Image.Image,
    seed: int,
    device: Device,
    resolution: int | None = None,
    chunk_size: int = CHUNK_SIZE,
) -> trimesh.Trimesh:
    """Reconstruct a vertex-coloured mesh from one cut-out object image.

    `rgba` is the output of `cutout.remove_background`. The mesh is returned in TripoSR's own
    frame. `export.finalize_mesh` moves it to the glTF convention in `types.py`.
    TripoSR has no sampling step, so `seed` does not change the result. It is set and logged
    anyway so every output records one.
    """
    if rgba.mode != "RGBA":
        raise ValueError(f"image_to_mesh needs an RGBA image, got mode {rgba.mode}.")
    if np.asarray(rgba)[..., 3].max() == 0:
        raise ValueError("The image is fully transparent, so there is no object to reconstruct.")
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("device='cuda' was requested but torch cannot see a CUDA device.")

    resolution = resolution or MC_RESOLUTION[device]
    torch.manual_seed(seed)
    model = _load_model(device, triposr_dir())
    model.renderer.set_chunk_size(chunk_size)
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()

    started = time.perf_counter()
    image = _composite_on_grey(rgba)
    with torch.no_grad():
        scene_codes = model([image], device=device)
        meshes = model.extract_mesh(
            scene_codes, has_vertex_color=True, resolution=resolution, threshold=MC_THRESHOLD
        )
    mesh = meshes[0]
    if len(mesh.faces) == 0:
        raise RuntimeError(
            "TripoSR produced an empty mesh. The input is probably too small or too faint."
        )
    peak_mb = torch.cuda.max_memory_allocated() / 2**20 if device == "cuda" else 0.0
    logger.info(
        "image_to_mesh seed=%d device=%s resolution=%d chunk=%d: %d vertices, %d faces in %.1fs, "
        "peak VRAM %.0f MB",
        seed,
        device,
        resolution,
        chunk_size,
        len(mesh.vertices),
        len(mesh.faces),
        time.perf_counter() - started,
        peak_mb,
    )
    return mesh
