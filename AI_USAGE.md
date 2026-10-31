# AI usage

Every AI tool use goes here, by whoever did it.

| When | Who | Tool | What it did | What we did ourselves |
| --- | --- | --- | --- | --- |
| Before 12:00 31 Oct | Swayam | Claude (web) | Researched how winning hackathon teams work and wrote a general playbook. No code. | Chose which sources to read. |
| 12:00 to 15:00 31 Oct | Swayam | Claude Code | Read the problem statement, ran two research passes (model feasibility on our laptops, cloud GPU options), scaffolded the repo and drafted the planning and agent-context docs. | Answered every design question, chose the architecture, tiers and team split. |
| 15:00 to 16:00 31 Oct | Swayam | Claude Code | Ran two more research passes (model quality, long-window hosting), merged them, wrote the task split, API contract, shared types, sync script and hook, and added shared dependencies. | Chose TripoSR as the single model, chose Modal as primary host, approved the work split and start of build. |
| 16:00 to 16:30 31 Oct | Swayam | Claude Code | Added the writing rules to AGENTS.md and CLAUDE.md, a writing reminder in the sync report, and ran a scan-and-fix pass for AI-style text and stale references across the docs. Rewrote README.md for the one-pipeline design. | Asked for the rule and the pass. |

| 16:30 to 16:50 31 Oct | Swayam | Claude Code | Ran the sync routine and did task S2. Vendored TripoSR, swapped `torchmcubes` for scikit-image marching cubes, patched the checkpoint loader for transformers 5, wrote `image_to_mesh`, `weights.py` and `scripts/download_weights.py`, added tests, ran the chair on CPU and logged timings. | Chose to keep the CPU resolution at 192 after seeing the 256 timing, and decided what goes in the commit. |
