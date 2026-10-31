# Sketch2Shape AI report

Living report. Agents append short facts under each "Draft facts" list during their sessions. Disha does the final pass at the end, rewrites the facts into prose in the team's voice, and checks every number against `EXPERIMENTS.md`. Keep real failures and numbers in, because that is what makes it read as genuine.

Fact format. `- 31 Oct 17:20 (Udit) TripoSR on the L4 took 4.1 s at mc-resolution 192, peak 5.8 GB. Source EXPERIMENTS #3.`

## Problem statement

A modeller needs hours to turn a rough drawing into a 3D asset. We want a tool where a user draws or uploads a sketch, optionally types a short prompt, and gets a textured mesh as `.glb` or `.obj` in minutes. The export must be real 3D geometry that opens in Blender, not a rendered image or a flat textured plane.

The organisers asked for a localhost run and a 2 to 3 minute video, so judges run the project on their own machine. That makes hardware the main constraint. Our dev laptop has a 4 GB GTX 1650 Ti, a judge may have no NVIDIA card at all, and the pipeline has to behave the same in both cases.

Draft facts

## Solution approach

The pipeline has six stages. Preprocess cleans the sketch (Otsu threshold, speck removal, 512 px canvas). Stable Diffusion 1.5 with a ControlNet scribble model turns the sketch and prompt into an object image that keeps the sketch outline. rembg with `isnet-general-use` removes the background. TripoSR predicts a triplane from the image, and scikit-image marching cubes extracts a mesh. A finalize step keeps the largest component, rotates to glTF axes and fits a unit cube. The export step writes `.glb` and `.obj` with vertex colours and checks that the file loads.

```mermaid
flowchart LR
    A[Sketch + prompt] --> B[Preprocess]
    B --> C[SD 1.5 + ControlNet scribble]
    C --> D[rembg isnet-general-use]
    D --> E[TripoSR + marching cubes]
    E --> F[Finalize mesh]
    F --> G[Validate, export .glb and .obj]
```

We chose one image-to-3D model for every device so results match across machines. TripoSR is MIT licensed, ungated and runs on CPU and GPU. We vendored its code instead of installing it, because the upstream texture bake has open bugs and `torchmcubes` is hard to build. The mesh keeps vertex colours.

Draft facts

- 31 Oct 16:45 (Swayam) TripoSR is vendored under `src/sketch2shape/vendor/tsr/` at upstream commit 107cefd instead of installed from PyPI. Changes are listed in its `SOURCE.md`. `torchmcubes` is replaced by scikit-image marching cubes, and the texture bake is dropped, so the mesh carries vertex colours.
- 31 Oct 16:45 (Swayam) `image_to_mesh` composites the RGBA cutout on mid grey, as TripoSR was trained, then extracts the mesh at a marching-cubes grid of 192 on CPU and 256 on CUDA. Same code path, one setting.
- TripoSR (Tochilkin et al., arXiv 2403.02151, p. 2) guesses camera extrinsics and intrinsics instead of taking them as input. It takes one 512 x 512 image and reports about 0.5 s on an A100. The paper tests on GSO and OmniObject3D object sets and says nothing about sketches.
- ControlNet (Zhang et al., ICCV 2023, p. 3817) trained with 50% empty prompts, so a scribble works without text. With no prompt, control on both CFG branches removes classifier-free guidance (Section 3.4). The prompt fallback is therefore a swept setting, not a default.
- SketchDream (Liu et al., ACM TOG 2024, p. 44:2) says a ControlNet image lifted by an image-to-3D model gives distorted unseen views and fuzzy back textures. Our back side is a model guess for the same reason.
- Training-free control costs too much for the hosted limit. FreeControl needs 176.31 s per image on an A6000 (CVPR 2024, Table 2, p. 7472). We use ControlNet.

## Datasets used

We trained nothing and used no dataset. The inputs are pretrained models and our own sketches.

| Model | Source | Licence |
| --- | --- | --- |
| TripoSR | `stabilityai/TripoSR` | MIT |
| Stable Diffusion 1.5 | `stable-diffusion-v1-5/stable-diffusion-v1-5` | CreativeML Open RAIL-M |
| ControlNet scribble v1.1 | `lllyasviel/control_v11p_sd15_scribble` | OpenRAIL |
| rembg `isnet-general-use` | danielgatis/rembg | MIT library, model terms to confirm |

The test set is twelve single-object sketches that team members drew or photographed, in `samples/sketches/`. They mix clean marker, messy pencil, thick brush and photographed paper, and two are deliberately bad. TODO count and describe the final set.

Draft facts

## Model architecture

TripoSR has a DINO ViT-B/16 image encoder, a 16 layer transformer that produces a triplane, and a small NeRF MLP. We sample its density on a grid and run marching cubes. The weights are 1.68 GB. The model has no sampling step, so the seed does not change its output. Variation between runs comes from the sketch-to-image stage.

The generate stage runs SD 1.5 (20 steps in our first run) with a ControlNet scribble branch. ControlNet was trained with 50% empty prompts, so a sketch works without text.

Draft facts

- 31 Oct 16:45 (Swayam) TripoSR is a DINO ViT-B/16 image encoder, a 16 layer transformer that produces a triplane, and a small NeRF MLP. The mesh comes from sampling its density on a grid and running marching cubes. Weights are 1.68 GB (`stabilityai/TripoSR`, MIT).
- 31 Oct 16:45 (Swayam) TripoSR has no sampling step, so the seed does not change its output. Variation between runs has to come from the sketch-to-image stage.

## Evaluation metrics

Silhouette IoU is the headline number. We render the mesh outline orthographically, crop both the outline and the cleaned sketch mask to their bounding boxes, and divide the overlap by the union. Cropping makes the score ignore scale and position. Unit tests pin it: a unit cube against a square mask scores above 0.97. We also report seconds per stage, peak VRAM and the failure rate on the twelve test sketches.

IoU is a simple checkable proxy for sketch fidelity, not a perceptual score. No accepted automatic metric exists for this task. TripoSR returns no camera, so a raw IoU at a fixed view can undercount a good mesh. We plan to also report aligned IoU and best IoU over a small grid of views.

Draft facts

- 31 Oct (Udit) Silhouette IoU renders the mesh outline orthographically without OpenGL (one `fillConvexPoly` per triangle, because overlapping front and back faces cancel under even-odd filling). Mesh and sketch mask are both cropped to their bounding box, so the score ignores scale and position. Unit tests: a unit cube against a square mask scores above 0.97, a sphere beats a box against a disc.
- Sketch2Model (Zhang et al., CVPR 2021, Table 4, p. 6015) measures sketch fidelity as the IoU between the mesh projected to the ground-truth view and the sketch silhouette. Its mean is 0.716 for a baseline and 0.745 with a predicted view. We use the same idea with a cleaned sketch mask.
- TripoSR does not return a camera. TripoSR's own shape metrics align predictions with a brute-force rotation search plus ICP (p. 4). We therefore plan to report raw IoU at a fixed view, aligned IoU and best IoU over a small view grid, with raw IoU as the headline.
- SKED defines Intersection-over-Sketch, the share of the sketch covered by the generated mask. Mean 0.8220 with its silhouette loss and 0.0211 without, on five samples (ICCV 2023, Table 2, p. 14568).
- There is no accepted automatic metric for sketch simplification, and papers use visual comparison or user studies (Xu et al., TPAMI 2023, p. 295). Silhouette IoU is a simple checkable proxy, not a perceptual score.

## Results and analysis

All numbers below are measured and come from `EXPERIMENTS.md`.

| Run | Machine | Time | Memory |
| --- | --- | --- | --- |
| TripoSR, grid 192, CPU | M2 MacBook Air | 32.9 s | 5.6 GB RAM |
| TripoSR, grid 192, CPU | Linux laptop | 22.5 s | not measured |
| TripoSR, grid 256, CPU | M2 MacBook Air | 112.1 s | 8.6 GB RAM |
| TripoSR, grid 256, GPU | GTX 1650 Ti | 5.4 s | 2370 MB VRAM |
| Full pipeline, sketch stages stubbed | GTX 1650 Ti | 14 s cold, 6.6 s warm | 2370 MB VRAM |

Grid 256 on CPU takes 3.4 times as long as grid 192, so the CPU default is 192. The same chair gives 22,779 vertices on both CPUs, so the CPU path is deterministic across machines. On the GPU a chunked density query keeps TripoSR at 2370 MB, well under the 6 GB we first expected.

TODO the full pipeline on the RunPod GPU, the generate stage on CPU, and mean silhouette IoU over the test set. These runs were not finished when this draft was written.

Draft facts

- 31 Oct 16:45 (Swayam) First real run. TripoSR on an M2 MacBook Air CPU, chair image, grid 192. 7.1 s to load, 32.9 s to reconstruct, 5.6 GB RAM, 22,779 vertices. The hidden side looks plausible (EXPERIMENTS #1).
- 31 Oct 16:45 (Swayam) Grid 256 on the same CPU took 112.1 s and 8.6 GB RAM, 3.4 times the time of grid 192 (EXPERIMENTS #2). We keep 192 on CPU.
- 31 Oct 23:35 (Swayam) TripoSR on the GTX 1650 Ti at grid 256 uses 2370 MB peak VRAM and reconstructs in 5.4 s, against 112 s on the M2 CPU at the same grid. We first expected 6 GB, because the library default sends all grid points through the MLP at once. Setting the renderer chunk size to 8192 bounds that. Chunk 2048 gave the same peak. The 4 GB card is enough, with no half precision.
- 1 Nov 00:15 (Swayam) First full pipeline run on the GTX 1650 Ti, with a stub for the sketch stages. 14 s end to end, peak VRAM 2370 MB at reconstruct, watertight mesh with vertex colours. The model load (6.7 s) happens once per process, so the server loads it at startup. `finalize_mesh` keeps the largest connected component, merges duplicate vertices, rotates TripoSR's frame (Z up, front +X) to glTF (Y up, front +Z) and fits a unit cube. A cone test with a coloured apex pins the front axis.
- 1 Nov 01:00 (Swayam) The API runs one worker thread, because one GPU runs one TripoSR job at a time. The queue holds 5 waiting jobs and extra submissions get 429. The server loads TripoSR and rembg at startup, so a job on the GTX 1650 Ti takes 6.6 s instead of about 14 s with the cold load. Jobs and files are deleted an hour after they finish.
- 31 Oct 16:45 (Swayam) TripoSR's own frame has Z up and the front of the object facing +X. The pipeline needs Y up and front on +Z, so `finalize_mesh` has to apply `(x, y, z) -> (y, z, x)`. Found by rendering the mesh from three sides.
- 1 Nov 03:40 (Swayam) First real end-to-end GPU run on a rented RTX PRO 4500 Blackwell (32 GB, $0.72 per hour): chair sketch to a watertight GLB with vertex colours, silhouette IoU 0.953 (seed 1) and 0.943 (seed 2) (EXPERIMENTS #8, #9). SD 1.5 diffusion takes about 6 s for 20 steps, TripoSR about 2.7 s at grid 256. A cold CLI run takes 4 to 5 minutes, almost all of it loading models from a network volume, so the server loads them at startup. Peak VRAM was 5.1 GB.
- 1 Nov 04:55 (Swayam) Test of 18 cases on the RunPod GPU, one process, seed 0 (EXPERIMENTS #10, #11, images in `samples/test_cases/results/`). Nine sketches from a mug to a guitar gave mean silhouette IoU 0.796 and every mesh was one watertight piece with vertex colours. Warm runs take 5 to 6 s. Prompts change material and style (red velvet, gingerbread, steampunk, glass) but the sketch wins when the two disagree: "a porcelain teapot" on a mug sketch still gives a mug.
- 1 Nov 04:55 (Swayam) Limits seen in the 18 case run. TripoSR guesses depth from one view, so a guitar comes out 0.90 as deep as it is wide. A white object on a light grey generated background defeats rembg (IoU 0.384 for the chair sketch prompted as "a horse"). "Grey stone" did not render as stone.

## What did not work and how we recovered

- The TripoSR checkpoint failed to load under transformers 5, which renamed the ViT layers. We rename the keys while loading instead of pinning the old library.
- The first marching cubes swap produced inward-facing triangles. A sphere test with negative volume caught it, and `gradient_direction="descent"` fixed it.
- TripoSR's frame is Z up with the front on +X. We found this by rendering the mesh from three sides and rotate to glTF axes in `finalize_mesh`.
- The generate stage does not fit a 4 GB card. fp16 returned a black frame after 92 s, and the fp32 retry ran out of memory because the fp16 pipeline stayed cached (`EXPERIMENTS.md` row 7). The stage runs on a larger GPU, and a fix that frees the fp16 pipeline first is in review.
- TODO the deliberately bad sketches and what we changed to recover them.

Draft facts

- 1 Nov 04:05 (Udit) The whole pipeline ran on a Windows laptop with no GPU (Ryzen 7 PRO 7840U, 16 GB) in 305.6 s with 7.23 GB peak RAM (EXPERIMENTS #9). Stable Diffusion with ControlNet took 263.3 s of that, TripoSR 25.6 s, the cutout 8.0 s. A judge on CPU waits about 5 minutes per sketch, which is why the API uses job polling. Best-of-N with N=4 would multiply the generate time to about 18 minutes, past our own 15 minute poll limit.

- 1 Nov 04:40 (Udit) On Swayam's 4 GB GTX 1650 Ti the fp16 Stable Diffusion pass returned a black frame after 92 s, and the fp32 retry then ran out of memory at 3560 MB because the fp16 pipeline was still in the `lru_cache`. The retry now clears the cache, runs `gc.collect()` and empties the CUDA cache first (EXPERIMENTS #7, #8). The VAE also stays in fp32 when the UNet runs in fp16, which is our suspected cause of the black frame. Not yet confirmed on a CUDA card.

- 31 Oct 16:45 (Swayam) First load of the TripoSR checkpoint failed. The weights use the transformers 4.35 names for the ViT layers (`encoder.layer.N.attention.attention.query`) and the locked transformers 5 renamed them (`layers.N.attention.q_proj`). We rename the checkpoint keys while loading instead of pinning the old library.
- 31 Oct 16:45 (Swayam) First marching cubes swap gave triangles that face inward. A test on a sphere (negative volume) caught it. Switching skimage to `gradient_direction="descent"` fixed it.
- 31 Oct 16:45 (Swayam) Upstream downloads `facebook/dino-vitb16/config.json` at load time. We inline the config so a run needs no network after the weights are in place.

## Real-world application

The output is a standard `.glb` with vertex colours, so it drops into Blender, a game engine or a 3D printing slicer. A designer can block out props from a napkin sketch and refine the mesh by hand. An art teacher can show students what a drawing looks like in 3D. The limits matter for these uses. The back of the object is a model guess, and the mesh is a starting point for an artist, not a finished asset.

Draft facts
