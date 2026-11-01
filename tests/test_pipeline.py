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
        GenerationRequest(Image.new("RGB", (64, 64)), "a box", 3),
        "cpu",
        tmp_path,
        "t",
        stages,
        candidates=1,
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


def _rect_mask() -> np.ndarray:
    mask = np.zeros((IMAGE_SIZE, IMAGE_SIZE), dtype=bool)
    mask[100:400, 200:300] = True  # tall bar
    return mask


def _prepare_bar(image: Image.Image) -> PreparedSketch:
    rgb = Image.new("RGB", (IMAGE_SIZE, IMAGE_SIZE), "white")
    return PreparedSketch(rgb, _rect_mask(), Image.new("L", (IMAGE_SIZE, IMAGE_SIZE)))


def _tag_generate(sketch, prompt, seed, device) -> Image.Image:
    # The red channel carries the seed so the fake cut-out knows which candidate it got.
    return Image.new("RGB", (IMAGE_SIZE, IMAGE_SIZE), (seed, 0, 0))


def _shaped_cutout(image: Image.Image) -> Image.Image:
    """Seed 11 is the tall bar the sketch asked for, every other seed is a wide slab."""
    seed = image.getpixel((0, 0))[0]
    alpha = np.zeros((IMAGE_SIZE, IMAGE_SIZE), dtype=np.uint8)
    if seed == 11:
        alpha[100:400, 200:300] = 255
    else:
        alpha[200:300, 50:450] = 255
    rgba = image.convert("RGBA")
    rgba.putalpha(Image.fromarray(alpha))
    return rgba


def test_best_of_n_keeps_the_candidate_that_matches_the_sketch(
    tmp_path, monkeypatch, caplog
) -> None:
    seen: list[int] = []

    def reconstruct(rgba, seed, device):
        seen.append(seed)
        return _fake_mesh(rgba, seed, device)

    monkeypatch.setattr(pipeline, "remove_background", _shaped_cutout)
    monkeypatch.setattr(pipeline, "image_to_mesh", reconstruct)
    stages = Stages(_prepare_bar, _tag_generate)
    with caplog.at_level("INFO", logger="sketch2shape.eval.select"):
        result = run(
            GenerationRequest(Image.new("RGB", (64, 64)), None, 10),
            "cpu",
            tmp_path,
            "t",
            stages,
            candidates=3,
        )
    # Seeds 10, 11, 12. Only 11 is the bar.
    assert result.seed == 11
    assert seen == [11], "reconstruction must run once, on the winner"
    assert Image.open(result.generated_image).getpixel((0, 0))[0] == 11
    assert "best candidate 1 of 3" in caplog.text
    assert [t.stage for t in result.timings].count("generate") == 1


def test_one_candidate_skips_selection(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pipeline, "remove_background", _shaped_cutout)
    monkeypatch.setattr(pipeline, "image_to_mesh", _fake_mesh)
    result = run(
        GenerationRequest(Image.new("RGB", (64, 64)), None, 10),
        "cpu",
        tmp_path,
        "t",
        Stages(_prepare_bar, _tag_generate),
        candidates=1,
    )
    assert result.seed == 10


def test_a_failed_cutout_does_not_sink_the_request(tmp_path, monkeypatch) -> None:
    def flaky(image: Image.Image) -> Image.Image:
        if image.getpixel((0, 0))[0] == 10:
            raise ValueError("No foreground found.")
        return _shaped_cutout(image)

    monkeypatch.setattr(pipeline, "remove_background", flaky)
    monkeypatch.setattr(pipeline, "image_to_mesh", _fake_mesh)
    result = run(
        GenerationRequest(Image.new("RGB", (64, 64)), None, 10),
        "cpu",
        tmp_path,
        "t",
        Stages(_prepare_bar, _tag_generate),
        candidates=3,
    )
    assert result.seed == 11
    assert any("seed 10" in w for w in result.warnings)


def test_candidates_env_and_validation(monkeypatch) -> None:
    monkeypatch.delenv("S2S_CANDIDATES", raising=False)
    assert pipeline.candidate_count() == 3
    monkeypatch.setenv("S2S_CANDIDATES", "2")
    assert pipeline.candidate_count() == 2
    monkeypatch.setenv("S2S_CANDIDATES", "zero")
    with pytest.raises(ValueError, match="S2S_CANDIDATES"):
        pipeline.candidate_count()


def test_fp32_retry_note_reaches_the_result_warnings(tmp_path, monkeypatch) -> None:
    def generate(sketch, prompt, seed, device) -> Image.Image:
        image = _tag_generate(sketch, prompt, seed, device)
        image.info["s2s_warning"] = "reran in fp32"
        return image

    monkeypatch.setattr(pipeline, "remove_background", _shaped_cutout)
    monkeypatch.setattr(pipeline, "image_to_mesh", _fake_mesh)
    result = run(
        GenerationRequest(Image.new("RGB", (64, 64)), None, 10),
        "cpu",
        tmp_path,
        "t",
        Stages(_prepare_bar, generate),
        candidates=2,
    )
    assert result.warnings.count("reran in fp32") == 1


def test_selection_uses_the_3d_score_when_an_iou_stage_exists(tmp_path, monkeypatch) -> None:
    """A cut-out can match the sketch and still reconstruct badly, so the mesh decides."""
    built: list[int] = []

    def reconstruct(rgba, seed, device):
        built.append(seed)
        return _fake_mesh(rgba, seed, device)

    scores = iter([0.20, 0.90, 0.50])  # one call per candidate, in seed order
    monkeypatch.setattr(pipeline, "remove_background", _shaped_cutout)
    monkeypatch.setattr(pipeline, "image_to_mesh", reconstruct)
    result = run(
        GenerationRequest(Image.new("RGB", (64, 64)), None, 20),
        "cpu",
        tmp_path,
        "t",
        Stages(_prepare_bar, _tag_generate, iou=lambda mesh, mask: next(scores)),
        candidates=3,
    )
    assert built == [20, 21, 22]
    assert result.seed == 21 and result.silhouette_iou == 0.90
    assert Image.open(result.generated_image).getpixel((0, 0))[0] == 21
