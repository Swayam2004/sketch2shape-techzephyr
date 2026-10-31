"""Run image_to_mesh on one RGBA image and write a GLB. Usage: s2_smoke.py <rgba.png> [out.glb]."""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

import torch
from PIL import Image

from sketch2shape.reconstruct import image_to_mesh

logger = logging.getLogger("s2_smoke")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("out", type=Path, nargs="?", default=Path("outputs/s2_smoke.glb"))
    parser.add_argument("--device", choices=["cuda", "cpu"], default=None)
    parser.add_argument("--resolution", type=int, default=None)
    parser.add_argument("--chunk", type=int, default=8192)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    rgba = Image.open(args.image).convert("RGBA")

    started = time.perf_counter()
    mesh = image_to_mesh(
        rgba, seed=args.seed, device=device, resolution=args.resolution, chunk_size=args.chunk
    )
    seconds = time.perf_counter() - started

    args.out.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(args.out)
    logger.info(
        "device=%s %.1fs total, %d vertices, %d faces, watertight=%s, wrote %s",
        device,
        seconds,
        len(mesh.vertices),
        len(mesh.faces),
        mesh.is_watertight,
        args.out,
    )


if __name__ == "__main__":
    main()
