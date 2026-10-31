# Plan

Kickoff Sat 31 Oct 12:00 IST. Hard stop Sun 1 Nov 12:00. Treat 10:30 as the real deadline.

## What changed from the playbook

The playbook assumed a tabular ML task with a leaderboard. The real task is a generative pipeline judged on a 100 point rubric (`problem-statement.pdf`, last pages).

| Criterion | Pts | Where we earn it |
| --- | --- | --- |
| Technical implementation | 25 | Clean stage interfaces, error handling, documented model choices |
| 3D output quality and design | 25 | Sketch fidelity, textured mesh, cleanup, best-of-N selection |
| End-to-end validity and efficiency | 20 | Draw/upload to GLB with no manual step, measured runtime and VRAM |
| Code reproducibility | 15 | Fresh clone to a working run, pinned deps, scripted weight download |
| Documentation | 15 | README with timings, hardware, limitations, sample outputs |

Still valid from the playbook: rubric first, working skeleton early, experiment log from hour 0, AI disclosure, README written alongside the code, fresh-clone test before submitting. Not applicable: CV folds, ensembling, seed averaging.

The brochure rulebook said no pre-existing code and mandatory AI disclosure. Assume both apply. Everything starts from this repo, and `AI_USAGE.md` stays current.

## Hardware is the main risk

Dev machine has a GTX 1650 Ti with 4 GB VRAM, 22 GB RAM (about 10 GB free) and 28 GB free disk.

- TripoSR needs about 6 GB VRAM at default settings ([press coverage](https://renderu.com/en/news/post/25204)). Fitting 4 GB needs fp16, smaller marching-cubes chunks, or CPU fallback.
- Hunyuan3D-2mini is quoted at 5 to 6 GB for shape only ([WaveSpeedAI](https://wavespeed.ai/blog/posts/introducing-wavespeed-ai-hunyuan3d-v2-mini-on-wavespeedai), [Hunyuan3D-2GP](https://openi.pcl.ac.cn/NewestAI/Hunyuan3D-2GP)). Nobody confirmed 4 GB. InstantMesh and Unique3D are out of reach locally.
- SD 1.5 plus a scribble ControlNet should fit in fp16 with CPU offload, but no source confirmed 4 GB. Measure it in the first hour.

So the pipeline gets a backend switch from day one. `local` runs on the 4 GB card (offload, then CPU). `remote` calls a GPU we control (Kaggle or Colab notebook, or a hosted Space) for faster, higher quality runs. Judges will follow the README on their own hardware, so `local` must work end to end even if it is slow, and every remote dependency must be documented.

## Pipeline

```
sketch (canvas or upload) + optional prompt
  -> preprocess      resize, pad to square, binarise, denoise, scribble map
  -> sketch-to-image SD 1.5 + ControlNet scribble (skippable "lite" mode)
  -> cutout          rembg, centre and rescale the object
  -> image-to-3D     TripoSR first, swap candidates behind one interface
  -> mesh cleanup    trimesh, keep largest component, fill holes, normalise scale
  -> validate        non-empty, watertight report, reload test, texture present
  -> export          .glb (primary), .obj
  -> Gradio UI       sketchpad, upload, prompt box, Model3D viewer, download
```

Each stage is a function with a typed input and output so a model can be swapped without touching the UI.

## Angle for the innovation and quality points

Single-view 3D invents the hidden side, so "faithful to the sketch" needs a number. Render the mesh silhouette from the input viewpoint and compute IoU against the cleaned sketch mask. That gives us:

1. A metric to compare model choices in `EXPERIMENTS.md`. This replaces the CV score from the playbook.
2. Best-of-N selection. Generate N images with different seeds, reconstruct each, keep the highest IoU. The cost is N times the runtime, so measure it.
3. A fixed set of 10 to 15 test sketches (simple objects, rough strokes, one hard case, one with a prompt) so every change is compared on the same inputs.

## Timeline

| By | Milestone |
| --- | --- |
| 12:30 | Env created, GPU check done, weights downloading, answers to open questions below |
| 14:00 | Image-to-3D alone works: a hand-picked image gives a `.glb` that opens in Blender |
| 16:00 | Full chain via CLI, sketch to `.glb`, with and without the ControlNet stage |
| 18:00 | Gradio UI with canvas, upload, prompt and 3D viewer. Timings and VRAM logged |
| 18:00 to 02:00 | Quality loop on the test set, silhouette IoU, cleanup, best-of-N, failure handling |
| 02:00 to 08:00 | Two people sleep in shifts. Others run the test set and write README sections |
| 08:00 | Code freeze. Only bug fixes and docs after this |
| 09:30 | Fresh clone on a second machine, follow the README only, record the time |
| 10:30 | Submission package complete: repo, sample `.glb` files, inputs and outputs, README |
| 11:00 | Submit. One hour of slack |

## Work order for the first hour

1. Create the env with uv. Install torch with the CUDA build matching driver 580 (CUDA 13 capable). Check `torch.cuda.is_available()`.
2. Clone TripoSR into a vendored folder with its licence. The `torchmcubes` dependency is commonly reported as painful to build. Plan to replace it with scikit-image marching cubes if it fails.
3. Run TripoSR on one downloaded test image. Record VRAM and seconds.
4. Load SD 1.5 plus scribble ControlNet with fp16 and offload. Record VRAM and seconds.
5. Write down which combination fits the 4 GB card, then fix the stage interfaces.

## Documentation we owe from hour 1

- `README.md`, filled as we go. Required: objective, architecture, dependencies, install, run, model choices, inputs and outputs, time per model, hardware, limitations.
- `EXPERIMENTS.md`, one row per run including failures.
- `AI_USAGE.md`, every AI tool and what it did.
- A third-party table in the README listing every model, repo, API and licence.

## Open questions

1. Which rubric do judges use, the problem statement's 100 points or the brochure's? Ask Aditya (6387559209).
2. Is a live demo required? The statement says "final demonstration". A local run on whose laptop?
3. Does the evaluation environment have a GPU? "Available evaluation environment" is vague and decides how much effort `remote` deserves.
4. Team size and roles. Suggested split with four people: pipeline and models, UI, evaluation and test set, docs and reproducibility.
5. Remote GPU. Do we have Kaggle or Colab quota, or anyone with a bigger card?
6. Where does the final repo live? A private GitHub repo shared with the organisers, or a zip?
