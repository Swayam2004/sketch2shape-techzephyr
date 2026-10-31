"""Shared data types and stage contracts.

Every owner codes against these. Change a type only through a PR that all three owners have seen,
and say so in STATUS.md first.

Stage functions and their owners

    preprocess.prepare_sketch(image)                        -> PreparedSketch   (Udit)
    generate.sketch_to_image(sketch, prompt, seed, device)  -> PIL RGB 512x512  (Udit)
    cutout.remove_background(image)                         -> PIL RGBA 512x512 (Swayam)
    reconstruct.image_to_mesh(rgba, seed, device)           -> trimesh.Trimesh  (Swayam)
    export.finalize_mesh(mesh)                              -> trimesh.Trimesh  (Swayam)
    export.save_mesh(mesh, out_dir, stem)                   -> ExportPaths      (Swayam)
    export.validate_mesh(path)                              -> ValidationReport (Swayam)
    eval.silhouette_iou(mesh, mask)                         -> float            (Udit)
    pipeline.run(request, device)                           -> GenerationResult (Swayam)

Mesh convention for everything after reconstruct. glTF axes, Y up, the front of the object faces
+Z (towards the camera), centred at the origin and scaled to fit a unit cube. Vertex colours are
RGBA uint8 in `mesh.visual.vertex_colors`. `eval.silhouette_iou` projects orthographically along -Z
onto the XY plane, so the same convention gives the "front view".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image

Device = Literal["cuda", "cpu"]

IMAGE_SIZE = 512


@dataclass(frozen=True)
class PreparedSketch:
    """A sketch cleaned for the rest of the pipeline. All images are IMAGE_SIZE square."""

    rgb: Image.Image
    """Black strokes on white, object centred with padding. Mode RGB."""
    mask: np.ndarray
    """Filled silhouette of the drawn object. bool array, shape (IMAGE_SIZE, IMAGE_SIZE)."""
    scribble: Image.Image
    """White lines on black, about 2 to 4 px wide. Mode L. ControlNet scribble input."""


@dataclass(frozen=True)
class GenerationRequest:
    sketch: Image.Image
    prompt: str | None = None
    seed: int = 0


@dataclass
class StageTiming:
    stage: str
    seconds: float
    peak_vram_mb: float | None = None


@dataclass(frozen=True)
class ExportPaths:
    glb: Path
    obj: Path | None = None


@dataclass(frozen=True)
class ValidationReport:
    ok: bool
    vertex_count: int
    face_count: int
    has_vertex_colors: bool
    is_watertight: bool
    errors: list[str] = field(default_factory=list)


@dataclass
class GenerationResult:
    paths: ExportPaths
    generated_image: Path | None
    seed: int
    device: Device
    timings: list[StageTiming]
    validation: ValidationReport
    silhouette_iou: float | None = None
    warnings: list[str] = field(default_factory=list)
