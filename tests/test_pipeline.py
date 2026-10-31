import numpy as np
import pytest
import trimesh
from PIL import Image

from sketch2shape import pipeline
from sketch2shape.pipeline import Stages, run, select_device
from sketch2shape.types import IMAGE_SIZE, GenerationRequest, PreparedSketch


def _prepare(image: Image.Image) -> PreparedSketch:
    rgb = Image.new("RGB", (IMAGE_SIZE, IMAGE_SIZE), "white")
    mask = np.zeros((IMAGE_SIZE, IMAGE_SIZE), dtype=bool)
    return PreparedSketch(rgb, mask, Image.new("L", (IMAGE_SIZE, IMAGE_SIZE)))


def _generate(sketch, prompt, seed, device) -> Image.Image:
    return sketch.rgb


def _fake_mesh(rgba, seed, device) -> trimesh.Trimesh:
    box = trimesh.creation.box()
    box.visual.vertex_colors = np.tile([10, 120, 200, 255], (len(box.vertices), 1))
    return box


def test_run_end_to_end_with_fakes(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pipeline, "remove_background", lambda image: image.convert("RGBA"))
    monkeypatch.setattr(pipeline, "image_to_mesh", _fake_mesh)
    stages = Stages(_prepare, _generate, iou=lambda mesh, mask: 0.5)
    result = run(
        GenerationRequest(Image.new("RGB", (64, 64)), "a box", 3), "cpu", tmp_path, "t", stages
    )
    assert result.validation.ok
    assert result.paths.glb.is_file() and result.generated_image.is_file()
    assert [t.stage for t in result.timings] == [
        "preprocess",
        "generate",
        "cutout",
        "reconstruct",
        "export",
    ]
    assert result.seed == 3 and result.silhouette_iou == 0.5
    assert any("CPU" in w for w in result.warnings)


def test_select_device_reads_env(monkeypatch) -> None:
    monkeypatch.setenv("S2S_BACKEND", "cpu")
    assert select_device() == "cpu"
    monkeypatch.setenv("S2S_BACKEND", "tpu")
    with pytest.raises(ValueError, match="S2S_BACKEND"):
        select_device()
