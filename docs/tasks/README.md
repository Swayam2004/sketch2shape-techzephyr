# Work distribution

Written Sat 31 Oct 15:45 IST. Design is settled, so this is build time. Read this file, then your own file.

- Swayam, `docs/tasks/swayam.md`
- Disha, `docs/tasks/disha.md`
- Udit, `docs/tasks/udit.md`

## The pipeline in one line

```
sketch + prompt -> preprocess -> SD1.5 + ControlNet scribble -> rembg cutout -> TripoSR -> cleanup and validate -> .glb and .obj
```

One pipeline and one set of default settings on every device. Only the device changes (`cuda` or `cpu`). Results stay the same across the hosted link and local runs, apart from tiny numeric differences. Contracts are in `src/sketch2shape/types.py` and `docs/api.md`.

## First thing in every chat, last thing in every chat

Run this routine before any new work, and again before you end the session. A hook runs `scripts/sync_check.py` when a session starts, so the report is already in your context. Act on it.

1. `git fetch origin`. Read the "ACTION REQUIRED" part of the sync report.
2. Commit or stash your own uncommitted work.
3. On `main`, run `git pull --ff-only`. On a feature branch, run `git rebase origin/main`.
4. If conflicts appear, resolve them yourself using the `resolving-merge-conflicts` skill. Keep both sides' intent. Run the tests. If you cannot tell whose intent should win, stop and ask the file's owner.
5. If `pyproject.toml` or `uv.lock` changed, run `uv sync`.
6. Read what changed (`git log --oneline ORIG_HEAD..HEAD` and `git diff --stat ORIG_HEAD..HEAD`), `STATUS.md` and any open PRs (`gh pr list`). Check the changes do not break your assumptions.
7. Run `uv run pytest` and `uv run ruff check .`. Fix anything your merge broke before you add new work.
8. Now start. At the end, repeat steps 1 to 7, push, and update `STATUS.md`, `EXPERIMENTS.md`, `AI_USAGE.md` and `REPORT.md`.

## How the work fits together

```
Swayam S1 deps ........ done in the kickoff PR
Udit   U0 RunPod pod ........................ unlocks GPU work for everyone
Swayam S2 TripoSR on CPU -> S3 cutout + export -> S4 pipeline -> S5 API -> S6 pod run -> S7 Modal
Udit   U2 preprocess -> U3 SD stage ---------^                         eval U4 -> Blender U6
Disha  D1 test sketches -> D2 UI on stub client -> D3 README + report facts -> D4 slides, video
```

Handoffs

| From | To | What | Target |
| --- | --- | --- | --- |
| Swayam | everyone | Kickoff PR with deps, types, API contract, tasks | 16:00 |
| Udit | everyone | Pod IP and port in `STATUS.md` | 16:45 |
| Disha | Udit and Swayam | 12 test sketches in `samples/sketches/` | 17:30 |
| Udit | Swayam | `prepare_sketch` and `sketch_to_image` merged | 19:00 |
| Swayam | Disha | API server answering on the pod | 20:00 |
| Swayam | everyone | First hosted URL | 23:00 |

## Milestones

| By | Milestone |
| --- | --- |
| 16:45 | Pod up, all three can SSH in. Kickoff PR merged |
| 17:30 | TripoSR on a hand-picked image gives a `.glb` that opens in Blender (Swayam, CPU is fine). `prepare_sketch` merged (Udit). 12 test sketches in the repo (Disha) |
| 19:00 | SD stage works on the pod (Udit). UI runs on the stub client (Disha). Cutout, export and validate merged (Swayam) |
| 20:00 | `uv run sketch2shape generate` goes from sketch to `.glb` on the pod. API answers |
| 21:00 | Eval harness scores the test set (Udit). First README pass (Disha) |
| 23:00 | Hosted URL on Modal. UI talks to the real API |
| 23:00 to 04:00 | Quality loop. Blender add-on v0 by 03:00 if the core is green |
| 08:00 | Code freeze. Only bug fixes and docs |
| 09:00 | Demo video recorded |
| 09:30 | Fresh clone on Windows and Mac, README only, timed |
| 10:30 | Submission package complete, repo public |
| 11:00 | Submit |

If you are late on a milestone by more than 30 minutes, say so in `STATUS.md` under Blocked on. Do not wait silently.

## Rules every task follows

- Branch `feat/<name>-<thing>`. Open a PR. Swayam merges. Say "ship it" and your agent does the git steps.
- Tests for anything with logic (`uv run pytest`). Small ones. Use synthetic inputs, never downloaded weights, so they run on every laptop in seconds.
- No `print`, use `logging`. Type hints. No hard-coded paths.
- Log every model or quality run in `EXPERIMENTS.md` as a row, including failures.
- Append plain facts to `REPORT.md` and one row to `AI_USAGE.md` at the end of each session.
- No pre-existing code. Public libraries and models only, listed in the README table with source and licence.

## Paste this first

Each person pastes this into their agent at the start of the first session.

> Read AGENTS.md, CONTEXT.md, STATUS.md, PLAN.md, docs/tasks/README.md and docs/tasks/<yourname>.md. Run the sync routine from docs/tasks/README.md. Then tell me in five lines what you are going to do first and what you need from the others. Wait for my go.
