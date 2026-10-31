# STATUS

Live board. One row per person. Update it when you start, switch or stop work, and before you end an agent session. Newest information wins.

| Person | Doing now | Files or dirs touched | Blocked on | Updated |
| --- | --- | --- | --- | --- |
| Swayam | S2 TripoSR on CPU, kickoff PR | `reconstruct/`, `scripts/download_weights.py`, `pyproject.toml` | Nothing | Sat 31 Oct 16:00 |
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
