"""Sketch preprocessing: raw drawing or upload -> scribble map and filled silhouette mask."""

from sketch2shape.preprocess.sketch import (
    PreprocessConfig,
    PreprocessResult,
    SketchError,
    fit_to_square,
    prepare_sketch,
    preprocess_sketch,
)

__all__ = [
    "PreprocessConfig",
    "PreprocessResult",
    "SketchError",
    "fit_to_square",
    "prepare_sketch",
    "preprocess_sketch",
]
