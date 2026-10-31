"""Command line entry point: `sketch2shape generate sketch.png --prompt "..." --out outputs/`."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from PIL import Image

from sketch2shape.pipeline import run, select_device
from sketch2shape.types import GenerationRequest

logger = logging.getLogger("sketch2shape")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sketch2shape")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate", help="Turn a sketch into a .glb and .obj")
    gen.add_argument("sketch", type=Path)
    gen.add_argument("--prompt", default=None)
    gen.add_argument("--seed", type=int, default=0)
    gen.add_argument("--out", type=Path, default=Path("outputs"))
    gen.add_argument("--device", choices=["cuda", "cpu"], default=None)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    if not args.sketch.is_file():
        parser.error(f"{args.sketch} is not a file.")
    request = GenerationRequest(Image.open(args.sketch), args.prompt, args.seed)
    result = run(request, select_device(args.device), out_dir=args.out)

    logger.info("glb: %s", result.paths.glb)
    logger.info("obj: %s", result.paths.obj)
    logger.info("validation: %s", result.validation)
    if result.silhouette_iou is not None:
        logger.info("silhouette IoU: %.3f", result.silhouette_iou)
    for warning in result.warnings:
        logger.warning(warning)
    return 0 if result.validation.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
