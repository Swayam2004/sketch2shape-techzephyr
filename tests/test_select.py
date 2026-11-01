import cv2
import numpy as np
import pytest
from PIL import Image

from sketch2shape.eval import select_best_candidate


def _shape_mask(kind: str, size: int = 128) -> np.ndarray:
    m = np.zeros((size, size), dtype=np.uint8)
    if kind == "disk":
        cv2.circle(m, (size // 2, size // 2), size // 3, 255, thickness=-1)
    elif kind == "wide":
        cv2.rectangle(m, (10, 50), (size - 10, 78), 255, thickness=-1)
    return m > 0


def _cutout(mask: np.ndarray) -> Image.Image:
    """RGBA picture whose alpha is the mask, the shape cutout.remove_background returns."""
    rgba = np.zeros((*mask.shape, 4), dtype=np.uint8)
    rgba[mask] = (200, 120, 60, 255)
    return Image.fromarray(rgba, "RGBA")


def test_picks_the_candidate_that_matches_the_sketch() -> None:
    sketch = _shape_mask("disk")
    result = select_best_candidate(sketch, [_cutout(_shape_mask("wide")), _cutout(sketch)])
    assert result.index == 1
    assert result.scores[1] > 0.95
    assert result.scores[0] < 0.5


def test_score_ignores_position_and_scale_like_the_mesh_iou() -> None:
    sketch = _shape_mask("disk", 128)
    small_shifted = np.zeros((128, 128), dtype=np.uint8)
    cv2.circle(small_shifted, (40, 90), 20, 255, thickness=-1)
    result = select_best_candidate(sketch, [_cutout(small_shifted > 0)])
    assert result.scores[0] > 0.95


def test_candidate_sizes_may_differ_from_the_sketch() -> None:
    result = select_best_candidate(_shape_mask("disk", 128), [_cutout(_shape_mask("disk", 512))])
    assert result.scores[0] > 0.95


def test_empty_candidate_scores_zero_and_ties_go_to_the_first() -> None:
    sketch = _shape_mask("disk")
    empty = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    result = select_best_candidate(sketch, [empty, empty])
    assert result.scores == (0.0, 0.0)
    assert result.index == 0


def test_bad_inputs_raise_clear_errors() -> None:
    with pytest.raises(ValueError, match="no candidates"):
        select_best_candidate(_shape_mask("disk"), [])
    with pytest.raises(ValueError, match="sketch mask is empty"):
        select_best_candidate(np.zeros((8, 8), bool), [_cutout(_shape_mask("disk"))])
