# STATUS

Live board. One row per person. Update it when you start, switch or stop work, and before you end an agent session. Newest information wins.

| Person | Doing now | Files or dirs touched | Blocked on | Updated |
| --- | --- | --- | --- | --- |
| Swayam | S6 done. Real pipeline ran twice on a RunPod GPU (IoU 0.953 and 0.943, EXPERIMENTS #8 and #9). Pod terminated, volume `s2s-weights` kept. Modal hosted demo dropped because the organisers accept localhost plus a 2 to 3 minute video. Next: wire best-of-N into `pipeline.py` once Udit sends the function, merge PRs | `weights.py`, `pipeline.py`, `api/`, `infra/` | Disha's 12 sketches, Udit's fp32 retry fix | Sun 1 Nov 03:45 |
| Disha (`sp4cefruity`) | Sketches (in progress, by hand). README rewritten with no hosted path, dashboard polish chosen over a Gradio app (PR to Swayam for `api/static/index.html`), then REPORT prose, Blender check and video script | `README.md`, `docs/`, `api/static/index.html` (PR) | First real GLB from the pod, Udit's add-on zip | Sun 1 Nov 04:10 |
| Udit (`ZenMaster192`) | U2 preprocess, U3 generate code and U4 eval written, 28 tests green, not committed yet. U0 pod not started | `preprocess/`, `generate/`, `eval/`, `scripts/eval_testset.py`, `scripts/preprocess_check.py` | U0 needs everyone's SSH public keys. U3 needs `download_weights.py`. U4 needs `pipeline.run` and Disha's sketches | 31 Oct, after 16:30 |

## Shared resources

| Resource | Owner | How to get in |
| --- | --- | --- |
| Dev GPU pod | Swayam | None running. RunPod volume `s2s-weights` (30 GB, EU-RO-1) holds weights and the repo. Ask Swayam to start a pod (about $0.72 per hour). |
| Hosted demo URL | none | Dropped. The organisers asked for a localhost run and a 2 to 3 minute video. |

## Heads-ups on shared files

Write one line here before you edit `pyproject.toml`, `uv.lock`, `AGENTS.md`, `CONTEXT.md`, `PLAN.md`, `src/sketch2shape/types.py` or `docs/api.md`.

- 31 Oct 16:00 Swayam. Kickoff PR adds all dependencies in one go. If you need another package, tell Swayam instead of running `uv add`, so `uv.lock` does not conflict.
- 31 Oct 16:30 Swayam. Writing rules (unslop) added to `AGENTS.md`, `CLAUDE.md` and the sync report. README rewritten. Pull before you edit those files.
- 31 Oct 16:50 Swayam. `pyproject.toml` gets a ruff exclude for `src/sketch2shape/vendor`. New shared helper `src/sketch2shape/weights.py` gives every stage the weights paths (`sd15_dir()`, `controlnet_scribble_dir()`, `rembg_home()`). Udit, load SD with `safety_checker=None`, the download skips that folder. Set `REMBG_HOME` to `rembg_home()` before creating the rembg session.
- 31 Oct 17:55 Swayam. Adding `papers/` to `.gitignore` so the research PDFs cannot be committed.
- 1 Nov 04:10 Disha. `AGENTS.md` line 123 and `CONTEXT.md` (tier 1 hosted link, D2, D6, D15, D20) and `PLAN.md` still describe a hosted demo. Swayam, please update them, I did not touch the shared files. `scripts/setup.sh` line 28 also says "use the hosted demo" (Udit's directory).
