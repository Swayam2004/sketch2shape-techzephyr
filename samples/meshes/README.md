# Sample outputs

Real pipeline outputs from a RunPod RTX PRO 4500 Blackwell (32 GB), 1 Nov 2026. Input is `chair_input.png`, prompt "a wooden chair", fp16, marching cubes grid 256. See `EXPERIMENTS.md` rows 8 and 9 for timings.

| File | Seed | Silhouette IoU | Vertices | Faces |
| --- | --- | --- | --- | --- |
| `chair_seed1.glb` | 1 | 0.953 | 32,482 | 64,960 |
| `chair_seed2.glb` | 2 | 0.943 | 40,228 | 80,452 |

`chair_seed1_generated.png` is the image that Stable Diffusion produced from the sketch before TripoSR built the mesh. Both meshes are watertight and carry vertex colours. Open them in Blender with File, Import, glTF 2.0, then set the viewport shading colour to Attribute.

## Prompt and style cases (seed 0, same pod)

| File | Sketch | Prompt | Silhouette IoU |
| --- | --- | --- | --- |
| `guitar.glb` | `samples/test_cases/guitar.png` | an acoustic guitar | 0.896 |
| `robot_steampunk.glb` | `samples/test_cases/robot.png` | a rusty steampunk robot with brass gears | 0.785 |
| `chair_velvet.glb` | `samples/test_cases/chair.png` | a red velvet armchair | 0.877 |
| `house_glass.glb` | `samples/test_cases/house.png` | a modern glass and concrete house | 0.949 |

All four are single watertight meshes with vertex colours. The full 18 case table is in `samples/test_cases/results/README.md`.
