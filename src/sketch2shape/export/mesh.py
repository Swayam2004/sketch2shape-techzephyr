"""Clean up a reconstructed mesh, write it as GLB and OBJ, and check the files load."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import numpy as np
import trimesh

from sketch2shape.types import ExportPaths, ValidationReport

logger = logging.getLogger(__name__)

_SMOOTH_ITERS = int(os.environ.get("S2S_SMOOTH_ITERS", "10"))

# TripoSR has Z up and the object front on +X. glTF has Y up and the front on +Z.
# (x, y, z) -> (y, z, x) is a proper rotation (determinant +1), so faces keep their winding.
_TRIPOSR_TO_GLTF = np.array(
    [
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
)


class InvalidMeshError(ValueError):
    """Raised when a mesh is empty or a written file does not load back."""


def finalize_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Return a cleaned copy in the pipeline convention from `types.py`.

    Keeps the largest connected component, because marching cubes leaves small floating blobs
    from background noise. Merges duplicate vertices, fixes normals, rotates from TripoSR's
    frame to glTF axes, centres at the origin and scales to fit a unit cube.
    """
    if len(mesh.faces) == 0:
        raise InvalidMeshError("Cannot finalize a mesh with no faces.")

    out = mesh.copy()
    out.merge_vertices()
    out.update_faces(out.nondegenerate_faces())
    out.remove_unreferenced_vertices()

    parts = out.split(only_watertight=False)
    if len(parts) > 1:
        out = max(parts, key=lambda p: len(p.faces))
        logger.info("Kept the largest of %d components (%d faces)", len(parts), len(out.faces))
    if len(out.faces) == 0:
        raise InvalidMeshError("The mesh has no faces left after cleanup.")

    # The hidden side comes from a guessed density field, so marching cubes turns noise into
    # bumps there. Taubin smoothing evens them out without shrinking the whole mesh. Set
    # S2S_SMOOTH_ITERS=0 to turn it off and compare.
    if _SMOOTH_ITERS > 0:
        trimesh.smoothing.filter_taubin(out, iterations=_SMOOTH_ITERS)

    out.apply_transform(_TRIPOSR_TO_GLTF)
    lo, hi = out.bounds
    out.apply_translation(-(lo + hi) / 2.0)
    out.apply_scale(1.0 / float(np.max(hi - lo)))
    out.fix_normals()
    return out


def save_mesh(mesh: trimesh.Trimesh, out_dir: Path, stem: str) -> ExportPaths:
    """Write `<stem>.glb` and `<stem>.obj` into `out_dir`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    glb, obj = out_dir / f"{stem}.glb", out_dir / f"{stem}.obj"
    mesh.export(glb)
    mesh.export(obj)
    return ExportPaths(glb=glb, obj=obj)


def validate_mesh(path: Path) -> ValidationReport:
    """Reload a written file and report what is in it. Never raises on a bad mesh, it reports."""
    errors: list[str] = []
    if not path.is_file():
        return ValidationReport(False, 0, 0, False, False, [f"{path} does not exist."])
    try:
        loaded = trimesh.load(path, force="mesh", process=False)
    except Exception as exc:  # noqa: BLE001 - trimesh raises many types for bad files
        return ValidationReport(False, 0, 0, False, False, [f"{path.name} did not load: {exc}"])

    vertices, faces = len(loaded.vertices), len(loaded.faces)
    if vertices == 0 or faces == 0:
        errors.append("The mesh is empty.")
    has_colors = loaded.visual.kind == "vertex" and len(loaded.visual.vertex_colors) == vertices
    if path.suffix.lower() == ".glb" and not has_colors:
        errors.append("The GLB has no vertex colours.")
    if not np.isfinite(loaded.vertices).all():
        errors.append("The mesh has NaN or infinite vertices.")
    return ValidationReport(not errors, vertices, faces, has_colors, loaded.is_watertight, errors)
