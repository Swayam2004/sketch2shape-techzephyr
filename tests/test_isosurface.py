"""Orientation checks for the skimage marching cubes swap in the vendored TripoSR."""

import numpy as np
import torch
import trimesh

from sketch2shape.vendor.tsr.models.isosurface import MarchingCubeHelper

RES = 48


def _sphere_level(centre: tuple[float, float, float], radius: float) -> torch.Tensor:
    """Negative inside a sphere, positive outside, on the helper's (x, y, z) ij grid."""
    helper = MarchingCubeHelper(RES)
    pts = helper.grid_vertices.numpy()
    dist = np.linalg.norm(pts - np.asarray(centre, dtype=np.float32), axis=1)
    return torch.from_numpy((dist - radius).astype(np.float32))


def test_axes_are_not_swapped() -> None:
    # An off-centre sphere with three different coordinates. Any axis flip or swap moves the
    # mesh centre away from (0.30, 0.50, 0.70).
    centre = (0.30, 0.50, 0.70)
    verts, _ = MarchingCubeHelper(RES)(_sphere_level(centre, 0.2))
    np.testing.assert_allclose(verts.numpy().mean(axis=0), centre, atol=0.01)


def test_marked_corner_stays_in_its_corner() -> None:
    # A cube whose +x +y +z corner is cut away. The missing corner must show up in the
    # output as a vertex-free region at the same place.
    helper = MarchingCubeHelper(RES)
    pts = helper.grid_vertices.numpy()
    inside = np.all((pts > 0.2) & (pts < 0.8), axis=1)
    notch = np.all(pts > 0.6, axis=1)
    level = torch.from_numpy(np.where(inside & ~notch, -1.0, 1.0).astype(np.float32))
    verts, _ = helper(level)
    v = verts.numpy()
    assert not np.any(np.all(v > 0.7, axis=1))
    assert np.any(np.all(v < 0.3, axis=1))


def test_faces_point_outward_and_mesh_is_closed() -> None:
    verts, faces = MarchingCubeHelper(RES)(_sphere_level((0.5, 0.5, 0.5), 0.3))
    mesh = trimesh.Trimesh(vertices=verts.numpy(), faces=faces.numpy())
    assert mesh.is_watertight
    # trimesh gives a negative volume for inward-facing triangles.
    assert mesh.volume > 0
    expected = 4 / 3 * np.pi * 0.3**3
    assert abs(mesh.volume - expected) / expected < 0.05
