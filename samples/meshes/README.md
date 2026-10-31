# Sample outputs

Real pipeline outputs from a RunPod RTX PRO 4500 Blackwell (32 GB), 1 Nov 2026. Input is `chair_input.png`, prompt "a wooden chair", fp16, marching cubes grid 256. See `EXPERIMENTS.md` rows 8 and 9 for timings.

| File | Seed | Silhouette IoU | Vertices | Faces |
| --- | --- | --- | --- | --- |
| `chair_seed1.glb` | 1 | 0.953 | 32,482 | 64,960 |
| `chair_seed2.glb` | 2 | 0.943 | 40,228 | 80,452 |

`chair_seed1_generated.png` is the image that Stable Diffusion produced from the sketch before TripoSR built the mesh. Both meshes are watertight and carry vertex colours. Open them in Blender with File, Import, glTF 2.0, then set the viewport shading colour to Attribute.
