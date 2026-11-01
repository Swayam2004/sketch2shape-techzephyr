# CONTEXT.md

Terms and decisions. Keep it short. Add a decision when the team settles one.

## Glossary

| Term | Meaning |
| --- | --- |
| Sketch | The user's rough 2D drawing, from the in-app canvas or an uploaded image. |
| Prompt | Optional text describing material, colour or style. Never required. |
| Stage | One step of the pipeline. Each stage has a typed input and output (`src/sketch2shape/types.py`). |
| Pipeline | preprocess, sketch-to-image, cutout, image-to-3D, mesh cleanup, validate, export. |
| Scribble map | The cleaned sketch as white lines on black. ControlNet conditioning. |
| Device | Where the heavy stages run. `cuda` (NVIDIA) or `cpu`. Auto-detected, overridable with `S2S_BACKEND`. |
| Tier | How a judge reaches the pipeline. Tier 1 local run with an NVIDIA GPU. Tier 2 local run on CPU. Both run the same pipeline and settings. The hosted tier was dropped (D25). |
| Silhouette IoU | Orthographic front view of the mesh, compared to the cleaned sketch mask. Our fidelity number. |
| Test set | 12 fixed sketches in `samples/sketches/` used to compare every change. |
| Demo video | A 2 to 3 minute recording that shows a localhost run and explains the architecture. It replaces the hosted demo (D25). |
| Sync routine | The check-and-pull steps every agent runs at the start and end of each session. See `docs/tasks/README.md`. |

## Decisions

| # | Decision | Why |
| --- | --- | --- |
| D1 | Judges use the 100 point rubric from the problem statement. No presentation round, teams submit and leave. | Confirmed by the team. |
| D2 | Optimise for low judge friction. Superseded by D25: local run first, demo video second. | Judges' hardware is unknown. |
| D3 | Two tiers, one pipeline (was three before D25). A local run auto-detects an NVIDIA GPU and uses it. Without one it runs on CPU, slower, and the UI warns about it. Same models and same default settings everywhere. D25 removed the hosted tier, so two tiers remain. | Reproducibility is 15 points, and results must match between machines. Supersedes the earlier "lite mode" idea. |
| D4 | API-first. A FastAPI service owns the pipeline. Gradio and the Blender add-on are clients. Contract in `docs/api.md`. | One implementation serves the UI, the CLI and Blender. |
| D5 | Blender add-on is in scope for this hackathon, not future work. | Novelty that few submissions will have. Core reliability still comes first. |
| D6 | Superseded by D25. The UI is the dashboard served by `sketch2shape serve`, with in-app sketching and an asset viewer. | Matches the problem statement. One less dependency than Gradio. |
| D7 | Extra cash cap is about 1,500 to 2,000 INR combined. Swayam's account pays for the RunPod dev pod. Modal is not used (D25). | Team budget. |
| D8 | Python 3.11 with uv on all three OSes. | Same environment everywhere. |
| D9 | `rembg` pinned to `isnet-general-use`. No gated models. Scikit-image marching cubes instead of `torchmcubes`. TripoSR is vendored, not installed from PyPI. | Licence safety, no tokens for judges, fewer build failures. See `docs/research/backend-feasibility.md`. |
| D10 | Repo is private until just before submission, then public. | Other teams could copy our work. |
| D11 | Everything starts from this repo. No pre-existing code. Every AI tool use is logged in `AI_USAGE.md`. | Event rule. |
| D12 | Three rubrics exist. The problem statement's 100 points is the confirmed one. The brochure and the rulebook each list a different 50/20/15/15 split led by Technical Accuracy. We optimise for the confirmed one and cover the others with failure logs, a measured accuracy number (silhouette IoU), a report and slides. | Cheap hedge. Technical accuracy is the tie-breaker. |
| D13 | Deliverables. Repo with README, `REPORT.md`, `EXPERIMENTS.md`, `AI_USAGE.md`, slides, demo video, sample `.glb` files with inputs. The brochure says to submit "all required credentials", so a throwaway access code for the local server goes in the README, never a real cloud key. | Rulebook sections 6 and 9, brochure ML page. |
| D14 | Dev GPU is a shared RunPod Secure Cloud pod, an L4 first, with a 30 GB network volume, paid by Swayam. See `docs/guides/runpod-dev-gpu.md`. | DevOps is the biggest bottleneck. |
| D15 | Superseded by D25, nothing is hosted. Old text. Demo host priority. Modal first (scale to zero, about 270 to 500 INR for 200 runs, inside the free credit). Then a free ZeroGPU Space plus a static page with sample `.glb` files. Last resort a paid HF T4 Space (about 1,890 INR). AWS credits stay optional (`docs/guides/aws-gpu-optional.md`). | Judging lasts 5 to 6 days, so an always-on GPU is too expensive. See `docs/research/long-window-hosting.md`. |
| D16 | Blender add-on owned by Udit from about 00:00, tested by Disha. | Udit works best overnight. |
| D17 | Pull requests into `main`, enforced by a repo ruleset with zero required approvals. Swayam merges. Agents run the git steps when a teammate says "ship it". | Strict but low friction. |
| D18 | One image-to-3D model everywhere. TripoSR (MIT, no gating, runs on CPU and GPU). Hunyuan3D, TripoSG, Stable Fast 3D and TRELLIS are not used. | Results must match across machines, and installs must stay easy. Hunyuan would have given higher quality but needs a compiled CUDA extension, Python 3.10 and a GPU. See `docs/research/model-quality.md`. |
| D19 | Living `REPORT.md`. Agents append facts each session, Disha does the final pass. `AI_USAGE.md` is written by agents at the end of every session. Disha owns README, report, slides, video, UI and the test set. | Report must read as genuine without loading Disha. |
| D20 | Judging is expected to take 5 to 6 days after the deadline (unofficial). Nothing needs to stay online, because judges run the project locally (D25). | Heard from an organising committee contact. |
| D21 | Benchmark directly on the pod, not on public HF Spaces. | Faster iteration. Spaces quota is 2 to 5 GPU minutes a day. |
| D22 | Every HF account (Swayam, Udit, Disha) is older than 30 days, so each can host a ZeroGPU Space. | Account ages checked by the team. |
| D23 | Build phase starts Sat 31 Oct about 15:45. Task split is in `docs/tasks/`. Every session starts and ends with the sync routine. | Three laptops work in parallel without stepping on each other. |
| D24 | TripoSR output uses vertex colours, not a baked texture, until a bake is shown to work in Blender. | `--bake-texture` has open bugs, and a broken GLB is worse than a plain one. |
| D25 | No hosted demo. Judges run the project on localhost, and the team submits a 2 to 3 minute video that shows a run and explains the architecture. Modal, ZeroGPU and the always-on host are dropped. | The organisers answered a question about external GPUs: "you can just run a localhost and to explain the pipeline just upload a demo video of 2-3 minutes". Received 1 Nov 2026 around 03:00. |

## Constraints worth remembering

- Dev machines cannot run TripoSR on GPU. Linux has a GTX 1650 Ti with 4 GB, Windows has an AMD iGPU (CPU only for PyTorch), Mac is M2 with 16 GB. The shared pod covers GPU runs.
- TripoSR needs about 6 GB VRAM by default.
- Hosted proxies cut HTTP calls at 100 to 150 seconds, so the API uses job polling.
- Plain `torch` from PyPI is a CUDA build on Linux and a CPU build on Windows. A Windows judge with an NVIDIA card runs on CPU unless they use the CUDA index. Document it.
- Hidden geometry is guessed. Aim for plausible, not exact.
- README must report time to generate a model, hardware used and limitations.

## Open questions

See the bottom of `PLAN.md`.
