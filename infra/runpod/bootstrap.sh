#!/usr/bin/env bash
# Run on the RunPod pod after first login. Safe to rerun.
set -euo pipefail

WORK="${WORK:-/workspace}"
REPO_SSH="git@github.com:Swayam2004/sketch2shape-techzephyr.git"
REPO_DIR="$WORK/sketch2shape"
KEY="$WORK/.ssh/s2s_deploy"

mkdir -p "$WORK/.cache/huggingface" "$WORK/.cache/uv" "$WORK/.cache/rembg" "$WORK/.ssh"

# The pod's home directory is wiped on termination. Keep caches on the volume.
cat > "$WORK/s2s-env.sh" <<EOF
export HF_HOME="$WORK/.cache/huggingface"
export UV_CACHE_DIR="$WORK/.cache/uv"
export REMBG_HOME="$WORK/.cache/rembg"
export GIT_SSH_COMMAND="ssh -i $KEY -o StrictHostKeyChecking=accept-new"
EOF
grep -q "s2s-env.sh" ~/.bashrc 2>/dev/null || echo "source $WORK/s2s-env.sh" >> ~/.bashrc
# shellcheck disable=SC1090
source "$WORK/s2s-env.sh"

if ! command -v uv >/dev/null 2>&1; then
  python3 -m pip install --quiet uv
fi

if [ ! -f "$KEY" ]; then
  ssh-keygen -t ed25519 -N "" -f "$KEY" -C "runpod-s2s-deploy" >/dev/null
fi

if ! git ls-remote "$REPO_SSH" >/dev/null 2>&1; then
  echo
  echo "GitHub does not accept this pod yet. Ask Swayam to add this public key"
  echo "as a read-only deploy key (repo Settings, Deploy keys), then rerun this script."
  echo
  cat "$KEY.pub"
  exit 1
fi

if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" pull --ff-only
else
  git clone "$REPO_SSH" "$REPO_DIR"
fi

cd "$REPO_DIR"
uv python install 3.11
uv sync

nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo "Ready in $REPO_DIR. Open a new shell or run 'source $WORK/s2s-env.sh'."
