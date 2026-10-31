# AI usage

Every AI tool use goes here, by whoever did it.

| When | Who | Tool | What it did | What we did ourselves |
| --- | --- | --- | --- | --- |
| Before 12:00 31 Oct | Swayam | Claude (web) | Researched how winning hackathon teams work and wrote a general playbook. No code. | Chose which sources to read. |
| 12:00 to 15:00 31 Oct | Swayam | Claude Code | Read the problem statement, ran two research passes (model feasibility on our laptops, cloud GPU options), scaffolded the repo and drafted the planning and agent-context docs. | Answered every design question, chose the architecture, tiers and team split. |
| 15:00 to 16:00 31 Oct | Swayam | Claude Code | Ran two more research passes (model quality, long-window hosting), merged them, wrote the task split, API contract, shared types, sync script and hook, and added shared dependencies. | Chose TripoSR as the single model, chose Modal as primary host, approved the work split and start of build. |
| 16:00 to 16:30 31 Oct | Swayam | Claude Code | Added the writing rules to AGENTS.md and CLAUDE.md, a writing reminder in the sync report, and ran a scan-and-fix pass for AI-style text and stale references across the docs. Rewrote README.md for the one-pipeline design. | Asked for the rule and the pass. |
| 31 Oct, after 16:30 | Udit | Claude Code | Wrote the preprocessing stage (adaptive threshold, hull fallback, `prepare_sketch` to the shared contract), the silhouette IoU module, the Stable Diffusion plus ControlNet stage, the test-set eval script and the contact sheet script, with 28 tests. | Chose the U-task scope, decided what to commit and when, and will run the GPU stage on the pod. |

