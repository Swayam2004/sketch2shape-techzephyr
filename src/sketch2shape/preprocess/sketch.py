from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

from sketch2shape.types import IMAGE_SIZE, PreparedSketch

log = logging.getLogger(__name__)


class SketchError(ValueError):
    """The input cannot be turned into a usable sketch."""


@dataclass(frozen=True)
class PreprocessConfig:
    size: int = IMAGE_SIZE
    # Fraction of the canvas left empty on each side, so the object never touches the edge.
    margin: float = 0.1
    # Stroke width in output pixels. ControlNet scribble was trained on bold lines.
    stroke_width: int = 3
    # Ink blobs smaller than this fraction of the input area are treated as paper noise.
    min_blob_fraction: float = 0.0002
    # Gaps up to this fraction of the output size get closed before filling the silhouette.
    gap_close_fraction: float = 0.03
    # Below this grey-level range the image is treated as blank.
    min_contrast: int = 30
    # A pixel is ink when it is this many grey levels darker than its local average. Adaptive
    # rather than global so a shadow across a phone photo does not turn into ink.
    threshold_offset: int = 12
    # The outline counts as closed when filling it adds at least this much area over the
    # strokes alone, or when the strokes already cover this share of their convex hull.
    closed_gain: float = 1.3
    solid_fraction: float = 0.6


@dataclass(frozen=True)
class PreprocessResult:
    scribble: (
        np.ndarray
    )  # (size, size) uint8, white strokes (255) on black, ControlNet scribble input
    mask: np.ndarray  # (size, size) bool, filled outer silhouette, compared against renders in eval
    source_bbox: tuple[int, int, int, int]  # x, y, w, h of the strokes in the original image
    warnings: tuple[str, ...] = ()

    def scribble_image(self) -> Image.Image:
        return Image.fromarray(self.scribble, mode="L")

    def rgb_image(self) -> Image.Image:
        """Black strokes on white, the view a person expects to see."""
        return Image.fromarray(255 - self.scribble).convert("RGB")

    def mask_image(self) -> Image.Image:
        return Image.fromarray(self.mask.astype(np.uint8) * 255)


def prepare_sketch(image: Image.Image) -> PreparedSketch:
    """Pipeline entry point. Matches the stage contract in `sketch2shape.types`."""
    result = preprocess_sketch(image)
    return PreparedSketch(
        rgb=result.rgb_image(), mask=result.mask, scribble=result.scribble_image()
    )


def preprocess_sketch(
    source: Image.Image | Path | str, config: PreprocessConfig | None = None
) -> PreprocessResult:
    cfg = config or PreprocessConfig()
    gray = _load_gray(source)

    if int(gray.max()) - int(gray.min()) < cfg.min_contrast:
        raise SketchError("Sketch has no strokes: the image is a single flat colour.")

    # Faint pencil lines sit in a narrow grey band. Stretch it before looking at the border
    # or thresholding, otherwise the offset below is larger than the line contrast.
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

    # Canvas exports are dark-on-light, but chalkboard-style uploads exist. The border is
    # mostly paper, so its median tells us which side is ink.
    border = np.concatenate([gray[0], gray[-1], gray[:, 0], gray[:, -1]])
    if np.median(border) < 128:
        gray = 255 - gray

    ink = _threshold_ink(gray, cfg)
    ink = _drop_small_blobs(ink, cfg.min_blob_fraction * ink.size)
    if not ink.any():
        raise SketchError("Sketch has no strokes after removing noise. Draw darker or larger.")

    x, y, w, h = cv2.boundingRect(ink)
    strokes = fit_to_square(ink[y : y + h, x : x + w], cfg.size, cfg.margin)

    if cfg.stroke_width > 1:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (cfg.stroke_width, cfg.stroke_width))
        strokes = cv2.dilate(strokes, k)

    mask, warnings = _fill_silhouette(strokes, cfg)
    for message in warnings:
        log.warning("preprocess: %s", message)
    log.info(
        "preprocess: input %sx%s, strokes bbox %s, output %s px, mask coverage %.2f",
        gray.shape[1],
        gray.shape[0],
        (x, y, w, h),
        cfg.size,
        mask.mean(),
    )
    return PreprocessResult(
        scribble=strokes, mask=mask, source_bbox=(x, y, w, h), warnings=warnings
    )


def fit_to_square(img: np.ndarray, size: int, margin: float) -> np.ndarray:
    """Scale a cropped binary image to fit a size x size canvas, centred, aspect preserved.

    Used by both preprocess and eval so the sketch mask and the rendered mesh land in the
    same frame, which makes silhouette IoU independent of scale and position.
    """
    if not 0 <= margin < 0.5:
        raise ValueError(f"margin must be in [0, 0.5), got {margin}")
    h, w = img.shape[:2]
    inner = max(1, round(size * (1 - 2 * margin)))
    scale = inner / max(h, w)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    # INTER_AREA plus a low threshold keeps thin strokes alive when shrinking a big upload.
    resized = cv2.resize(img.astype(np.uint8), (nw, nh), interpolation=cv2.INTER_AREA)
    resized = np.where(resized > 32, 255, 0).astype(np.uint8)
    canvas = np.zeros((size, size), dtype=np.uint8)
    ox, oy = (size - nw) // 2, (size - nh) // 2
    canvas[oy : oy + nh, ox : ox + nw] = resized
    return canvas


def _load_gray(source: Image.Image | Path | str) -> np.ndarray:
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.is_file():
            raise SketchError(f"Sketch file not found: {path}")
        try:
            img = Image.open(path)
            img.load()
        except (UnidentifiedImageError, OSError) as exc:
            raise SketchError(f"Cannot read sketch image {path}: {exc}") from exc
    else:
        img = source

    # Transparent canvas exports would otherwise turn black and read as all ink.
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        paper = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        img = Image.alpha_composite(paper, rgba)
    return np.asarray(img.convert("L"), dtype=np.uint8)


def _drop_small_blobs(binary: np.ndarray, min_area: float) -> np.ndarray:
    n, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    keep = np.zeros(n, dtype=bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_area
    return np.where(keep[labels], 255, 0).astype(np.uint8)


def _threshold_ink(gray: np.ndarray, cfg: PreprocessConfig) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    # Window about an eighth of the short side. It must be wider than a stroke so the local
    # average is mostly paper.
    block = max(15, min(gray.shape) // 8) | 1
    return cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        block,
        cfg.threshold_offset,
    )


def _fill_silhouette(
    strokes: np.ndarray, cfg: PreprocessConfig
) -> tuple[np.ndarray, tuple[str, ...]]:
    k = max(3, int(cfg.size * cfg.gap_close_fraction) | 1)
    closed = cv2.morphologyEx(
        strokes, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    )
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(closed)
    cv2.drawContours(filled, contours, -1, 255, thickness=cv2.FILLED)

    # An outline that never closes encloses nothing, so filling it gives back the strokes.
    ink_area = int(np.count_nonzero(closed))
    filled_area = int(np.count_nonzero(filled))
    hull = cv2.convexHull(np.concatenate(contours))
    hull_filled = np.zeros_like(closed)
    cv2.fillConvexPoly(hull_filled, hull, 255)
    hull_area = int(np.count_nonzero(hull_filled))

    encloses_area = filled_area >= cfg.closed_gain * ink_area
    is_solid = ink_area >= cfg.solid_fraction * hull_area
    if encloses_area or is_solid:
        return filled > 0, ()
    message = (
        "The outline does not close, so the silhouette uses the convex hull of the strokes. "
        "Close the shape for a more faithful result."
    )
    return hull_filled > 0, (message,)
