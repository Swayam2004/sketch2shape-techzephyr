"""Write a contact sheet of input, mask and scribble for every sketch in a folder.

    uv run python scripts/preprocess_check.py [sketch_dir] [output.png]

Look at the sheet yourself. A mask that is cut off or merged with the background is a bug.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from sketch2shape.preprocess import SketchError, preprocess_sketch

log = logging.getLogger("preprocess_check")

EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
CELL = 192


def _tile(image: Image.Image) -> Image.Image:
    tile = Image.new("RGB", (CELL, CELL), "white")
    thumb = image.convert("RGB")
    thumb.thumbnail((CELL, CELL))
    tile.paste(thumb, ((CELL - thumb.width) // 2, (CELL - thumb.height) // 2))
    return tile


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sketch_dir", nargs="?", type=Path, default=Path("samples/sketches"))
    parser.add_argument(
        "output", nargs="?", type=Path, default=Path("outputs/preprocess_check.png")
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    paths = sorted(p for p in args.sketch_dir.glob("*") if p.suffix.lower() in EXTENSIONS)
    if not paths:
        log.error("No sketches found in %s", args.sketch_dir)
        return 1

    sheet = Image.new("RGB", (CELL * 3, (CELL + 16) * len(paths)), "white")
    draw = ImageDraw.Draw(sheet)
    failures = 0
    for row, path in enumerate(paths):
        top = row * (CELL + 16)
        draw.text((4, top + 2), path.name, fill="black")
        try:
            result = preprocess_sketch(path)
        except SketchError as exc:
            failures += 1
            log.error("%s: %s", path.name, exc)
            draw.text((CELL + 4, top + 40), f"FAILED: {exc}", fill="red")
            continue
        for note in result.warnings:
            log.warning("%s: %s", path.name, note)
        with Image.open(path) as src:
            tiles = [_tile(src), _tile(result.mask_image()), _tile(result.scribble_image())]
        for col, tile in enumerate(tiles):
            sheet.paste(tile, (col * CELL, top + 16))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output)
    log.info("Wrote %s with %d sketches, %d failed", args.output, len(paths), failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
