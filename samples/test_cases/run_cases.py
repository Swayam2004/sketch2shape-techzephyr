"""Run every case in cases.json through the pipeline in one process.

    uv run python samples/test_cases/run_cases.py [--out outputs/cases] [--seed 0]

One process means the models load once, so the per-case seconds are warm numbers. Writes a
`.glb`, the generated image and `results.md` into the output folder.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from PIL import Image

from sketch2shape.pipeline import run
from sketch2shape.types import GenerationRequest

log = logging.getLogger("run_cases")
HERE = Path(__file__).parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("outputs/cases"))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--only", nargs="*", default=None, help="case ids to run")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
    if args.only:
        cases = [c for c in cases if c["id"] in args.only]
    args.out.mkdir(parents=True, exist_ok=True)

    rows = [
        "| Case | Level | Prompt | IoU | Seconds | Faces | Watertight | Warnings |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in cases:
        sketch = Image.open(HERE / case["sketch"])
        request = GenerationRequest(sketch=sketch, prompt=case["prompt"] or None, seed=args.seed)
        try:
            result = run(request, out_dir=args.out, stem=case["id"])
        except (
            ValueError,
            RuntimeError,
            OSError,
        ) as exc:  # one failed case must not stop the batch
            log.error("case %s failed: %s", case["id"], exc)
            rows.append(
                f"| {case['id']} | {case['level']} | {case['prompt']} | failed | - | - | - | {exc} |"
            )
            continue
        seconds = sum(t.seconds for t in result.timings)
        iou = f"{result.silhouette_iou:.3f}" if result.silhouette_iou is not None else "-"
        rows.append(
            f"| {case['id']} | {case['level']} | {case['prompt'] or '(none)'} | {iou} | {seconds:.1f} "
            f"| {result.validation.face_count} | {result.validation.is_watertight} "
            f"| {'; '.join(result.warnings) or '-'} |"
        )
        log.info("case %s: iou %s, %.1f s", case["id"], iou, seconds)
    (args.out / "results.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    log.info("wrote %s", args.out / "results.md")


if __name__ == "__main__":
    main()
