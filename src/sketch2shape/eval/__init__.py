"""Evaluation: silhouette IoU between a reconstructed mesh and the cleaned sketch mask."""

from sketch2shape.eval.silhouette import VIEWS, mask_iou, render_silhouette, silhouette_iou

__all__ = ["VIEWS", "mask_iou", "render_silhouette", "silhouette_iou"]
