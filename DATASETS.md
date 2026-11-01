# Datasets

We trained and fine-tuned nothing. The pipeline runs four pretrained models, and the only data we made is a set of our own sketches. No public dataset enters the repo, the evaluation or the pipeline at run time.

## Data we made

| Set | Files | Source | Use |
| --- | --- | --- | --- |
| Real sketches | 12 JPEGs in `samples/sketches/` (bottle, bulb, button, cactus, candle, cloud, cup, donut, envelope, icecream, key, paperclip), one prompt each in `samples/sketches/prompts.json` | Pen sketches drawn by Disha and photographed on paper | Test set for every change. Results in `samples/sketches/results/` and `EXPERIMENTS.md` rows 14 to 17 |
| Synthetic test cases | 9 PNGs in `samples/test_cases/` (mug, table, chair, lamp, house, bicycle, robot, sailboat, guitar) plus `cases.json` | Drawn by `samples/test_cases/make_sketches.py` with a fixed seed. Strokes wobble slightly to look hand drawn | Difficulty levels and prompt tests. Results in `samples/test_cases/results/` |
| Output meshes | `.glb` files and generated images in `samples/meshes/` | Produced by this pipeline from the sets above | Demo outputs, open them in Blender |

The sketches carry no third-party content and no personal data.

## Data behind the pretrained models

We did not download or touch these datasets. They are listed because the rulebook asks for the source of the data a solution depends on. Each model's weights download by script (`scripts/download_weights.py`).

| Model | Training data, as the authors state it | Status | Source |
| --- | --- | --- | --- |
| TripoSR | Rendered objects from a curated subset of Objaverse (CC-BY licensed items) | Verified on the model card and in the paper | https://huggingface.co/stabilityai/TripoSR, https://arxiv.org/abs/2403.02151 |
| Stable Diffusion 1.5 | Subsets of LAION-5B | Reported by the authors, not checked by us | https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5 |
| ControlNet scribble v1.1 | Image and synthesised scribble pairs, see the card | Not checked by us | https://huggingface.co/lllyasviel/control_v11p_sd15_scribble |
| rembg `isnet-general-use` | IS-Net general-use weights trained for dichotomous image segmentation | Not checked by us | https://github.com/danielgatis/rembg |

Two consequences for the results.

- TripoSR learned from clean product-style renders, so raw line art is out of its distribution. That is why a Stable Diffusion step turns the sketch into an object image first.
- We cannot report a score against a public benchmark. Our metric is silhouette IoU between the sketch outline and the mesh outline, measured on our own 21 sketches.
