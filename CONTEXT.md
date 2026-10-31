# CONTEXT.md

Terms and decisions. Keep it short. Add a decision when the team settles one.

## Glossary

| Term | Meaning |
| --- | --- |
| Sketch | The user's rough 2D drawing, from the in-app canvas or an uploaded image. |
| Prompt | Optional text describing material, colour or style. Never required. |
| Stage | One step of the pipeline. Each stage has a typed input and output so models can be swapped. |
| Pipeline | preprocess, sketch-to-image, cutout, image-to-3D, mesh cleanup, validate, export. |
| Scribble map | The cleaned, binarised sketch used as ControlNet conditioning. |
| Backend | Where heavy stages run. `cuda` (local NVIDIA), `cpu` (local, slow), `remote` (our hosted GPU API). |
| Tier | What a judge can use. Tier 1 hosted link. Tier 2 local NVIDIA GPU. Tier 3 local CPU lite mode. |
| Lite mode | CPU-friendly path. Skips the SD stage or uses a few-step variant. Lower quality, still produces a valid `.glb`. |
| Silhouette IoU | Render the mesh from the input view, compare its outline to the cleaned sketch mask. Our fidelity number. |
| Test set | 12 fixed sketches in `samples/sketches/` used to compare every change. |
| Hosted demo | Our public GPU-backed web app for judges. Has a queue, rate limit and a throwaway access code. |

## Decisions

| # | Decision | Why |
| --- | --- | --- |
| D1 | Judges use the 100 point rubric from the problem statement. No presentation round, teams submit and leave. | Confirmed by the team. |
| D2 | Optimise for low judge friction. Hosted link first, local second. | Judges' hardware is unknown. A link needs no setup. |
| D3 | Three tiers. Auto-detect NVIDIA GPU and use it. Otherwise run CPU and warn that results are slower and slightly less accurate. Tier 3 is mandatory. | Reproducibility is 15 points and must work with no GPU and no network access to our link. |
| D4 | API-first. A FastAPI service owns the pipeline. Gradio and the Blender add-on are clients. | One implementation serves the UI, the CLI and Blender. |
| D5 | Blender add-on is in scope for this hackathon, not future work. | Novelty that few submissions will have, Blender is open source and popular. Core pipeline reliability still comes first. |
| D6 | Hosted demo runs a Gradio app with in-app sketching, asset viewer and all processing. Shutdown date is announced but extendable in the backend. | Matches the problem statement and keeps judging easy. |
| D7 | Cloud GPU. Udit's card (international payments) gives an instant GPU. AWS credits (about $100 per person) are a second source once the account upgrade and GPU quota request go through. Extra spend cap is about 1,500 to 2,000 INR combined. | See `docs/research/cloud-gpu-options.md`. |
| D8 | Python 3.11 with uv on all three OSes. | Same environment on every laptop and on judges' machines. |
| D9 | `rembg` pinned to a permissive model. No gated models by default. Scikit-image marching cubes instead of `torchmcubes`. | Licence safety, no tokens for judges, fewer build failures. See `docs/research/backend-feasibility.md`. |
| D10 | Repo is private until just before submission, then public. | Other teams could copy our work. |
| D11 | Everything starts from this repo. No pre-existing code. Every AI tool use is logged in `AI_USAGE.md`. | Event rule. |

## Constraints worth remembering

- Dev machines have no usable GPU for the full pipeline. Linux has a GTX 1650 Ti with 4 GB, Windows has an AMD iGPU (CPU only for PyTorch), Mac is M2 with 16 GB.
- TripoSR needs about 6 GB VRAM by default. Larger models (Hunyuan3D, TRELLIS) are remote only.
- Hidden geometry is guessed. Aim for plausible, not exact.
- README must report time to generate a model, hardware used and limitations.

## Open questions

See the bottom of `PLAN.md`.
