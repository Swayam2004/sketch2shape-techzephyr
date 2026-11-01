"""Compare selection by 3D score with and without a front-view, no-shadow prompt.

    uv run python samples/test_cases/viewpoint_compare.py

Writes outputs/vp2/vp.md. Front vs side is the IoU between the +z and +x silhouettes, a rough
measure of whether the back of a roundish object was invented sensibly. Flat objects such as a
key or an envelope score low on it by design.
"""

import importlib
import json
import logging
from pathlib import Path

import trimesh
from PIL import Image

from sketch2shape.eval.silhouette import mask_iou, normalise_mask, render_silhouette
from sketch2shape.pipeline import run
from sketch2shape.types import GenerationRequest

st = importlib.import_module("sketch2shape.generate.sketch_to_image")
logging.basicConfig(level=logging.WARNING)
prompts = json.loads(Path("samples/sketches/prompts.json").read_text())
FRONT = "{prompt}, front view, product design render, single object, centred, plain white background, soft even studio lighting, no shadow"
NEG = (
    st.NEGATIVE_PROMPT
    + ", cast shadow, floor, ground plane, three-quarter view, angled view, top view"
)
variants = {"select3d": (st.PROMPT_TEMPLATE, st.NEGATIVE_PROMPT), "select3d_front": (FRONT, NEG)}
rows = [
    "| Variant | Sketch | IoU | Front vs side | Depth over width |",
    "| --- | --- | --- | --- | --- |",
]
out = Path("outputs/vp2")
out.mkdir(parents=True, exist_ok=True)
for name, (tmpl, neg) in variants.items():
    st.PROMPT_TEMPLATE, st.NEGATIVE_PROMPT = tmpl, neg
    for stem in [p.stem for p in sorted(Path("samples/sketches").glob("*.jpeg"))] + [
        "icecream_strawberry"
    ]:
        img = Image.open(f"samples/sketches/{stem.split('_')[0]}.jpeg")
        prompt = "strawberry icecream" if stem == "icecream_strawberry" else prompts[f"{stem}.jpeg"]
        r = run(GenerationRequest(img, prompt, 0), out_dir=out, stem=f"{name}_{stem}", candidates=3)
        m = trimesh.load(r.paths.glb, force="mesh")
        f, s = render_silhouette(m, 256, "+z") > 0, render_silhouette(m, 256, "+x") > 0
        cons = mask_iou(normalise_mask(f, 256, 0.1), normalise_mask(s, 256, 0.1))
        rows.append(
            f"| {name} | {stem} | {r.silhouette_iou:.3f} | {cons:.3f} | {m.extents[2] / m.extents[0]:.2f} |"
        )
        print(rows[-1], flush=True)
Path(out / "vp.md").write_text("\n".join(rows) + "\n")
print("DONE")
