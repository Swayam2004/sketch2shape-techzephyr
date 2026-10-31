# Model options

> Status note, 31 Oct 15:30. The team chose TripoSR as the single model on every device (`CONTEXT.md` D18). The recommended stack and the "lite" path below are superseded. The comparison itself still holds.

Decision aid for the model choice. Facts come from `backend-feasibility.md` (agent-reported, labelled verified or reported there). Nothing is benchmarked on our machines yet. The benchmark list is at the bottom.

## Stage 3 and 4. Image to 3D

| Model | VRAM | Licence | Output | Strengths | Weaknesses |
| --- | --- | --- | --- | --- | --- |
| TripoSR | About 6 GB on GPU. CPU works. | MIT | Mesh with vertex colours. UV bake possible through xatlas. | Smallest and simplest. Runs on every tier. Open licence, no gating. We know its install traps. | Lower detail than newer models. Texture is basic. CPU time reported from 25 s to 6 min. Trained on Objaverse renders, so raw line art is off-distribution and needs the SD stage in front. `torchmcubes` needs a shim. |
| Stable Fast 3D | About 6 GB. CPU flag exists. | Stability Community licence, gated on Hugging Face | UV-unwrapped textured mesh with material estimates | Better textures than TripoSR. Fast. | Gated, so judges need an HF token. Windows needs Visual Studio 2022. Mac under 32 GB should use CPU. |
| Hunyuan3D-2mini | About 5 to 6 GB shape only. About 16 GB with texture. | Tencent community licence, excludes EU, UK and South Korea | Shape, and PBR-style texture with the paint model | Likely the best visual quality we can run on a 24 GB pod. Not gated. | Texture needs CUDA kernels, so no CPU or Mac texture. Heavier install. Licence territory limit. |
| Hunyuan3D-2.1 | 10 GB shape, 21 GB texture, 29 GB both | Tencent community licence | Same family, higher quality | Better again on a big GPU | Does not fit a 24 GB card for both stages together. Skip for now. |
| TRELLIS, TRELLIS.2 | 16 GB and 24 GB minimum | MIT plus submodule terms | Strong meshes and textures | Top quality of the group | Linux and NVIDIA only, hard install. Remote experiment at most. |
| TripoSG-scribble | More than 8 GB | MIT | Shape directly from scribble plus prompt | Skips the SD stage. Strong novelty angle | Shape only as far as we know, no texture. Remote only. |
| InstantMesh, Unique3D | Not researched | Not researched | | Named in the problem statement | We have no numbers. They are not safe to plan on without a check. |

## Stage 2. Sketch to image

| Option | Fit | Strengths | Weaknesses |
| --- | --- | --- | --- |
| SD 1.5 plus ControlNet scribble, fp16 | Runs on 4 GB with offload, on any GPU, slowly on CPU (1 to 4 min est.) | Matches the problem statement. Keeps the sketch structure. Prompt adds colour and material. | OpenRAIL licence terms. 20 to 60 s on a small GPU. fp16 gives black images on GTX 16xx cards. |
| Same with LCM-LoRA, 4 steps | Same memory | 5 to 15 s on the small GPU. Makes CPU tier less painful. | Documented with canny, not scribble. Fidelity to the sketch is unproven. |
| T2I-Adapter sketch (SD 1.5) | Smaller than a ControlNet by design | Apache-2.0 | No speed figures found. Needs a quality test. |
| SDXL scribble ControlNet | Heavy, remote only | Better images | Does not fit our CPU or small-GPU tiers |
| Skip generation (lite mode) | Fastest | Works on every laptop | Raw sketches are off-distribution for TripoSR, so quality drops |

## Background removal

`rembg` with `u2net` or `isnet-general-use`. Avoid the new default model because its licence needs a paid agreement.

## Recommended starting stack

1. GPU path (dev pod and hosted demo). SD 1.5 plus scribble ControlNet, then `rembg`, then TripoSR with a UV bake.
2. Quality experiment on the pod. Hunyuan3D-2mini shape plus texture. If it clearly wins on the test set, it becomes the hosted-demo mode while the TripoSR path stays as the reproducible local default.
3. Comparison only. Stable Fast 3D on the pod, using one of our tokens, to measure the gap. Not a default because it is gated.
4. CPU lite path. Skip SD, run `rembg` and TripoSR on CPU with the scikit-image marching cubes shim.
5. LCM-LoRA is tested in hour one as the speed fix for the SD stage.

## Benchmark list for the dev pod

1. TripoSR on the pod at mc-resolution 128, 192, 256. Seconds and VRAM.
2. SD 1.5 plus scribble, 25 steps against LCM 4 steps. Silhouette IoU on the 12 test sketches.
3. Hunyuan3D-2mini shape and texture on the same inputs.
4. Stable Fast 3D on the same inputs.
5. CPU lite run on the Windows and Mac laptops. Seconds per object.
6. Output check in Blender. Opens, non-empty, texture visible.
