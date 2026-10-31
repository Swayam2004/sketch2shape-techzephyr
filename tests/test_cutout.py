import numpy as np
import pytest
from PIL import Image

from sketch2shape.cutout import center_object, remove_background
from sketch2shape.types import IMAGE_SIZE
from sketch2shape.weights import rembg_home


def _blob(x0: int, y0: int, x1: int, y1: int, size: int = 512) -> Image.Image:
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[y0:y1, x0:x1] = [200, 30, 30, 255]
    return Image.fromarray(arr)


def test_center_object_scales_to_85_percent_and_centres() -> None:
    out = center_object(_blob(10, 10, 110, 60))
    ys, xs = np.nonzero(np.asarray(out)[..., 3] > 10)
    assert out.size == (IMAGE_SIZE, IMAGE_SIZE)
    assert abs((xs.max() - xs.min() + 1) - round(IMAGE_SIZE * 0.85)) <= 1
    assert abs((xs.min() + xs.max()) / 2 - IMAGE_SIZE / 2) <= 1
    assert abs((ys.min() + ys.max()) / 2 - IMAGE_SIZE / 2) <= 1


def test_center_object_rejects_empty_image() -> None:
    with pytest.raises(ValueError, match="No foreground"):
        center_object(Image.new("RGBA", (64, 64), (0, 0, 0, 0)))


@pytest.mark.skipif(
    not (rembg_home() / "isnet-general-use.onnx").is_file(), reason="rembg weights not downloaded"
)
def test_remove_background_on_a_disc() -> None:
    arr = np.full((512, 512, 3), 255, dtype=np.uint8)
    yy, xx = np.mgrid[:512, :512]
    arr[(yy - 200) ** 2 + (xx - 150) ** 2 < 90**2] = [220, 40, 40]
    out = remove_background(Image.fromarray(arr))
    assert out.mode == "RGBA" and out.size == (IMAGE_SIZE, IMAGE_SIZE)
    assert np.asarray(out)[..., 3].max() > 200
