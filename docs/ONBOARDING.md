# Onboarding for teammates

Goal. Everyone works in parallel on their own laptop, each with their own Claude Code session, against one private GitHub repo.

## 1. Prerequisites

- Git, plus the GitHub CLI (`gh`). Run `gh auth login`.
- `uv` (https://docs.astral.sh/uv/getting-started/installation/).
- Claude Code, already installed on your laptop.
- Windows only. Install WSL2 later if you can. The native Windows run through uv is the important one, because it behaves like a judge's laptop.

## 2. Get the code

Swayam adds you to the private repo. Accept the invite, then

```
gh repo clone Swayam2004/sketch2shape-techzephyr
cd sketch2shape-techzephyr
```

## 3. Run setup

macOS or Linux

```
bash scripts/setup.sh
```

Windows PowerShell

```
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```

The script creates the Python 3.11 environment, copies `.env.example` to `.env` and prints your hardware tier. It installs nothing without telling you. If `uv` is missing it stops and says so.

## 4. Start your agent

Open `claude` in the repo folder. Project skills in `.claude/skills/` load by themselves, and a hook prints the repo sync report when the session starts. First prompt, with your own name

> Read AGENTS.md, CONTEXT.md, STATUS.md, PLAN.md, docs/tasks/README.md and docs/tasks/<yourname>.md. Run the sync routine from docs/tasks/README.md. Then tell me in five lines what you are going to do first and what you need from the others. Wait for my go.

## 5. Work loop

1. Update your row in `STATUS.md`.
2. Ask your agent to do the work.
3. When you are happy, tell your agent `ship it`. It makes a branch, commits, rebases on `main`, pushes and opens a pull request. You never need to type git commands. Send Swayam the PR link.
4. Log every AI use in `AI_USAGE.md`. Log every model run in `EXPERIMENTS.md`.
5. Swayam merges. Direct pushes to `main` are blocked on purpose.

For the shared GPU, see `docs/guides/runpod-dev-gpu.md`. First generate an SSH key (`ssh-keygen -t ed25519`) and send Udit the `.pub` file.

## 6. Do not

- Commit `.env`, keys, weights or anything from `.notes/`.
- Edit files in another person's directories without a note in `STATUS.md`.
- Paste cloud credentials into prompts or docs.
