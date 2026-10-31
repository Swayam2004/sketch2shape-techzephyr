# STATUS

Live board. One row per person. Update it when you start, switch or stop work, and before you end an agent session. Newest information wins.

| Person | Doing now | Files or dirs touched | Blocked on | Updated |
| --- | --- | --- | --- | --- |
| Swayam | S2 done on branch `feat/swayam-triposr-cpu`, not pushed yet. Next S3 cutout, export, validate | `reconstruct/`, `vendor/tsr/`, `weights.py`, `scripts/download_weights.py`, `pyproject.toml` | Blender check of the GLB (no Blender on this machine) | Sat 31 Oct 16:50 |
| Disha (`sp4cefruity`) | D0 SSH key, D1 twelve test sketches | `samples/sketches/` | Nothing | - |
| Udit (`ZenMaster192`) | U0 RunPod pod, then U2 preprocessing | RunPod account, `preprocess/` | Needs everyone's SSH public keys | - |

## Shared resources

| Resource | Owner | How to get in |
| --- | --- | --- |
| Dev GPU pod `s2s-dev` | Udit | Not created yet. See `docs/guides/runpod-dev-gpu.md`. Pod IP and port will be posted here. |
| Hosted demo URL | Swayam | Not created yet |

## Heads-ups on shared files

Write one line here before you edit `pyproject.toml`, `uv.lock`, `AGENTS.md`, `CONTEXT.md`, `PLAN.md`, `src/sketch2shape/types.py` or `docs/api.md`.

- 31 Oct 16:00 Swayam. Kickoff PR adds all dependencies in one go. If you need another package, tell Swayam instead of running `uv add`, so `uv.lock` does not conflict.
- 31 Oct 16:30 Swayam. Writing rules (unslop) added to `AGENTS.md`, `CLAUDE.md` and the sync report. README rewritten. Pull before you edit those files.
- 31 Oct 16:50 Swayam. `pyproject.toml` gets a ruff exclude for `src/sketch2shape/vendor`. New shared helper `src/sketch2shape/weights.py` gives every stage the weights paths (`sd15_dir()`, `controlnet_scribble_dir()`, `rembg_home()`). Udit, load SD with `safety_checker=None`, the download skips that folder. Set `REMBG_HOME` to `rembg_home()` before creating the rembg session.
