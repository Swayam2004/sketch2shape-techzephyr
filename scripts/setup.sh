#!/usr/bin/env bash
# Linux and macOS setup. Installs nothing silently.
set -euo pipefail
cd "$(dirname "$0")/.."

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing '$1'. $2" >&2
    exit 1
  fi
}

need git "Install git first."
need uv "Install uv from https://docs.astral.sh/uv/getting-started/installation/ then rerun this script."

uv python install 3.11
uv sync

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Fill in values only if you need them."
fi

if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
  vram=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)
  echo "NVIDIA GPU found (${vram} MiB VRAM). TripoSR needs about 6 GB, so a smaller card falls back to CPU."
else
  echo "CPU only. The pipeline still runs, but each model takes longer. Use a machine with an NVIDIA GPU for faster runs."
fi

echo "Done. Next, read README.md, then run 'uv run sketch2shape serve'."
