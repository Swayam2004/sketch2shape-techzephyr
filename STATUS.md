# STATUS

Live board. One row per person. Update it when you start, switch or stop work, and before you end an agent session. Newest information wins.

| Person | Doing now | Files or dirs touched | Blocked on | Updated |
| --- | --- | --- | --- | --- |
| Swayam | Best-of-3 merged (#26) and measured: mean IoU 0.809 to 0.851 (EXPERIMENTS #14). Tuning pass found no better defaults (#15). Three demo meshes in `samples/meshes/`. fp32 retry warning now reaches `PipelineResult.warnings`. Pod `ttekoyf2ash8vg` terminated, volume `s2s-weights` kept. Warm-up now runs in the background with a ready flag (#28). Next: Disha's sketches through scripts/eval_testset.py when they land | `pipeline.py`, `generate/` (retry note only), `samples/`, `api/` | Disha's 12 sketches | Sun 1 Nov 09:15 |
| Disha (`sp4cefruity`) | Sketches (in progress, by hand). README merged (#17). Dashboard polish chosen over Gradio, PR #18 waits for Swayam (touches `api/server.py` static mount and `api/static/`), then REPORT prose, Blender check and video script | `README.md`, `docs/`, `api/static/index.html` (PR) | First real GLB from the pod, Udit's add-on zip | Sun 1 Nov 04:10 |
| Udit (`ZenMaster192`) | Task A done in PR `feat/udit-generate-fp16-fix`: fp32 retry frees the fp16 pipeline, VAE kept in fp32, opt-in `S2S_OFFLOAD=1`. Verified on CPU only. PR #21 best-of-N selection and PR #22 Blender add-on are open. Windows CPU run done. Next: run the 12 sketches when Disha pushes them | `generate/`, `tests/test_generate.py`, `EXPERIMENTS.md` | Swayam, a pod run for the fp16 VAE and offload checks (below). Disha's sketches | Sun 1 Nov 04:45 |

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
- 1 Nov 03:50 Swayam. Editing AGENTS.md (line 123), CONTEXT.md (glossary, D2, D3, D6, D7, D13, D15, D18, D20, new D25), PLAN.md (tiers, compute, timeline, checklist) and scripts/setup.sh to remove the hosted demo. Pull before you edit those.

## Requests

- 1 Nov 04:45 Udit to Swayam. I have no CUDA card. Please run the real sketch path on the pod and on your 1650 Ti, with `generate` from my PR branch `feat/udit-generate-fp16-fix`. Three runs, each logged as an EXPERIMENTS row with seconds and peak VRAM. 1) Default fp16 with the fp32 VAE. Is the black frame gone? 2) Same with `S2S_OFFLOAD=1`. 3) On the 1650 Ti, if the black frame stays, does the fp32 retry now fit in 4 GB? Also, `sketch_to_image` returns only an image, so its fp32 retry warning goes to the log and not to `PipelineResult.warnings`. Tell me if you want that surfaced.

- 1 Nov 05:35 Udit to Swayam. Windows CPU run done (EXPERIMENTS #9), no friction. Two findings for `pipeline.py`. 1) `CPU_WARNING` says the 3D step takes 20 to 40 s and generation takes longer. Generate took 263 s here, so a judge should be told about 5 minutes. Suggested text, "Running on CPU. Expect about 5 minutes per sketch." 2) `WeightsMissingError` in `reconstruct/triposr.py` does not say the download is about 7 GB. I added that to the generate stage message, which a fresh clone hits first.

- 1 Nov 05:10 Udit to Swayam. Best-of-N selection is written and tested in PR `feat/udit-best-of-n`. Proposed signature, nothing in `pipeline.py` changes until you agree. `eval.select_best_candidate(sketch_mask: np.ndarray, candidates: Sequence[PIL.Image]) -> Selection`. `candidates` are the RGBA outputs of `cutout.remove_background`, one per seed. `Selection.index` is the winner and `Selection.scores` is one 2D IoU per candidate. Both outlines are fitted to the same frame first, because the cutout recentres the object. Wiring for you in `pipeline.py` is roughly: N seeds from `request.seed`, then `generate`, `remove_background`, `select_best_candidate`, then `image_to_mesh` once on the winner. Open questions for you. N must be 4 on every device. On CPU the generate step alone took 278 s for one candidate (EXPERIMENTS #8), so four candidates is about 18 minutes there, past the 15 minute poll limit in `docs/api.md`. Options are N=4 on GPU and N=1 on CPU (breaks the same-default rule), or lower steps for all.

- 1 Nov 08:30 Swayam to Udit. Done: best-of-3 in `pipeline.py` with N=3 everywhere (`S2S_CANDIDATES` overrides), CPU warning now says about 15 minutes, weights error mentions 7 GB, fp32 retry note surfaced through `image.info` in `sketch_to_image.py` (small edit in your directory, tests added). Your three CUDA runs are covered by EXPERIMENTS #14: fp16 with fp32 VAE gave no black frames on the pod. Offload and the 1650 Ti runs are not done.

- 1 Nov 09:00 Swayam to Disha. One-line dashboard change in PR `feat/swayam-warmup-state`: `/v1/health` now has `ready`, and the header line in `index.html` adds "loading models, the first job waits" while it is false. `docs/api.md` health example updated. The server starts answering at once and loads models in the background.
