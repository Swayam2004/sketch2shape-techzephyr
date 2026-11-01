from __future__ import annotations

import logging

import cv2
import numpy as np
import trimesh

from sketch2shape.preprocess import fit_to_square

log = logging.getLogger(__name__)

# Orthographic camera placed on the named axis, looking at the origin, +y up (or -z for
# top/bottom). Each entry maps a vertex to image (u right, v up). The input view of the
# image-to-3D model is not settled yet; switch the default once reconstruct fixes it.
VIEWS: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {
    # name: ((axis_u, sign_u), (axis_v, sign_v))
    "+z": ((0, 1), (1, 1)),
    "-z": ((0, -1), (1, 1)),
    "+x": ((2, -1), (1, 1)),
    "-x": ((2, 1), (1, 1)),
    "+y": ((0, 1), (2, -1)),
    "-y": ((0, 1), (2, 1)),
}

_SUBPIXEL_BITS = 4


def mask_iou(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        raise ValueError(f"mask shape mismatch: {a.shape} vs {b.shape}")
    a, b = a.astype(bool), b.astype(bool)
    union = np.logical_or(a, b).sum()
    if union == 0:
        return 1.0
    return float(np.logical_and(a, b).sum() / union)


def render_silhouette(
    mesh: trimesh.Trimesh, size: int = 512, view: str = "+z", margin: float = 0.1
) -> np.ndarray:
    """Orthographic outline of the mesh, cropped to its extent and centred like the sketch mask."""
    if view not in VIEWS:
        raise ValueError(f"unknown view {view!r}, expected one of {sorted(VIEWS)}")
    if len(mesh.faces) == 0:
        raise ValueError("cannot render an empty mesh")

    (au, su), (av, sv) = VIEWS[view]
    v = np.asarray(mesh.vertices, dtype=np.float64)
    uv = np.stack([v[:, au] * su, v[:, av] * sv], axis=1)

    # Rasterise at the output resolution first, then reuse fit_to_square so the render goes
    # through exactly the same crop-and-centre as the sketch mask.
    lo, hi = uv.min(axis=0), uv.max(axis=0)
    extent = float((hi - lo).max()) or 1.0
    px = (uv - lo) / extent * (size - 1)
    px[:, 1] = (size - 1) - px[:, 1]  # image rows grow downward
    pts = np.round(px * (1 << _SUBPIXEL_BITS)).astype(np.int32)

    raster = np.zeros((size, size), dtype=np.uint8)
    # One triangle at a time: cv2.fillPoly on many polygons uses even-odd filling, so
    # overlapping front and back faces would cancel out.
    for tri in pts[mesh.faces]:
        cv2.fillConvexPoly(raster, tri, 255, lineType=cv2.LINE_8, shift=_SUBPIXEL_BITS)

    if not raster.any():
        raise ValueError(f"mesh projects to nothing from view {view!r}")
    x, y, w, h = cv2.boundingRect(raster)
    return fit_to_square(raster[y : y + h, x : x + w], size, margin) > 0


def normalise_mask(
    mask: np.ndarray, size: int | None = None, margin: float = 0.1, name: str = "mask"
) -> np.ndarray:
    """Crop a binary mask to its bounding box and fit it to a size x size canvas.

    The sketch mask, a rendered mesh and a generated image all land in this one frame, so their
    IoU does not depend on where the object sits or how big it is.
    """
    if mask.ndim != 2 or (size is None and mask.shape[0] != mask.shape[1]):
        raise ValueError(f"{name} must be square 2D, got shape {mask.shape}")
    if not mask.any():
        raise ValueError(f"{name} is empty")
    size = size or mask.shape[0]
    m = mask.astype(np.uint8) * 255
    x, y, w, h = cv2.boundingRect(m)
    return fit_to_square(m[y : y + h, x : x + w], size, margin) > 0


def silhouette_iou(
    mesh: trimesh.Trimesh, sketch_mask: np.ndarray, view: str = "+z", margin: float = 0.1
) -> float:
    """IoU of the mesh outline against the sketch mask, invariant to scale and position.

    The sketch mask is re-normalised here so callers can pass any binary mask, not only one
    from preprocess_sketch.
    """
    size = sketch_mask.shape[0]
    target = normalise_mask(sketch_mask, size, margin, name="sketch mask")

    rendered = render_silhouette(mesh, size=size, view=view, margin=margin)
    iou = mask_iou(rendered, target)
    log.info(
        "silhouette_iou: view %s, size %d, faces %d, iou %.4f", view, size, len(mesh.faces), iou
    )
    return iou
