import importlib

import numpy as np
import pytest
from PIL import Image

from sketch2shape.generate import ModelFilesMissing, build_prompt, is_degenerate, sketch_to_image
from sketch2shape.types import IMAGE_SIZE, PreparedSketch


def test_prompt_template_with_and_without_user_text() -> None:
    assert build_prompt("a red kettle").startswith("a red kettle, product design render")
    for empty in (None, "", "   "):
        assert build_prompt(empty).startswith("a single object, product design render")


def test_black_and_flat_images_are_degenerate() -> None:
    assert is_degenerate(Image.new("RGB", (64, 64), "black"))
    assert is_degenerate(Image.new("RGB", (64, 64), (200, 200, 200)))


def test_textured_image_is_not_degenerate() -> None:
    noise = np.random.default_rng(0).integers(0, 255, (64, 64, 3), dtype=np.uint8)
    assert not is_degenerate(Image.fromarray(noise))


def _blank_sketch() -> PreparedSketch:
    blank = Image.new("RGB", (IMAGE_SIZE, IMAGE_SIZE), "white")
    return PreparedSketch(
        rgb=blank, mask=np.zeros((IMAGE_SIZE, IMAGE_SIZE), bool), scribble=blank.convert("L")
    )


def test_fp32_retry_frees_the_fp16_pipeline_first(monkeypatch, caplog) -> None:
    """Swayam's 4 GB card ran out of memory because both pipelines sat in the lru_cache."""
    # The package re-exports the function under the module's name, so import the module by path.
    stage = importlib.import_module("sketch2shape.generate.sketch_to_image")

    events: list[str] = []

    class FakeLoader:
        def __call__(self, device: str, fp16: bool) -> object:
            events.append(f"load fp16={fp16}")
            return object()

        def cache_clear(self) -> None:
            events.append("cache_clear")

    noise = np.random.default_rng(0).integers(0, 255, (64, 64, 3), dtype=np.uint8)
    outputs = iter([Image.new("RGB", (64, 64), "black"), Image.fromarray(noise)])

    monkeypatch.setattr(stage, "_model_paths", lambda root: (root, root))
    monkeypatch.setattr(stage, "_load_pipeline", FakeLoader())
    monkeypatch.setattr(stage, "_run", lambda *args, **kwargs: next(outputs))

    with caplog.at_level("WARNING", logger=stage.log.name):
        image = stage.sketch_to_image(_blank_sketch(), "a chair", 1, "cuda")

    assert not is_degenerate(image)
    assert events == ["load fp16=True", "cache_clear", "load fp16=False"]
    assert any("retrying in fp32" in record.getMessage() for record in caplog.records)


def test_missing_weights_give_a_clear_error(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("S2S_WEIGHTS_DIR", str(tmp_path))
    blank = Image.new("RGB", (IMAGE_SIZE, IMAGE_SIZE), "white")
    sketch = PreparedSketch(
        rgb=blank, mask=np.zeros((IMAGE_SIZE, IMAGE_SIZE), bool), scribble=blank.convert("L")
    )
    with pytest.raises(ModelFilesMissing, match="download_weights"):
        sketch_to_image(sketch, None, 0, "cpu")
