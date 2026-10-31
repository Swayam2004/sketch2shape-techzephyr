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
    Write-Host "Hardware tier 2 (NVIDIA GPU found)."
} else {
    Write-Host "Hardware tier 3 (CPU only). Use the shared GPU box or the hosted demo for quality runs."
}

Write-Host "Done. Next, read AGENTS.md, CONTEXT.md and STATUS.md, then start 'claude' in this folder."
