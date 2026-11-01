"""Try one change at a time on a few hard cases and print IoU and mesh depth.

    uv run python samples/test_cases/tune.py [--out outputs/tune] [--seed 0] [--candidates 3]

Each variant patches one module constant, runs the cases and restores it. Depth is the glTF Z
extent over the X extent of the final mesh, so 1.0 means as deep as wide.
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
from pathlib import Path

from PIL import Image

from sketch2shape.pipeline import run
from sketch2shape.types import GenerationRequest

log = logging.getLogger("tune")
HERE = Path(__file__).parent
CASES = ("guitar", "robot", "chair_as_horse")
GREY_TEMPLATE = (
    "{prompt}, product design render, single object, centred, plain medium grey background, "
    "soft studio lighting"
)

# name -> (module, constant, value)
VARIANTS: list[tuple[str, str, str, object]] = [
    ("baseline", "", "", None),
    ("controlnet 0.7", "sketch2shape.generate.sketch_to_image", "CONTROLNET_SCALE", 0.7),
    ("controlnet 0.5", "sketch2shape.generate.sketch_to_image", "CONTROLNET_SCALE", 0.5),
    ("grey background", "sketch2shape.generate.sketch_to_image", "PROMPT_TEMPLATE", GREY_TEMPLATE),
    ("foreground 0.7", "sketch2shape.cutout.background", "FOREGROUND_RATIO", 0.7),
    ("foreground 1.0", "sketch2shape.cutout.background", "FOREGROUND_RATIO", 1.0),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("outputs/tune"))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--candidates", type=int, default=3)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    cases = {c["id"]: c for c in json.loads((HERE / "cases.json").read_text(encoding="utf-8"))}
    rows = [
        "| Variant | Case | IoU | Depth over width | Seed kept |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name, module, const, value in VARIANTS:
        target = importlib.import_module(module) if module else None
        old = getattr(target, const) if target else None
        if target:
            setattr(target, const, value)
        try:
            for cid in CASES:
                case = cases[cid]
                request = GenerationRequest(
                    Image.open(HERE / case["sketch"]), case["prompt"] or None, args.seed
                )
                stem = f"{name.replace(' ', '_')}_{cid}"
                result = run(request, out_dir=args.out, stem=stem, candidates=args.candidates)
                import trimesh

                ext = trimesh.load(result.paths.glb, force="mesh").extents
                iou = result.silhouette_iou
                rows.append(
                    f"| {name} | {cid} | {iou:.3f} | {ext[2] / ext[0]:.2f} | {result.seed} |"
                )
                log.info(rows[-1])
        finally:
            if target:
                setattr(target, const, old)
    (args.out / "tune.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    log.info("wrote %s", args.out / "tune.md")


if __name__ == "__main__":
    main()
