"""Input checks for `image_to_mesh`. None of these load model weights."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from sketch2shape.reconstruct import WeightsMissingError, image_to_mesh
from sketch2shape.reconstruct.triposr import _composite_on_grey
from sketch2shape.weights import triposr_dir, weights_dir


def _rgba(alpha: int = 255) -> Image.Image:
    arr = np.zeros((32, 32, 4), dtype=np.uint8)
    arr[8:24, 8:24] = (200, 30, 30, alpha)
    return Image.fromarray(arr, "RGBA")


def test_rejects_rgb_input() -> None:
    with pytest.raises(ValueError, match="RGBA"):
        image_to_mesh(Image.new("RGB", (32, 32)), seed=0, device="cpu")


def test_rejects_fully_transparent_input() -> None:
    with pytest.raises(ValueError, match="transparent"):
        image_to_mesh(_rgba(alpha=0), seed=0, device="cpu")


def test_missing_weights_say_how_to_fix_it(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("S2S_WEIGHTS_DIR", str(tmp_path))
    with pytest.raises(WeightsMissingError, match="download_weights"):
        image_to_mesh(_rgba(), seed=0, device="cpu")


def test_composite_puts_transparent_pixels_on_grey() -> None:
    out = np.asarray(_composite_on_grey(_rgba()))
    assert out.shape == (32, 32, 3)
    assert tuple(out[0, 0]) == (128, 128, 128)
    assert tuple(out[16, 16]) == (200, 30, 30)


def test_weights_dir_honours_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("S2S_WEIGHTS_DIR", str(tmp_path))
    assert weights_dir() == tmp_path
    assert triposr_dir() == tmp_path / "triposr"


def test_relative_weights_dir_is_taken_from_repo_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("S2S_WEIGHTS_DIR", raising=False)
    assert weights_dir().is_absolute()
    assert weights_dir().name == "weights"
