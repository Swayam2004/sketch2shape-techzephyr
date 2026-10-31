from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from PIL import Image

from sketch2shape.eval.silhouette import mask_iou, normalise_mask

log = logging.getLogger(__name__)

# Same cut-off cutout.remove_background uses to find the object in its alpha channel.
ALPHA_THRESHOLD = 10


@dataclass(frozen=True)
class Selection:
    """Winner of a best-of-N pick. `scores` holds one 2D IoU per candidate, in input order."""

    index: int
    scores: tuple[float, ...]


def select_best_candidate(
    sketch_mask: np.ndarray, candidates: Sequence[Image.Image], margin: float = 0.1
) -> Selection:
    """Pick the cut-out whose outline best matches the cleaned sketch mask.

    Candidates are the RGBA pictures from `cutout.remove_background`, one per seed. That step
    recentres and rescales the object, so both outlines are fitted to the same frame before the
    IoU, the way `silhouette_iou` does for the 3D mesh. An empty cut-out scores 0.0 instead of
    raising, so one failed seed does not sink the request. Ties go to the lowest index, which
    keeps the choice deterministic for a fixed seed list.
    """
    if not candidates:
        raise ValueError("no candidates to choose from")
    target = normalise_mask(sketch_mask, margin=margin, name="sketch mask")

    scores: list[float] = []
    for i, cut in enumerate(candidates):
        alpha = np.asarray(cut.convert("RGBA"))[..., 3] > ALPHA_THRESHOLD
        if not alpha.any():
            log.warning("select: candidate %d has no foreground, scoring it 0", i)
            scores.append(0.0)
            continue
        # Cut-outs from rembg are square, but a caller may pass another size.
        side = max(alpha.shape)
        padded = np.zeros((side, side), dtype=bool)
        padded[: alpha.shape[0], : alpha.shape[1]] = alpha
        scores.append(mask_iou(normalise_mask(padded, target.shape[0], margin), target))

    best = int(np.argmax(scores))
    log.info(
        "select: best candidate %d of %d, 2D IoU scores %s",
        best,
        len(scores),
        [round(s, 3) for s in scores],
    )
    return Selection(index=best, scores=tuple(scores))
