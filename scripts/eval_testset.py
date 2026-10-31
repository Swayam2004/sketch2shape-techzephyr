"""Run every test sketch through the pipeline and score it with silhouette IoU.

    uv run python scripts/eval_testset.py [--sketch-dir samples/sketches] [--out outputs/eval]

Writes `results.csv` and `results.md` into the output folder. Paste the Markdown table into
EXPERIMENTS.md. The seed is fixed at 0 so two runs of the same code give the same table.

`prompts.json` in the sketch folder maps a file name or stem to a prompt, for example
`{"mug.png": "a blue ceramic mug"}`. A sketch with no entry runs without a prompt.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import trimesh
from PIL import Image

from sketch2shape.eval import silhouette_iou
from sketch2shape.preprocess import prepare_sketch
from sketch2shape.types import Device, GenerationRequest

log = logging.getLogger("eval_testset")

EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
SEED = 0


@dataclass
class Row:
    sketch: str
    iou: float | None = None
    seconds: float | None = None
    vertices: int | None = None
    error: str = ""


def _pick_device() -> Device:
    forced = os.environ.get("S2S_BACKEND", "").strip().lower()
    if forced in ("cuda", "cpu"):
        return forced  # type: ignore[return-value]
    try:
        import torch
    except ImportError:
        return "cpu"
    return "cuda" if torch.cuda.is_available() else "cpu"


def _load_prompts(sketch_dir: Path) -> dict[str, str]:
    path = sketch_dir / "prompts.json"
    if not path.is_file():
        log.warning("No prompts.json in %s, running without prompts", sketch_dir)
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must be a JSON object mapping file names to prompts")
    return {str(k): str(v) for k, v in data.items()}


def _write_outputs(rows: list[Row], out_dir: Path, device: Device) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "results.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["sketch", "iou", "seconds", "vertices", "error"])
        for r in rows:
            writer.writerow(
                [r.sketch, _fmt(r.iou, 4), _fmt(r.seconds, 1), r.vertices or "", r.error]
            )

    scored = [r.iou for r in rows if r.iou is not None]
    lines = [
        f"Seed {SEED}, device {device}, {len(scored)} of {len(rows)} sketches scored.",
        "",
        "| Sketch | IoU | Seconds | Vertices | Failure |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        lines.append(
            f"| {r.sketch} | {_fmt(r.iou, 3)} | {_fmt(r.seconds, 1)} | {r.vertices or ''} | {r.error} |"
        )
    if scored:
        lines += ["", f"Mean IoU {sum(scored) / len(scored):.3f}, min {min(scored):.3f}."]
    (out_dir / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fmt(value: float | None, digits: int) -> str:
    return "" if value is None else f"{value:.{digits}f}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sketch-dir", type=Path, default=Path("samples/sketches"))
    parser.add_argument("--out", type=Path, default=Path("outputs/eval"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    paths = sorted(p for p in args.sketch_dir.glob("*") if p.suffix.lower() in EXTENSIONS)
    if not paths:
        log.error("No sketches found in %s", args.sketch_dir)
        return 1

    try:
        from sketch2shape import pipeline
    except ImportError as exc:
        log.error("pipeline.py is not available yet (%s). Pull Swayam's branch first.", exc)
        return 1

    device = _pick_device()
    prompts = _load_prompts(args.sketch_dir)
    log.info("Scoring %d sketches on %s with seed %d", len(paths), device, SEED)

    rows: list[Row] = []
    for path in paths:
        row = Row(sketch=path.name)
        rows.append(row)
        try:
            with Image.open(path) as src:
                sketch = src.copy()
            prompt = prompts.get(path.name) or prompts.get(path.stem)
            mask = prepare_sketch(sketch).mask

            start = time.perf_counter()
            result = pipeline.run(
                GenerationRequest(sketch=sketch, prompt=prompt, seed=SEED), device
            )
            row.seconds = time.perf_counter() - start

            mesh = trimesh.load(result.paths.glb, force="mesh")
            row.vertices = len(mesh.vertices)
            row.iou = silhouette_iou(mesh, mask)
            log.info("%s: iou %.3f in %.1f s", path.name, row.iou, row.seconds)
        # One bad sketch must not hide the other eleven. The error text goes into the table.
        except Exception as exc:  # noqa: BLE001
            row.error = f"{type(exc).__name__}: {exc}"[:120]
            log.error("%s failed: %s", path.name, row.error)

    _write_outputs(rows, args.out, device)
    log.info("Wrote %s and %s", args.out / "results.csv", args.out / "results.md")
    return 1 if any(r.error for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
