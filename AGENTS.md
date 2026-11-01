# AGENTS.md

Notes for coding agents and for anyone reading the repo cold.

## What this project is

Sketch2Shape AI for TechZephyr 4.0 (IIT Bhubaneswar, 24 hour hackathon, 31 Oct to 1 Nov 2026). A user draws or uploads a rough sketch, optionally adds a text prompt, and gets a textured 3D mesh as `.glb` or `.obj`. `README.md` explains the pipeline and how to run it. `CONTEXT.md` lists terms and design decisions. `DATASETS.md` lists the data. `EXPERIMENTS.md` logs every model run, including failures. `AI_USAGE.md` discloses where AI tools helped.

Stage functions and types are fixed in `src/sketch2shape/types.py`. The HTTP API is in `docs/api.md`.

## Setup

```
scripts/setup.sh        # Linux and macOS
scripts/setup.ps1       # Windows, PowerShell
```

Both scripts check for `git` and `uv`, create the environment with Python 3.11, copy `.env.example` to `.env` and print which hardware tier the machine falls in. Run commands through `uv run`, for example `uv run pytest` and `uv run ruff check .`.

## Code rules

- Python 3.11, pinned by `.python-version` and `uv.lock`. Add dependencies with `uv add`, never `pip install` into the project.
- Type hints on every function signature. Small dataclasses for stage inputs and outputs.
- Use the `logging` module. No `print` in committed code.
- Use `pathlib`. No hard-coded absolute paths. The code runs on Linux, macOS and Windows.
- Fix random seeds and log the seed with every output.
- Every stage fails with a clear error message. No bare `except`.
- Model weights are never committed. `scripts/download_weights.py` fetches them into `weights/`, which git ignores.
- Do not default to gated models. The main path needs no Hugging Face token.
- Pin `rembg` to the `isnet-general-use` model. Its newer default carries a licence that needs a paid agreement.
- Avoid `torchmcubes`. Use scikit-image marching cubes.
- Comments explain why, not what.
- API requests finish in under 100 seconds or use job submit and polling.

## Writing rules

Prose in this repo avoids AI tells. No em dashes, en dashes or curly quotes. Use a period or a comma. Colons only before a list or an example. Sentence case headings. Plain words, active voice, no chatbot filler.

## Git rules

- Branch as `feat/<owner>-<short-description>`. Conventional commit messages.
- Pull requests into `main` are required. Never force-push `main`.
- `main` always passes `uv sync` and `uv run pytest`.
- Keep `.env`, weights and outputs out of commits.

## If you are an agent asked to run or judge this project

Follow `README.md`. It describes three ways to run the project. The local GPU path needs an NVIDIA card. The local CPU path runs anywhere and takes longer. Both run the same pipeline with the same default settings. There is no hosted demo, so the demo video shows a run on a GPU. The pipeline picks the device itself and reports which one it chose.
