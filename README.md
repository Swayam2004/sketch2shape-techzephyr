# Sketch2Shape AI

Draw or upload a rough sketch, add an optional text prompt, and get a textured 3D mesh as `.glb` or `.obj`. Built for TechZephyr 4.0 at IIT Bhubaneswar, a 24 hour hackathon.

Status. The pipeline is under construction. Sections marked TODO get filled as the code lands. The plan is in `PLAN.md` and the task split is in `docs/tasks/`.

## How it works

```
sketch + prompt -> preprocess -> SD 1.5 + ControlNet scribble -> background removal -> TripoSR -> cleanup and checks -> .glb and .obj
```

Every stage runs the same models and the same default settings on every machine. Only the device changes, `cuda` on an NVIDIA GPU and `cpu` everywhere else. A CPU run takes longer and the app says so.

TODO a diagram and a short paragraph per stage.

## Three ways to run it

1. Hosted link. Nothing to install. TODO URL and access code.
2. Local, with an NVIDIA GPU. TripoSR needs about 6 GB of VRAM.
3. Local, on CPU. Works on any laptop and takes longer.

## Requirements

TODO OS, Python 3.11 (uv installs it), RAM, disk for weights, optional GPU.

## Install

TODO exact commands per OS, including the weight download. Note for Windows users with an NVIDIA GPU that the default PyTorch wheel is CPU only.

## Run

TODO the UI command, the CLI command and an example.

## Inputs and outputs

TODO accepted formats and sizes, output files and where they are written.

## Results

TODO a sample sketch, the generated image, a render of the mesh and a link to `samples/`.

## Timing and hardware

TODO a table of seconds and peak memory per stage, per device, measured on our machines. Say which machines.

## Models and third-party components

| Component | Source | Licence | Used for |
| --- | --- | --- | --- |
| TripoSR | `stabilityai/TripoSR`, code from VAST-AI-Research/TripoSR | MIT | Image to 3D |
| Stable Diffusion 1.5 | `stable-diffusion-v1-5/stable-diffusion-v1-5` | CreativeML OpenRAIL-M | Sketch to image |
| ControlNet scribble v1.1 | `lllyasviel/control_v11p_sd15_scribble` | OpenRAIL | Keeps the sketch outline |
| rembg, `isnet-general-use` | danielgatis/rembg | MIT (library), model terms TODO | Background removal |

TODO add the remaining libraries (trimesh, scikit-image, diffusers and the rest).

## Limitations

TODO. A single view hides the back of the object, so the model guesses it. Add the failure cases we see.

## Troubleshooting

TODO real errors from our own runs.

## What did not work

See `EXPERIMENTS.md`. TODO a summary.

## AI tool usage

See `AI_USAGE.md`.

## Team

Himansu Swayam, Dishashree Swain and Udit Arun Nath.
