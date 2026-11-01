"""Remove the background from a generated image and frame the object for TripoSR."""

from __future__ import annotations

import logging
import os
from functools import lru_cache

import numpy as np
from PIL import Image

from sketch2shape.types import IMAGE_SIZE
from sketch2shape.weights import rembg_home

logger = logging.getLogger(__name__)

# The newer rembg default model carries a licence that needs a paid agreement (AGENTS.md).
MODEL_NAME = "isnet-general-use"
# TripoSR expects the object to fill about 85 percent of the frame.
FOREGROUND_RATIO = 0.85
ALPHA_THRESHOLD = 10


@lru_cache(maxsize=1)
def _session():
    # rembg reads U2NET_HOME at import time, so set it before the import.
    os.environ.setdefault("U2NET_HOME", str(rembg_home()))
    from rembg import new_session

    return new_session(MODEL_NAME, providers=["CPUExecutionProvider"])


def center_object(rgba: Image.Image, ratio: float | None = None) -> Image.Image:
    """Crop to the object, then paste it centred so its longer side is `ratio` of the frame.

    `ratio` defaults to FOREGROUND_RATIO, read at call time so tune.py can vary it.
    """
    ratio = FOREGROUND_RATIO if ratio is None else ratio
    alpha = np.asarray(rgba)[..., 3]
    ys, xs = np.nonzero(alpha > ALPHA_THRESHOLD)
    if len(xs) == 0:
        raise ValueError("No foreground found. The image is empty after background removal.")
    crop = rgba.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    target = round(IMAGE_SIZE * ratio)
    scale = target / max(crop.size)
    crop = crop.resize(
        (max(1, round(crop.width * scale)), max(1, round(crop.height * scale))),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGBA", (IMAGE_SIZE, IMAGE_SIZE), (0, 0, 0, 0))
    canvas.paste(crop, ((IMAGE_SIZE - crop.width) // 2, (IMAGE_SIZE - crop.height) // 2))
    return canvas


def remove_background(image: Image.Image) -> Image.Image:
    """RGB image to a centred RGBA cut-out, IMAGE_SIZE square."""
    from rembg import remove

    cut = remove(image.convert("RGB"), session=_session()).convert("RGBA")
    out = center_object(cut)
    logger.info("Background removed with %s", MODEL_NAME)
    return out
