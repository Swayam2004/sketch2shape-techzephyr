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
pipeline: preprocess -> sketch-to-image (SD1.5 + ControlNet scribble)
          -> cutout (rembg isnet-general-use) -> image-to-3D (TripoSR)
          -> mesh cleanup (trimesh) -> validate -> export .glb/.obj
      |
device = cuda | cpu   (auto-detected, overridable by S2S_BACKEND)
```

Each stage is one function with a typed input and output, so a model swap never touches the API or the UI.

## Tiers for judges

All three tiers run the same pipeline with the same default settings, so results match.

1. Hosted link. Gradio on Modal, with a queue, a rate limit and a throwaway access code. Shutdown date is announced and can be extended from the backend.
2. Local run with an NVIDIA GPU. `scripts/setup.*`, then one run command. The app detects CUDA and uses it.
3. Local run on CPU. Same models, slower. The UI warns that it will take a while. This tier is mandatory.

## Compute

- Dev GPU now. One shared RunPod Secure Cloud pod, L4 first (about 1,300 INR for 24 hours, 4090 about 1,900), with a 50 GB network volume. Udit's international card pays. Everyone connects over SSH. Steps in `docs/guides/runpod-dev-gpu.md`.
- AWS credits (about $100 per person, 136 to 146 days left). Optional and Swayam-only, for cheap demo hosting. Needs a Paid plan upgrade and a G-instance quota request. Steps in `docs/guides/aws-gpu-optional.md`. Stop after 30 minutes if it stalls.
- Hosted demo priority. Modal first, then a free ZeroGPU Space with a static page of samples, then a paid HF T4 Space. See D15 in `CONTEXT.md`. Judging lasts 5 to 6 days, so nothing runs always-on on a GPU. Hosted proxies cut calls at 100 to 150 seconds, so the API uses job polling.
- Extra spend cap of 1,500 to 2,000 INR combined.
- Research behind this is in `docs/research/`. All claims there are agent-reported unless marked verified.

## Our angle

Single-view 3D invents the hidden side, so "faithful to the sketch" needs a number. Render the mesh outline from the input view and compute IoU against the cleaned sketch mask.

1. It compares model choices in `EXPERIMENTS.md`, in place of the CV score from the playbook.
2. Best-of-N. Generate N images with different seeds, reconstruct each, keep the highest IoU. Measure the extra runtime.
3. Twelve fixed test sketches so every change is compared on the same inputs.

The Blender add-on is the second angle. Only start it when the core path, UI and docs work.

## Timeline and work split

Full detail per person in `docs/tasks/`. Every session starts and ends with the sync routine in `docs/tasks/README.md`.

| By | Milestone |
| --- | --- |
| 16:00 | Kickoff PR merged (deps, contracts, tasks). Everyone pulls |
| 16:45 | Pod up and all three can SSH in (Udit) |
| 17:30 | TripoSR gives a `.glb` from a hand-picked image (Swayam). `prepare_sketch` merged (Udit). 12 test sketches in the repo (Disha) |
| 19:00 | SD stage works on the pod (Udit). UI runs on the stub client (Disha). Cutout, export and validate merged (Swayam) |
| 20:00 | Full chain via CLI on the pod. API answering |
| 21:00 | Eval harness scores the test set. First README pass |
| 23:00 | Hosted URL on Modal. UI talks to the real API |
| 23:00 to 04:00 | Quality loop on the test set. Blender add-on v0 by 03:00 if the core is green |
| 08:00 | Code freeze. Only bug fixes and docs |
| 09:00 | Demo video recorded |
| 09:30 | Fresh clone on Windows and Mac, README only, timed |
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

1. Organiser reply to the message that was sent (submission method, slides and video, credentials, judge GPU). Judging duration is already known unofficially.
2. Whether CPU generation time is acceptable at the default settings. Decide after Udit's CPU run.
3. Whether a UV texture bake is worth trying after the core works (D24).
