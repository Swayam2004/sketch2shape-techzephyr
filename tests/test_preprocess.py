import cv2
import numpy as np
import pytest
from PIL import Image

from sketch2shape.eval import mask_iou
from sketch2shape.preprocess import PreprocessConfig, SketchError, prepare_sketch, preprocess_sketch
from sketch2shape.types import IMAGE_SIZE


def _circle_sketch(dark_on_light: bool = True, size: int = 400) -> Image.Image:
    bg, ink = (255, 0) if dark_on_light else (0, 255)
    img = np.full((size, size), bg, dtype=np.uint8)
    cv2.circle(img, (size // 2, size // 2), size // 3, ink, thickness=4)
    return Image.fromarray(img)


def _reference_disk(size: int, margin: float) -> np.ndarray:
    ref = np.zeros((size, size), dtype=np.uint8)
    inner = size * (1 - 2 * margin)
    cv2.circle(ref, (size // 2, size // 2), int(inner / 2), 255, thickness=-1)
    return ref > 0


def test_outline_becomes_filled_mask() -> None:
    cfg = PreprocessConfig(size=256)
    out = preprocess_sketch(_circle_sketch(), cfg)
    assert out.mask.shape == (256, 256)
    assert out.scribble.shape == (256, 256)
    assert mask_iou(out.mask, _reference_disk(256, cfg.margin)) > 0.9


def test_scribble_is_white_strokes_on_black() -> None:
    out = preprocess_sketch(_circle_sketch(), PreprocessConfig(size=256))
    assert out.scribble[0, 0] == 0
    assert out.scribble.max() == 255
    # Strokes are thin, so most of the canvas stays black.
    assert (out.scribble > 0).mean() < 0.2


def test_light_on_dark_input_is_inverted() -> None:
    a = preprocess_sketch(_circle_sketch(dark_on_light=True), PreprocessConfig(size=128))
    b = preprocess_sketch(_circle_sketch(dark_on_light=False), PreprocessConfig(size=128))
    assert mask_iou(a.mask, b.mask) > 0.95


def test_transparent_background_is_treated_as_paper() -> None:
    rgba = np.zeros((300, 300, 4), dtype=np.uint8)
    cv2.circle(rgba, (150, 150), 100, (0, 0, 0, 255), thickness=4)
    out = preprocess_sketch(Image.fromarray(rgba, mode="RGBA"), PreprocessConfig(size=128))
    assert out.mask.mean() > 0.3


def test_off_centre_sketch_is_recentred() -> None:
    img = np.full((400, 400), 255, dtype=np.uint8)
    cv2.circle(img, (80, 80), 50, 0, thickness=3)
    out = preprocess_sketch(Image.fromarray(img), PreprocessConfig(size=128))
    ys, xs = np.nonzero(out.mask)
    assert abs(xs.mean() - 64) < 4 and abs(ys.mean() - 64) < 4


def test_prepare_sketch_matches_stage_contract() -> None:
    out = prepare_sketch(_circle_sketch())
    assert out.rgb.mode == "RGB" and out.rgb.size == (IMAGE_SIZE, IMAGE_SIZE)
    assert out.scribble.mode == "L" and out.scribble.size == (IMAGE_SIZE, IMAGE_SIZE)
    assert out.mask.dtype == bool and out.mask.shape == (IMAGE_SIZE, IMAGE_SIZE)
    # rgb is the scribble inverted: black strokes on white paper.
    assert np.asarray(out.rgb)[0, 0, 0] == 255
    assert np.asarray(out.scribble)[0, 0] == 0


def test_circle_mask_area_matches_reference() -> None:
    cfg = PreprocessConfig(size=512)
    out = preprocess_sketch(_circle_sketch(), cfg)
    ref = _reference_disk(512, cfg.margin)
    assert abs(out.mask.sum() / ref.sum() - 1) < 0.05
    assert out.warnings == ()


def test_rectangle_outline_is_filled() -> None:
    img = np.full((300, 400), 255, dtype=np.uint8)
    cv2.rectangle(img, (50, 80), (350, 220), 0, thickness=4)
    out = preprocess_sketch(Image.fromarray(img), PreprocessConfig(size=256))
    assert out.warnings == ()
    ys, xs = np.nonzero(out.mask)
    box = (xs.max() - xs.min() + 1) * (ys.max() - ys.min() + 1)
    assert out.mask.sum() / box > 0.97


def test_open_arc_falls_back_to_convex_hull_with_warning() -> None:
    img = np.full((400, 400), 255, dtype=np.uint8)
    cv2.ellipse(img, (200, 200), (140, 140), 0, 20, 200, 0, thickness=4)
    out = preprocess_sketch(Image.fromarray(img), PreprocessConfig(size=256))
    assert len(out.warnings) == 1 and "convex hull" in out.warnings[0]
    # The hull of a large arc covers far more than the thin stroke itself.
    assert out.mask.sum() > 5 * (out.scribble > 0).sum()


def test_speckle_noise_is_removed() -> None:
    rng = np.random.default_rng(0)
    img = np.full((400, 400), 255, dtype=np.uint8)
    cv2.circle(img, (200, 200), 120, 0, thickness=4)
    for x, y in rng.integers(0, 400, size=(60, 2)):
        img[y, x] = 0
    out = preprocess_sketch(Image.fromarray(img), PreprocessConfig(size=256))
    clean = preprocess_sketch(_circle_sketch(size=400), PreprocessConfig(size=256))
    assert mask_iou(out.mask, clean.mask) > 0.95


def test_uneven_lighting_photo() -> None:
    # Grey paper with a strong left-to-right shadow gradient and sensor noise.
    rng = np.random.default_rng(1)
    h = w = 400
    paper = np.tile(np.linspace(110, 230, w), (h, 1))
    img = paper.copy()
    cv2.circle(img, (200, 200), 120, 0, thickness=5)
    img = np.clip(img * 0.9 + rng.normal(0, 4, img.shape), 0, 255).astype(np.uint8)
    out = preprocess_sketch(Image.fromarray(img), PreprocessConfig(size=256))
    assert out.warnings == ()
    assert mask_iou(out.mask, _reference_disk(256, 0.1)) > 0.9


def test_faint_pencil_line_is_found() -> None:
    img = np.full((400, 400), 255, dtype=np.uint8)
    cv2.circle(img, (200, 200), 120, 205, thickness=3)
    out = preprocess_sketch(Image.fromarray(img), PreprocessConfig(size=256))
    assert mask_iou(out.mask, _reference_disk(256, 0.1)) > 0.9


def test_blank_image_raises() -> None:
    blank = Image.fromarray(np.full((200, 200), 255, dtype=np.uint8))
    with pytest.raises(SketchError, match="no strokes"):
        preprocess_sketch(blank)


def test_accepts_path(tmp_path) -> None:
    p = tmp_path / "s.png"
    _circle_sketch().save(p)
    assert preprocess_sketch(p, PreprocessConfig(size=64)).mask.any()


def test_missing_file_raises(tmp_path) -> None:
    with pytest.raises(SketchError, match="not found"):
        preprocess_sketch(tmp_path / "nope.png")
