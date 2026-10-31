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
from sketch2shape.export import finalize_mesh, save_mesh, validate_mesh
from sketch2shape.reconstruct import image_to_mesh
from sketch2shape.types import (
    IMAGE_SIZE,
    Device,
    GenerationRequest,
    GenerationResult,
    PreparedSketch,
    StageTiming,
)

logger = logging.getLogger(__name__)

BACKEND_ENV = "S2S_BACKEND"
CPU_WARNING = (
    "Running on CPU. Expect about 20 to 40 seconds for the 3D step and longer for image generation."
)


@dataclass(frozen=True)
class Stages:
    """The stages owned by other people, injectable so tests and the stub can replace them."""

    prepare: Callable[[Image.Image], PreparedSketch]
    generate: Callable[[PreparedSketch, str | None, int, Device], Image.Image]
    iou: Callable[[trimesh.Trimesh, np.ndarray], float] | None = None


def _stub_prepare(image: Image.Image) -> PreparedSketch:
    rgb = image.convert("RGB").resize((IMAGE_SIZE, IMAGE_SIZE))
    mask = np.asarray(rgb.convert("L")) < 128
    scribble = Image.fromarray((mask * 255).astype(np.uint8), mode="L")
    return PreparedSketch(rgb=rgb, mask=mask, scribble=scribble)


def _stub_generate(
    sketch: PreparedSketch, prompt: str | None, seed: int, device: Device
) -> Image.Image:
    return sketch.rgb


def default_stages() -> tuple[Stages, list[str]]:
    """Use Udit's real stages when they are importable, else a pass-through stub.

    The stub treats the input as an already finished object photo, which lets the rest of the
    pipeline run end to end before the preprocess and generate stages land.
    """
    try:
        from sketch2shape.eval import silhouette_iou
        from sketch2shape.generate import sketch_to_image
        from sketch2shape.preprocess import prepare_sketch
    except ImportError:
        warning = "Preprocess and generate stages are missing, using the pass-through stub."
        logger.warning(warning)
        return Stages(_stub_prepare, _stub_generate), [warning]
    return Stages(prepare_sketch, sketch_to_image, silhouette_iou), []


def select_device(requested: str | None = None) -> Device:
    """`S2S_BACKEND=auto|cuda|cpu`, default auto (CUDA when torch can see it)."""
    choice = (requested or os.environ.get(BACKEND_ENV, "auto")).lower()
    if choice not in ("auto", "cuda", "cpu"):
        raise ValueError(f"{BACKEND_ENV} must be auto, cuda or cpu, got {choice!r}.")
    if choice == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return choice  # type: ignore[return-value]


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
) -> GenerationResult:
    """Sketch (and optional prompt) in, validated `.glb` and `.obj` out."""
    device = device or select_device()
    warnings: list[str] = []
    if stages is None:
        stages, stage_warnings = default_stages()
        warnings += stage_warnings
    if device == "cpu":
        warnings.append(CPU_WARNING)
    stem = stem or f"mesh_seed{request.seed}"
    timings: list[StageTiming] = []
    logger.info("pipeline start seed=%d device=%s prompt=%r", request.seed, device, request.prompt)

    with _timed(timings, "preprocess", device, on_stage):
        prepared = stages.prepare(request.sketch)
    with _timed(timings, "generate", device, on_stage):
        image = stages.generate(prepared, request.prompt, request.seed, device)
    out_dir.mkdir(parents=True, exist_ok=True)
    generated_path = out_dir / f"{stem}_generated.png"
    image.save(generated_path)
    with _timed(timings, "cutout", device, on_stage):
        rgba = remove_background(image)
    with _timed(timings, "reconstruct", device, on_stage):
        raw = image_to_mesh(rgba, request.seed, device)
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
        seed=request.seed,
        device=device,
        timings=timings,
        validation=report,
        silhouette_iou=iou,
        warnings=warnings,
    )
