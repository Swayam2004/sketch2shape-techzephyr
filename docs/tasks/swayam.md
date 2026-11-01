# Swayam. Integrator

Machine. Linux, GTX 1650 Ti (4 GB), 22 GB RAM. TripoSR needs about 6 GB on GPU, so your laptop runs it on CPU and the pod runs it on GPU. Same code, different device.

You own `src/sketch2shape/reconstruct/`, `cutout/`, `export/`, `api/`, `pipeline.py`, `infra/`, `scripts/download_weights.py`, and merging PRs.

Read `docs/tasks/README.md` first and follow the sync routine.

## S1. Dependencies and contracts. Done in the kickoff PR

`pyproject.toml` now has torch, diffusers, transformers, fastapi and the rest. Plain `torch` from PyPI gives a CUDA build on Linux and a CPU build on Windows. A Windows judge with an NVIDIA card gets CPU torch unless they use the CUDA index. That is acceptable. Document it in the README.

Check later. TripoSR pins `transformers==4.35.0` and the lock now holds transformers 5. If the vendored model breaks, patch the vendored code, do not downgrade the whole project.

## S2. TripoSR on CPU. Target 17:30

Goal. `reconstruct.image_to_mesh(rgba, seed, device) -> trimesh.Trimesh` works on CPU and later on CUDA.

1. Vendor the `tsr` package from `VAST-AI-Research/TripoSR` into `src/sketch2shape/vendor/tsr/` with its MIT licence file and a `SOURCE.md` giving the commit hash. Remove the `torchmcubes` import. Use `skimage.measure.marching_cubes` instead and check orientation on a known shape (a cube with one corner marked).
2. Weights. `scripts/download_weights.py` downloads TripoSR (`stabilityai/TripoSR`), SD 1.5 (`stable-diffusion-v1-5/stable-diffusion-v1-5`), ControlNet scribble (`lllyasviel/control_v11p_sd15_scribble`) and the rembg model (`isnet-general-use`) into `weights/`. All are ungated. It skips what already exists and prints sizes. Windows and Mac must work.
3. Return vertex colours. Do not use `--bake-texture`, it has open bugs (GLBs that do not open in Blender).
4. Set marching-cubes resolution 256 on GPU and 192 on CPU. Both are settings, not forks of the code. Keep defaults identical across devices unless the CPU time is unusable, and then decide it with the team.

Done when. A hand-picked RGBA PNG of a chair becomes a `.glb` that loads in `trimesh` and opens in Blender with colours. Timing is in `EXPERIMENTS.md`.

## S3. Cutout, cleanup, export, validate. Target 19:00

- `cutout.remove_background(image) -> RGBA`. rembg with `isnet-general-use`, explicit session. Centre the object and rescale it to about 85 percent of the frame, as TripoSR expects.
- `export.finalize_mesh(mesh)`. Keep the largest connected component, fix normals, merge duplicate vertices, normalise to a unit cube, glTF axes (see `types.py`), keep vertex colours.
- `export.save_mesh(mesh, out_dir, stem) -> ExportPaths`. Writes `.glb` and `.obj`.
- `export.validate_mesh(path) -> ValidationReport`. Reload the file, check non-empty, face count, colours present, watertight flag. This is the "basic mesh validation" the problem statement asks for.

Done when. Tests with synthetic meshes pass. A broken input raises a clear error.

## S4. Pipeline and CLI. Target 20:00

- `pipeline.run(request, device) -> GenerationResult`. Calls Udit's `prepare_sketch` and `sketch_to_image` and your stages. Times each stage and records peak VRAM on CUDA. Collects warnings, including the CPU warning.
- Device selection. `S2S_BACKEND=auto|cuda|cpu`, default auto (CUDA when `torch.cuda.is_available()`).
- CLI. `uv run sketch2shape generate sketch.png --prompt "..." --seed 1 --out outputs/`. Add `[project.scripts]` in `pyproject.toml`.
- Until Udit's stages land, use a pass-through stub so you can test the rest. Remove it afterwards.

## S5. FastAPI server. Target 21:00

Implement `docs/api.md` in `src/sketch2shape/api/`. One worker thread runs jobs one at a time, because one GPU. Queue limit 5. Rate limit per IP. Access code from `S2S_ACCESS_CODE`. Remove finished jobs older than 1 hour. Mount nothing else yet. Test with `httpx` against the app, using a fake pipeline.

## S6. Run it on the pod. Target 20:30, after Udit posts the address

- `bash infra/runpod/bootstrap.sh`, then run the CLI on a few test sketches on CUDA.
- Log seconds and peak VRAM per stage in `EXPERIMENTS.md`. If TripoSR runs out of memory, report it.
- Expose port 7860 for a demo (proxy URL format is in `docs/guides/runpod-dev-gpu.md`).

## S7. Hosted demo on Modal. Dropped on 1 Nov (D25 in `CONTEXT.md`), kept below for the record

Udit's card pays. Udit creates the Modal account and shares the project through a Modal token set as a secret on the box you deploy from. Never commit tokens.

- Build a Modal image from this repo (uv sync), keep weights in a Modal Volume, run the API on a GPU function (L4) with scale to zero, and serve the Gradio UI from a CPU container that calls the GPU function. Jobs and polling because web endpoints cut at 150 seconds.
- Measure cold start. Add a warm-up ping and a daily keep-alive if cold start is bad.
- Write `docs/guides/modal-deploy.md` as you go.
- Backup, later. A free ZeroGPU Space and a static page with sample `.glb` files. All three of our HF accounts are old enough to host one. ZeroGPU lists Python 3.10 or 3.12 only, so check before relying on it.

## S8. Ongoing

- Merge PRs quickly. Review for contract breaks (`types.py`, `docs/api.md`), not style.
- AWS credit exploration is optional and capped at 30 minutes (`docs/guides/aws-gpu-optional.md`).
- Keep `STATUS.md` current. Watch Disha's and Udit's blockers first.
- At 00:00 start the quality loop with Udit's eval harness. Ideas in order. Best-of-N by silhouette IoU, prompt template tuning, ControlNet conditioning strength, marching-cubes resolution.

## Kickoff prompt

> Read AGENTS.md, CONTEXT.md, STATUS.md, PLAN.md, docs/tasks/README.md and docs/tasks/swayam.md. Run the sync routine. Do S2 first. Tell me your plan in five lines, then go.
