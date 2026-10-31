import cv2
import numpy as np
import pytest
import trimesh

from sketch2shape.eval import mask_iou, render_silhouette, silhouette_iou


def _disk(size: int = 128) -> np.ndarray:
    m = np.zeros((size, size), dtype=np.uint8)
    cv2.circle(m, (size // 2, size // 2), size // 2 - 13, 255, thickness=-1)
    return m > 0


def test_mask_iou_bounds() -> None:
    a = np.zeros((10, 10), bool)
    a[:5] = True
    assert mask_iou(a, a) == 1.0
    assert mask_iou(a, ~a) == 0.0


def test_mask_iou_shape_mismatch_raises() -> None:
    with pytest.raises(ValueError, match="shape"):
        mask_iou(np.zeros((4, 4), bool), np.zeros((5, 5), bool))


def test_render_silhouette_of_sphere_is_round() -> None:
    sil = render_silhouette(trimesh.creation.icosphere(subdivisions=3), size=128)
    assert sil.shape == (128, 128)
    assert mask_iou(sil, _disk(128)) > 0.9


def test_sphere_matches_disk_better_than_box() -> None:
    disk = _disk()
    sphere = silhouette_iou(trimesh.creation.icosphere(subdivisions=3), disk)
    box = silhouette_iou(trimesh.creation.box(), disk)
    assert sphere > 0.9
    assert box < sphere


def test_unit_cube_matches_square_mask() -> None:
    square = np.zeros((128, 128), bool)
    square[20:108, 20:108] = True
    assert silhouette_iou(trimesh.creation.box(extents=[1, 1, 1]), square) > 0.97


def test_shifted_or_scaled_mask_scores_lower() -> None:
    cube = trimesh.creation.box(extents=[1, 1, 1])
    square = np.zeros((128, 128), bool)
    square[20:108, 20:108] = True
    wide = np.zeros((128, 128), bool)
    wide[20:108, 20:60] = True
    assert silhouette_iou(cube, wide) < silhouette_iou(cube, square) - 0.3


def test_silhouette_iou_ignores_scale_and_offset() -> None:
    mesh = trimesh.creation.icosphere(subdivisions=3)
    mesh.apply_scale(7.0)
    mesh.apply_translation([3.0, -2.0, 5.0])
    assert silhouette_iou(mesh, _disk()) > 0.9


def test_view_axis_changes_projection() -> None:
    # A box long in x: seen down z it's a wide rectangle, seen down x it's a square.
    box = trimesh.creation.box(extents=[4.0, 1.0, 1.0])
    square = np.zeros((64, 64), bool)
    square[8:56, 8:56] = True
    assert silhouette_iou(box, square, view="+x") > 0.9


def test_empty_mesh_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        render_silhouette(trimesh.Trimesh(), size=32)
