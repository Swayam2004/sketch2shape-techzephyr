"""Zip blender_addon/sketch2shape_addon for Blender's "Install from disk".

    uv run python scripts/package_blender_addon.py

Writes outputs/sketch2shape_blender_addon.zip. The zip holds one top-level folder, which is what
Blender expects.
"""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path

logger = logging.getLogger("package_blender_addon")

ROOT = Path(__file__).resolve().parents[1]
ADDON_DIR = ROOT / "blender_addon" / "sketch2shape_addon"
OUT_PATH = ROOT / "outputs" / "sketch2shape_blender_addon.zip"


def build_zip(addon_dir: Path = ADDON_DIR, out_path: Path = OUT_PATH) -> Path:
    if not (addon_dir / "__init__.py").is_file():
        raise FileNotFoundError(f"No add-on found in {addon_dir}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(addon_dir.rglob("*.py")):
            archive.write(path, Path(addon_dir.name) / path.relative_to(addon_dir))
    return out_path


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    path = build_zip()
    logger.info("Wrote %s (%d bytes)", path, path.stat().st_size)


if __name__ == "__main__":
    main()
