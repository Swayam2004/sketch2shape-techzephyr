# Windows PowerShell setup. Installs nothing silently.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

function Require-Command($name, $hint) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Error "Missing '$name'. $hint"
    }
}

Require-Command git "Install Git for Windows first."
Require-Command uv "Install uv from https://docs.astral.sh/uv/getting-started/installation/ then rerun this script."

uv python install 3.11
uv sync

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example. Fill in values only if you need them."
}

if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    Write-Host "NVIDIA GPU found. TripoSR needs about 6 GB of VRAM."
} else {
    Write-Host "CPU only. The pipeline still runs, but each model takes longer. Use a machine with an NVIDIA GPU for faster runs."
}

Write-Host "Done. Next, read AGENTS.md, CONTEXT.md and STATUS.md, then start 'claude' in this folder."
