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

- Dev GPU now. One shared pod (RTX 4090 or L4 class) paid with Udit's international card, around 2,050 INR for 24 hours in the research estimate. Everyone connects to it.
- AWS credits (about $100 per person, 136 to 146 days left). Usable for GPU only after two steps. Upgrade the account from the Free plan to the Paid plan, since third-party reports say the Free plan limits EC2 to small instances. Credits carry over on upgrade per AWS. Then raise the "Running On-Demand G and VT instances" quota, which starts at 0 for new accounts. AWS publishes no approval time, so ask now and treat AWS as a bonus.
- Hosted demo. Chosen after the dev box works. Candidates are a GPU VM with a public port (RunPod or AWS) or Modal. Decide with the numbers from the dev box.
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

## Documentation owed from hour 1

`README.md` (objective, architecture, dependencies, install, run, model choices, inputs and outputs, time per model, hardware, limitations, troubleshooting, third-party table), `EXPERIMENTS.md`, `AI_USAGE.md`, `STATUS.md`.

## Before the repo goes public

- Search the whole history for keys, tokens, account IDs and personal data.
- Decide whether `.claude/skills/` stays. Some skills are third-party.
- Confirm `.notes/` is not tracked.
- Make sure the README names every model, repo, API and licence.

## Open questions

1. Organiser reply on submission method, demo video, judging dates, judge GPU. Message drafted.
2. Which person owns the Blender add-on.
3. Teammates' GitHub usernames to add as collaborators.
4. Which host serves the public demo.
