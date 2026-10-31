# Source of the vendored `tsr` package

| Item | Value |
| --- | --- |
| Upstream | https://github.com/VAST-AI-Research/TripoSR |
| Commit | `107cefdc244c39106fa830359024f6a2f1c78871` |
| Licence | MIT, see `LICENSE` in this directory |
| Weights | `stabilityai/TripoSR` on Hugging Face (MIT, not gated). Downloaded by `scripts/download_weights.py`, never committed. |

## Changes from upstream

- `bake_texture.py` removed. It needs `xatlas` and `moderngl`, and the texture bake has open bugs (decision D24). The mesh keeps vertex colours.
- `models/isosurface.py`. `torchmcubes` replaced by `skimage.measure.marching_cubes` (decision D9). The `[2, 1, 0]` axis flip is gone because skimage returns vertices in volume index order. `tests/test_isosurface.py` checks the orientation.
- `models/tokenizers/image.py`. The DINO ViT config is inlined instead of downloaded from `facebook/dino-vitb16` at load time. Only the config was ever used there, the weights come from the TripoSR checkpoint.
- `system.py`. `from_pretrained` rewrites the `tsr.` class paths in `config.yaml` to the vendored package path, and loads the checkpoint with `weights_only=True`.
- `utils.py`. `remove_background` and `save_video` removed, so `rembg` and `imageio` are not imported here. Background removal lives in `sketch2shape.cutout`.
- `__init__.py` files added so the package imports under `sketch2shape.vendor`.
