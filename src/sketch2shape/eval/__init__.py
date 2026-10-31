"""Evaluation: silhouette IoU between a reconstructed mesh and the cleaned sketch mask."""

from sketch2shape.eval.select import Selection, select_best_candidate
from sketch2shape.eval.silhouette import (
    VIEWS,
    mask_iou,
    normalise_mask,
    render_silhouette,
    silhouette_iou,
)

__all__ = [
    "VIEWS",
    "Selection",
    "mask_iou",
    "normalise_mask",
    "render_silhouette",
    "select_best_candidate",
    "silhouette_iou",
]
