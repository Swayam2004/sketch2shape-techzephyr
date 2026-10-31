# Sketch2Shape AI report

Living report. Agents append short facts under each "Draft facts" list during their sessions. Disha does the final pass at the end, rewrites the facts into prose in the team's voice, and checks every number against `EXPERIMENTS.md`. Keep real failures and numbers in, because that is what makes it read as genuine.

Fact format. `- 31 Oct 17:20 (Udit) TripoSR on the L4 took 4.1 s at mc-resolution 192, peak 5.8 GB. Source EXPERIMENTS #3.`

## Problem statement

Draft facts

## Solution approach

Draft facts

- 31 Oct 16:45 (Swayam) TripoSR is vendored under `src/sketch2shape/vendor/tsr/` at upstream commit 107cefd instead of installed from PyPI. Changes are listed in its `SOURCE.md`. `torchmcubes` is replaced by scikit-image marching cubes, and the texture bake is dropped, so the mesh carries vertex colours.
- 31 Oct 16:45 (Swayam) `image_to_mesh` composites the RGBA cutout on mid grey, as TripoSR was trained, then extracts the mesh at a marching-cubes grid of 192 on CPU and 256 on CUDA. Same code path, one setting.

## Datasets used

We use pretrained models and our own sketches. List each model, source and licence.

Draft facts

## Model architecture

Draft facts

- 31 Oct 16:45 (Swayam) TripoSR is a DINO ViT-B/16 image encoder, a 16 layer transformer that produces a triplane, and a small NeRF MLP. The mesh comes from sampling its density on a grid and running marching cubes. Weights are 1.68 GB (`stabilityai/TripoSR`, MIT).
- 31 Oct 16:45 (Swayam) TripoSR has no sampling step, so the seed does not change its output. Variation between runs has to come from the sketch-to-image stage.

## Evaluation metrics

Silhouette IoU against the cleaned sketch mask, time per model, peak memory, failure rate on the 12 test sketches.

Draft facts

- 31 Oct (Udit) Silhouette IoU renders the mesh outline orthographically without OpenGL (one `fillConvexPoly` per triangle, because overlapping front and back faces cancel under even-odd filling). Mesh and sketch mask are both cropped to their bounding box, so the score ignores scale and position. Unit tests: a unit cube against a square mask scores above 0.97, a sphere beats a box against a disc.

## Results and analysis

Draft facts

- 31 Oct 16:45 (Swayam) First real run. TripoSR on an M2 MacBook Air CPU, chair image, grid 192. 7.1 s to load, 32.9 s to reconstruct, 5.6 GB RAM, 22,779 vertices. The hidden side looks plausible (EXPERIMENTS #1).
- 31 Oct 16:45 (Swayam) Grid 256 on the same CPU took 112.1 s and 8.6 GB RAM, 3.4 times the time of grid 192 (EXPERIMENTS #2). We keep 192 on CPU.
- 31 Oct 23:35 (Swayam) TripoSR on the GTX 1650 Ti at grid 256 uses 2370 MB peak VRAM and reconstructs in 5.4 s, against 112 s on the M2 CPU at the same grid. We first expected 6 GB, because the library default sends all grid points through the MLP at once. Setting the renderer chunk size to 8192 bounds that. Chunk 2048 gave the same peak. The 4 GB card is enough, with no half precision.
- 31 Oct 16:45 (Swayam) TripoSR's own frame has Z up and the front of the object facing +X. The pipeline needs Y up and front on +Z, so `finalize_mesh` has to apply `(x, y, z) -> (y, z, x)`. Found by rendering the mesh from three sides.

## What did not work and how we recovered

Draft facts

- 31 Oct 16:45 (Swayam) First load of the TripoSR checkpoint failed. The weights use the transformers 4.35 names for the ViT layers (`encoder.layer.N.attention.attention.query`) and the locked transformers 5 renamed them (`layers.N.attention.q_proj`). We rename the checkpoint keys while loading instead of pinning the old library.
- 31 Oct 16:45 (Swayam) First marching cubes swap gave triangles that face inward. A test on a sphere (negative volume) caught it. Switching skimage to `gradient_direction="descent"` fixed it.
- 31 Oct 16:45 (Swayam) Upstream downloads `facebook/dino-vitb16/config.json` at load time. We inline the config so a run needs no network after the weights are in place.

## Real-world application

Draft facts
