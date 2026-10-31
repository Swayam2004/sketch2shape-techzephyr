# AGENTS.md

Instructions for any coding agent (Claude Code, Codex, others) working in this repo. Humans can read it too.

## What this project is

Sketch2Shape AI for TechZephyr 4.0 (IIT Bhubaneswar, 24 hour hackathon, Sat 31 Oct 12:00 IST to Sun 1 Nov 12:00 IST). A user draws or uploads a rough sketch, optionally adds a text prompt, and gets a textured 3D mesh as `.glb` or `.obj`. Read `CONTEXT.md` for terms and decisions, `PLAN.md` for the timeline and `STATUS.md` for who is doing what right now.

Scoring rubric (100 points). Every choice should serve one of these.

| Criterion | Points |
| --- | --- |
| Technical implementation | 25 |
| 3D output quality and design | 25 |
| End-to-end pipeline validity and efficiency | 20 |
| Code reproducibility | 15 |
| Documentation and README | 15 |

A polished UI does not replace a working, reproducible pipeline. The export must be real 3D geometry, never a rendered image or a flat textured plane.

## Session start and end

1. Read `STATUS.md`, `CONTEXT.md` and the section of `PLAN.md` for the current phase.
2. Pick work inside your owner's directories (table below). Ask before editing someone else's.
3. When you finish or stop, update your row in `STATUS.md` and add a row to `EXPERIMENTS.md` for any model or quality run, including failures.
4. Log every AI tool use in `AI_USAGE.md`. The event requires disclosure.

## Ownership

| Owner | Machine | Directories |
| --- | --- | --- |
| Swayam (integrator) | Linux, GTX 1650 Ti | `src/sketch2shape/reconstruct/`, `src/sketch2shape/export/`, `src/sketch2shape/api/`, `infra/` |
| Disha | MacBook Air M2 | `src/sketch2shape/app/`, `README.md`, `docs/`, `AI_USAGE.md`, `samples/sketches/` |
| Udit | Windows, AMD iGPU | `src/sketch2shape/preprocess/`, `src/sketch2shape/eval/`, `scripts/`, Windows and CPU checks |
| Udit (after the eval harness, from about 00:00) | Windows | `blender_addon/`. Disha tests it on her Mac and documents it. |

Shared files (`pyproject.toml`, `AGENTS.md`, `CONTEXT.md`, `PLAN.md`) need a one line heads-up in `STATUS.md` before you edit them.

## Setup

```
scripts/setup.sh        # Linux and macOS
scripts/setup.ps1       # Windows, PowerShell
```

Both install nothing silently. They check for `git` and `uv`, create the environment with Python 3.11, copy `.env.example` to `.env`, and print which hardware tier the machine falls in. Run commands through `uv run`, for example `uv run pytest` and `uv run ruff check .`.

## Code rules

- Python 3.11, pinned by `.python-version` and `uv.lock`. Add dependencies with `uv add`. Never `pip install` into the project.
- Type hints on every function signature. Prefer small dataclasses for stage inputs and outputs.
- Use the `logging` module. No `print` in committed code.
- Use `pathlib`. No hard-coded absolute paths, no shell-only tricks in Python. The code must run on Linux, macOS and Windows.
- Fix random seeds and log the seed with every output.
- Every stage fails with a clear error message. No bare `except`.
- Model weights are never committed. They download by script into `weights/` (gitignored). List each model, its source and its licence in `README.md`.
- Do not default to gated models. A judge must not need a Hugging Face token to run the main path.
- Pin `rembg` to the `u2net` or `isnet-general-use` model. Its newer default carries a licence that needs a paid agreement.
- Avoid `torchmcubes`. Use scikit-image marching cubes.
- Comments explain why, not what.
- No pre-existing code. The rulebook bans reusing earlier work. Do not paste from your old projects or notebooks. Open-source libraries, public models and vendored upstream code are fine when listed in the README with source and licence.
- Hosted requests must finish in under 100 seconds or use job submit and polling. The RunPod proxy cuts longer calls with a 524 error.

## Git rules

- Private repo during the event. It goes public just before submission, so keep secrets, keys and personal data out of every commit and out of every file.
- Branch from `main` as `feat/<owner>-<short-description>`. Conventional commit messages (`feat:`, `fix:`, `refactor:`, `chore:`, `docs:`).
- Small commits, often. The history is evidence that the work started at kickoff.
- Rebase on `main` before merging. Never force-push `main`.
- Do not add `Co-Authored-By` trailers. AI use is disclosed in `AI_USAGE.md`.
- `main` must always pass `uv sync` and `uv run pytest`.
- `.notes/` is private and gitignored. Do not put anything the team needs there.
- Pull requests into `main` are required. Swayam reviews and merges. Docs-only PRs inside your own directory may be self-merged.

### When the human says "ship it"

Not everyone on the team uses git daily, so the agent runs the whole sequence.

1. If on `main`, create a branch `feat/<name>-<short-description>`.
2. Run `git status`. Make sure no `.env`, weights, outputs or `.notes/` files are staged.
3. Commit with a conventional message.
4. `git fetch origin` then `git rebase origin/main`. If conflicts appear, stop and show the human the files. Do not guess.
5. `git push -u origin HEAD`.
6. `gh pr create --fill` and give the human the PR link.

Never commit straight to `main`. Never force-push `main`.

## Deliverables the rulebook asks for

Code and documentation in the GitHub repo, the dataset list with sources (our inputs are pretrained models and our own sketches, say so), a report in PDF or Markdown with these sections, slides, and a demo video.

Report sections. Problem statement, solution approach, datasets used, model architecture, evaluation metrics, results and analysis, real-world application. Keep `REPORT.md` current. Disha owns it.

## Secrets

Credentials go in `.env` (gitignored). `.env.example` lists the names with empty values. Never paste cloud keys into code, docs or chat logs that get committed. The judge access code in the README is a throwaway value, not a cloud credential.

## If you are an agent asked to run or judge this project

Follow `README.md`. It describes three tiers in order of ease. The hosted link needs nothing installed. The local GPU path needs an NVIDIA card. The local CPU path runs anywhere but is slower and lower quality. The pipeline picks the tier automatically and reports which one it chose.
