# Sketch2Shape AI report

Living report. Agents append short facts under each "Draft facts" list during their sessions. Disha does the final pass at the end, rewrites the facts into prose in the team's voice, and checks every number against `EXPERIMENTS.md`. Keep real failures and numbers in, because that is what makes it read as genuine.

Fact format. `- 31 Oct 17:20 (Udit) TripoSR on the L4 took 4.1 s at mc-resolution 192, peak 5.8 GB. Source EXPERIMENTS #3.`

## Problem statement

Draft facts

## Solution approach

Draft facts

- 31 Oct (Udit) Preprocessing uses numpy and OpenCV only, no model. It stretches contrast, applies an adaptive threshold (so a shadow across a photo does not become ink), drops specks, crops to the strokes and resizes to 512 px. Closed outlines get a filled mask. Outlines that never close fall back to the convex hull and log a warning. Source `tests/test_preprocess.py`.
- 31 Oct (Udit) Sketch-to-image code is written (SD1.5 plus ControlNet scribble, UniPC, 20 steps, guidance 7.5, noise from a CPU generator so one seed starts from the same noise on every device). It is not run yet. It needs the weights on the pod.

## Datasets used

We use pretrained models and our own sketches. List each model, source and licence.

Draft facts

## Model architecture

Draft facts

## Evaluation metrics

Silhouette IoU against the cleaned sketch mask, time per model, peak memory, failure rate on the 12 test sketches.

Draft facts

- 31 Oct (Udit) Silhouette IoU renders the mesh outline orthographically without OpenGL (one `fillConvexPoly` per triangle, because overlapping front and back faces cancel under even-odd filling). Mesh and sketch mask are both cropped to their bounding box, so the score ignores scale and position. Unit tests: a unit cube against a square mask scores above 0.97, a sphere beats a box against a disc.

## Results and analysis

Draft facts

## What did not work and how we recovered

Draft facts

## Real-world application

Draft facts
