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


def test_missing_weights_give_a_clear_error(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("S2S_WEIGHTS_DIR", str(tmp_path))
    blank = Image.new("RGB", (IMAGE_SIZE, IMAGE_SIZE), "white")
    sketch = PreparedSketch(
        rgb=blank, mask=np.zeros((IMAGE_SIZE, IMAGE_SIZE), bool), scribble=blank.convert("L")
    )
    with pytest.raises(ModelFilesMissing, match="download_weights"):
        sketch_to_image(sketch, None, 0, "cpu")
