"""Run the full sketch to mesh pipeline and time each stage."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import trimesh
from PIL import Image

from sketch2shape.cutout import remove_background
from sketch2shape.eval import select_best_candidate
from sketch2shape.export import finalize_mesh, save_mesh, validate_mesh
from sketch2shape.reconstruct import image_to_mesh
from sketch2shape.types import (
    Device,
    GenerationRequest,
    GenerationResult,
    PreparedSketch,
    StageTiming,
)

logger = logging.getLogger(__name__)

BACKEND_ENV = "S2S_BACKEND"
CANDIDATES_ENV = "S2S_CANDIDATES"
# The same on every device so a CPU run and a GPU run pick from the same seeds. CPU generation
# takes about 270 s a candidate, so 4 would pass the 15 minute client poll limit.
DEFAULT_CANDIDATES = 3
CPU_WARNING = (
    "Running on CPU. Expect about 15 minutes per sketch, because the image step runs "
    f"{DEFAULT_CANDIDATES} times and picks the best outline."
)


@dataclass(frozen=True)
class Stages:
    """The stages owned by other people, injectable so tests can replace them."""

    prepare: Callable[[Image.Image], PreparedSketch]
    generate: Callable[[PreparedSketch, str | None, int, Device], Image.Image]
    iou: Callable[[trimesh.Trimesh, np.ndarray], float] | None = None


def default_stages() -> Stages:
    """Udit's real preprocess, generate and IoU stages. Imported late so tests skip diffusers."""
    from sketch2shape.eval import silhouette_iou
    from sketch2shape.generate import sketch_to_image
    from sketch2shape.preprocess import prepare_sketch

    return Stages(prepare_sketch, sketch_to_image, silhouette_iou)


def select_device(requested: str | None = None) -> Device:
    """`S2S_BACKEND=auto|cuda|cpu`, default auto (CUDA when torch can see it)."""
    choice = (requested or os.environ.get(BACKEND_ENV, "auto")).lower()
    if choice not in ("auto", "cuda", "cpu"):
        raise ValueError(f"{BACKEND_ENV} must be auto, cuda or cpu, got {choice!r}.")
    if choice == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return choice  # type: ignore[return-value]


def candidate_count(requested: int | None = None) -> int:
    """How many seeds to try per request. `S2S_CANDIDATES` overrides the default of 3."""
    if requested is None:
        raw = os.environ.get(CANDIDATES_ENV, str(DEFAULT_CANDIDATES))
        try:
            requested = int(raw)
        except ValueError:
            raise ValueError(f"{CANDIDATES_ENV} must be a whole number, got {raw!r}.") from None
    if requested < 1:
        raise ValueError(f"{CANDIDATES_ENV} must be at least 1, got {requested}.")
    return requested


@contextmanager
def _timed(
    timings: list[StageTiming],
    stage: str,
    device: Device,
    on_stage: Callable[[str], None] | None = None,
) -> Iterator[None]:
    if on_stage:
        on_stage(stage)
    cuda = device == "cuda"
    if cuda:
        torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    try:
        yield
    finally:
        if cuda:
            torch.cuda.synchronize()
        peak = torch.cuda.max_memory_allocated() / 2**20 if cuda else None
        timing = StageTiming(stage, time.perf_counter() - started, peak)
        timings.append(timing)
        logger.info("stage=%s %.1fs peak_vram_mb=%s", stage, timing.seconds, peak)


def run(
    request: GenerationRequest,
    device: Device | None = None,
    out_dir: Path = Path("outputs"),
    stem: str | None = None,
    stages: Stages | None = None,
    on_stage: Callable[[str], None] | None = None,
    candidates: int | None = None,
) -> GenerationResult:
    """Sketch (and optional prompt) in, validated `.glb` and `.obj` out.

    Generates `candidates` images from seeds `request.seed + 0..N-1`, keeps the cut-out whose
    outline best matches the sketch, and reconstructs only that one. The result reports the
    winning seed, so running it alone reproduces the mesh.
    """
    device = device or select_device()
    count = candidate_count(candidates)
    warnings: list[str] = []
    if stages is None:
        stages = default_stages()
    if device == "cpu":
        warnings.append(CPU_WARNING)
    stem = stem or f"mesh_seed{request.seed}"
    timings: list[StageTiming] = []
    logger.info(
        "pipeline start seed=%d candidates=%d device=%s prompt=%r",
        request.seed,
        count,
        device,
        request.prompt,
    )

    with _timed(timings, "preprocess", device, on_stage):
        prepared = stages.prepare(request.sketch)
    seeds = [request.seed + i for i in range(count)]
    with _timed(timings, "generate", device, on_stage):
        images = [stages.generate(prepared, request.prompt, seed, device) for seed in seeds]
    with _timed(timings, "cutout", device, on_stage):
        kept: list[tuple[int, Image.Image, Image.Image]] = []
        for seed, image in zip(seeds, images, strict=True):
            try:
                kept.append((seed, image, remove_background(image)))
            except ValueError as exc:
                # An empty cut-out is one bad seed, not a bad request.
                logger.warning("seed %d dropped: %s", seed, exc)
                warnings.append(f"Candidate seed {seed} was dropped: {exc}")
        if not kept:
            raise ValueError("Every candidate came back empty after background removal.")
        pick = None
        if len(kept) > 1:
            pick = select_best_candidate(prepared.mask, [rgba for _, _, rgba in kept])
    won = kept[pick.index if pick else 0]
    seed, image, rgba = won
    if pick:
        scores = {k[0]: round(sc, 3) for k, sc in zip(kept, pick.scores, strict=True)}
        logger.info("chose seed %d, 2D IoU by seed %s", seed, scores)
    out_dir.mkdir(parents=True, exist_ok=True)
    generated_path = out_dir / f"{stem}_generated.png"
    image.save(generated_path)
    with _timed(timings, "reconstruct", device, on_stage):
        raw = image_to_mesh(rgba, seed, device)
    with _timed(timings, "export", device, on_stage):
        mesh = finalize_mesh(raw)
        paths = save_mesh(mesh, out_dir, stem)
        report = validate_mesh(paths.glb)

    iou = stages.iou(mesh, prepared.mask) if stages.iou else None
    if not report.ok:
        warnings.append("Mesh validation failed: " + "; ".join(report.errors))
    return GenerationResult(
        paths=paths,
        generated_image=generated_path,
        seed=seed,
        device=device,
        timings=timings,
        validation=report,
        silhouette_iou=iou,
        warnings=warnings,
    )
