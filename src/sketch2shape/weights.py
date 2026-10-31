"""Where model weights live on disk.

`scripts/download_weights.py` writes here, the stages read from here. One place, so the stage
code never hard-codes a path.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WEIGHTS_DIR = "weights"


def weights_dir() -> Path:
    """`S2S_WEIGHTS_DIR` if set, else `weights/`. A relative value is taken from the repo root."""
    raw = Path(os.environ.get("S2S_WEIGHTS_DIR") or DEFAULT_WEIGHTS_DIR).expanduser()
    return raw if raw.is_absolute() else REPO_ROOT / raw


def triposr_dir() -> Path:
    return weights_dir() / "triposr"


def sd15_dir() -> Path:
    return weights_dir() / "sd15"


def controlnet_scribble_dir() -> Path:
    return weights_dir() / "controlnet-scribble"


def rembg_home() -> Path:
    """Value for `REMBG_HOME`. rembg puts the model under `<home>/models/<name>/`."""
    return weights_dir() / "rembg"
