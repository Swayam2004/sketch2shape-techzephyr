# Plan

Kickoff Sat 31 Oct 12:00 IST. Hard stop Sun 1 Nov 12:00. Treat 10:30 as the real deadline. Decisions and their reasons are in `CONTEXT.md`.

## Scoring

| Criterion | Pts | Where we earn it |
| --- | --- | --- |
| Technical implementation | 25 | Typed stage interfaces, error handling, documented model choices |
| 3D output quality and design | 25 | Sketch fidelity, textured mesh, cleanup, best-of-N by silhouette IoU |
| End-to-end validity and efficiency | 20 | Draw or upload to GLB with no manual step, measured runtime and VRAM |
| Code reproducibility | 15 | Fresh clone to a working run on all three OSes, pinned deps, scripted weight download |
| Documentation and README | 15 | Timings, hardware, limitations, samples, troubleshooting |

## Architecture

```
                    +--> Gradio app (sketchpad, upload, prompt, 3D viewer, download)
client  --HTTP-->   |
                    +--> CLI
FastAPI service ----+--> Blender add-on (sends sketch, imports the returned .glb)
      |
      v
pipeline: preprocess -> sketch-to-image (SD1.5 + ControlNet scribble, or LCM few-step)
          -> cutout (rembg, permissive model) -> image-to-3D (TripoSR first)
          -> mesh cleanup (trimesh) -> validate -> export .glb/.obj
      |
backend = cuda | cpu | remote   (auto-detected, overridable by S2S_BACKEND)
```

Each stage is one function with a typed input and output, so a model swap never touches the API or the UI.

## Tiers for judges

1. Hosted link. Gradio on a cloud GPU, with a queue, a rate limit and a throwaway access code. Shutdown date is announced and can be extended from the backend.
2. Local NVIDIA GPU. `scripts/setup.*`, then one run command. The app detects CUDA and uses it.
3. Local CPU lite mode. Runs anywhere. The UI warns that results are slower and slightly less accurate. It still produces a valid `.glb`. This tier is mandatory.

## Compute

- Dev GPU now. One shared RunPod Secure Cloud pod, L4 first (about 1,300 INR for 24 hours, 4090 about 1,900), with a 50 GB network volume. Udit's international card pays. Everyone connects over SSH. Steps in `docs/guides/runpod-dev-gpu.md`.
- AWS credits (about $100 per person, 136 to 146 days left). Optional and Swayam-only, for cheap demo hosting. Needs a Paid plan upgrade and a G-instance quota request. Steps in `docs/guides/aws-gpu-optional.md`. Stop after 30 minutes if it stalls.
- Hosted demo priority. AWS GPU VM on credits, then Modal, then a RunPod pod during judging windows. The RunPod proxy cuts requests at 100 seconds, so the API uses job polling.
- Extra spend cap of 1,500 to 2,000 INR combined.
- Research behind this is in `docs/research/`. All claims there are agent-reported unless marked verified.

## Our angle

Single-view 3D invents the hidden side, so "faithful to the sketch" needs a number. Render the mesh outline from the input view and compute IoU against the cleaned sketch mask.

1. It compares model choices in `EXPERIMENTS.md`, in place of the CV score from the playbook.
2. Best-of-N. Generate N images with different seeds, reconstruct each, keep the highest IoU. Measure the extra runtime.
3. Twelve fixed test sketches so every change is compared on the same inputs.

The Blender add-on is the second angle. Only start it when the core path, UI and docs work.

## Timeline

| By | Milestone |
| --- | --- |
| 15:00 | Repo on GitHub, all three have cloned and run setup. Dev GPU box up. AWS upgrade and quota request sent. Organiser message sent |
| 17:00 | One hand-picked image becomes a `.glb` on the GPU box (TripoSR) and opens in Blender. Twelve test sketches drawn. Preprocess and eval skeletons exist |
| 20:00 | Full chain via CLI and API on the GPU box. Gradio UI calls the API. CPU lite smoke test passes on Windows and Mac |
| 23:00 | First hosted demo URL. Timings and VRAM logged for the README |
| 23:00 to 04:00 | Quality loop on the test set (IoU, cleanup, best-of-N, failure handling). Blender add-on v0 by 03:00 if the core is green |
| 08:00 | Code freeze. Only bug fixes and docs |
| 09:00 | Demo video recorded |
| 09:30 | Fresh clone on Windows and Mac, README only, record how long it takes |
| 10:30 | Submission package complete. Repo goes public, sample `.glb` and inputs included |
| 11:00 | Submit. One hour of slack |

## Deliverables checklist

From the rulebook (sections 6 and 9) and the problem statement. See D12 and D13 in `CONTEXT.md`.

- [ ] GitHub repo, public before submission, with source, README and setup instructions
- [ ] `REPORT.md` or PDF with problem, approach, datasets, architecture, metrics, results and analysis, real-world application
- [ ] Dataset and model list with sources and licences (we use pretrained models and our own sketches)
- [ ] At least one `.glb` or `.obj` plus example inputs and outputs in `samples/`
- [ ] Time to generate a model, hardware used, limitations, in the README
- [ ] Slides (rulebook asks for them even though judging is offline, confirm with organisers)
- [ ] Demo video
- [ ] Hosted demo link and a throwaway access code in the submission
- [ ] `AI_USAGE.md` complete

## Documentation owed from hour 1

`README.md` (objective, architecture, dependencies, install, run, model choices, inputs and outputs, time per model, hardware, limitations, troubleshooting, third-party table), `EXPERIMENTS.md`, `AI_USAGE.md`, `STATUS.md`.

## Before the repo goes public

- Search the whole history for keys, tokens, account IDs and personal data.
- Decide whether `.claude/skills/` stays. Some skills are third-party.
- Confirm `.notes/` is not tracked.
- Make sure the README names every model, repo, API and licence.

## Open questions

1. Organiser reply on submission method, slides and video, credentials, judging dates, judge GPU. Message drafted, not yet sent.
2. Model choice, see `docs/research/model-options.md`.
3. Which host serves the public demo. Priority order is set, final pick follows the first benchmark.
