# STATUS

Live board. One row per person. Update it when you start, switch or stop work, and before you end an agent session. Newest information wins.

| Person | Doing now | Files or dirs touched | Blocked on | Updated |
| --- | --- | --- | --- | --- |
| Swayam | S4 pipeline and CLI in PR, runs end to end with a stub for Udit's stages. Next S5 FastAPI | `pipeline.py`, `cli.py`, `reconstruct/`, `cutout/`, `export/` | Blender check of the chair GLB, PR #5 merge so the stub can go | Sun 1 Nov 00:20 |
| Disha (`sp4cefruity`) | D0 SSH key, D1 twelve test sketches | `samples/sketches/` | Nothing | - |
| Udit (`ZenMaster192`) | U2 preprocess, U3 generate code and U4 eval written, 28 tests green, not committed yet. U0 pod not started | `preprocess/`, `generate/`, `eval/`, `scripts/eval_testset.py`, `scripts/preprocess_check.py` | U0 needs everyone's SSH public keys. U3 needs `download_weights.py`. U4 needs `pipeline.run` and Disha's sketches | 31 Oct, after 16:30 |

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
