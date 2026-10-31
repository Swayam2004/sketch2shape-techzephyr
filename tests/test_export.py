import numpy as np
import pytest
import trimesh

from sketch2shape.export import InvalidMeshError, finalize_mesh, save_mesh, validate_mesh


def _colored_box(extents=(2.0, 1.0, 4.0)) -> trimesh.Trimesh:
    box = trimesh.creation.box(extents=extents)
    box.visual.vertex_colors = np.tile([200, 50, 50, 255], (len(box.vertices), 1))
    return box


def test_finalize_fits_unit_cube_and_centres() -> None:
    out = finalize_mesh(_colored_box())
    lo, hi = out.bounds
    assert np.allclose((lo + hi) / 2, 0, atol=1e-6)
    assert np.isclose((hi - lo).max(), 1.0)


def test_finalize_moves_triposr_up_axis_to_y() -> None:
    # Tall along Z in TripoSR's frame, so it must be tall along Y in glTF.
    out = finalize_mesh(_colored_box(extents=(1.0, 1.0, 4.0)))
    assert np.argmax(out.extents) == 1


def test_finalize_moves_front_from_plus_x_to_plus_z() -> None:
    # A cone with its apex on +X, apex coloured blue. The apex must end up on +Z.
    cone = trimesh.creation.cone(radius=0.5, height=2.0)
    cone.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    colors = np.tile([200, 50, 50, 255], (len(cone.vertices), 1))
    apex = int(np.argmax(cone.vertices[:, 0]))
    colors[apex] = [0, 0, 255, 255]
    cone.visual.vertex_colors = colors
    out = finalize_mesh(cone)
    blue = (out.visual.vertex_colors[:, :3] == [0, 0, 255]).all(axis=1)
    assert blue.sum() == 1
    assert np.argmax(out.vertices[blue][0]) == 2


def test_finalize_drops_floating_blob() -> None:
    blob = trimesh.creation.box(extents=(0.1, 0.1, 0.1))
    blob.apply_translation([10, 10, 10])
    blob.visual.vertex_colors = np.tile([0, 255, 0, 255], (len(blob.vertices), 1))
    out = finalize_mesh(trimesh.util.concatenate([_colored_box(), blob]))
    assert len(out.faces) == 12
    assert out.is_watertight


def test_finalize_rejects_empty_mesh() -> None:
    with pytest.raises(InvalidMeshError):
        finalize_mesh(trimesh.Trimesh())


def test_save_and_validate_roundtrip(tmp_path) -> None:
    paths = save_mesh(finalize_mesh(_colored_box()), tmp_path / "out", "box")
    report = validate_mesh(paths.glb)
    assert report.ok, report.errors
    assert report.has_vertex_colors
    assert report.is_watertight
    assert report.face_count > 0
    assert paths.obj is not None and paths.obj.is_file()


def test_validate_reports_missing_and_corrupt_files(tmp_path) -> None:
    assert not validate_mesh(tmp_path / "nope.glb").ok
    bad = tmp_path / "bad.glb"
    bad.write_bytes(b"not a glb")
    report = validate_mesh(bad)
    assert not report.ok and report.errors


def test_validate_flags_missing_colours(tmp_path) -> None:
    plain = trimesh.creation.box()
    plain.visual = trimesh.visual.ColorVisuals(plain)
    path = tmp_path / "plain.glb"
    plain.export(path)
    report = validate_mesh(path)
    assert not report.has_vertex_colors
    assert not report.ok
