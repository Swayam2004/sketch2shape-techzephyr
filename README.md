# Sketch2Shape AI

Turns a rough 2D sketch (drawn in the app or uploaded) and an optional text prompt into a textured 3D asset exported as `.glb` or `.obj`. Built for TechZephyr 4.0, IIT Bhubaneswar, 24 hour hackathon.

> Status: scaffold only. Sections marked TODO get filled as the pipeline lands. See `docs/PLAN.md`.

## Pipeline

TODO diagram and one paragraph per stage.

```
sketch + prompt -> preprocess -> sketch-to-image -> cutout -> image-to-3D -> cleanup -> validate -> .glb/.obj
```

## Requirements

TODO OS, Python version, GPU and VRAM, disk for weights, RAM.

## Install

TODO exact commands, including weight download.

## Run

TODO UI command, CLI command, example.

## Inputs and outputs

TODO accepted formats, sizes, output files, where they are written.

## Results

TODO sample sketch, generated image, rendered mesh, link to `samples/`.

## Timing and hardware

TODO table of seconds and peak VRAM per stage, per backend, on the dev machine (GTX 1650 Ti, 4 GB).

## Models and third-party components

| Component | Source | Licence | Used for |
| --- | --- | --- | --- |
| TODO | | | |

## Limitations

TODO hidden-side geometry is guessed, VRAM limits, failure cases we saw.

## Troubleshooting

TODO

## What did not work

See `EXPERIMENTS.md`. TODO summary.

## AI tool usage

See `AI_USAGE.md`.

## Team

TODO
