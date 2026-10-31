# Image-to-3D quality and install

Research date 31 Oct 2026. Scope is the quality path on one 24 GB NVIDIA GPU (RTX 4090 or L4), Linux, uv or pip. Candidates are TripoSR, Hunyuan3D-2mini with Hunyuan3D-Paint, and TripoSG with TripoSG-scribble. Stable Fast 3D and TRELLIS are out. This file builds on `model-options.md` and `backend-feasibility.md` and does not repeat them. Nothing here was run on our machines.

## Labels

- **verified** means I read it on an official repo, model card, paper or API today.
- **reported** means a user or maintainer said it in a GitHub issue or third-party page. It may be wrong or dated.
- **unknown** means no primary source found. Any number next to it is an estimate to measure.

## Short answer

- Hunyuan3D (2.0 family shape plus Paint) is the highest-quality option that fits 24 GB and still installs. Its one hard step is compiling `custom_rasterizer` for texture.
- TripoSR is the easiest install and the only one with a believable CPU path. Its quality is a tier below, and its texture is vertex colour unless the bake works.
- TripoSG gives shape only. It adds a compiled CUDA package (`diso`) for little gain over Hunyuan shape. Keep TripoSG-scribble as an optional novelty mode, not the main path.
- Use Hunyuan3D-2.0 or 2mini, not 2.1, on a 24 GB card. 2.1 needs 29 GB for shape plus texture and has the worse install.

## Comparison table

| | TripoSR | Hunyuan3D-2mini or 2.0 plus Paint 2.0 | Hunyuan3D-2.1 | TripoSG and TripoSG-scribble |
| --- | --- | --- | --- | --- |
| Shape model | Transformer, triplane, NeRF colour, marching cubes | DiT flow matching, mini 0.6B, 2.0 1.1B | DiT 3.0B | Rectified flow, 1.5B, 2048 tokens. Scribble variant 512 tokens |
| Texture | Vertex colours. Optional UV bake (open bugs) | UV texture from 8 to 12 view diffusion, albedo only (inferred) | PBR, albedo plus metallic and roughness | None. Shape only |
| Published metrics | Chamfer and F-score on GSO and OmniObject3D, run by the authors against 2023 to 2024 models | Tencent tables, baselines anonymised. 2mini has no numbers | Tencent tables, includes TripoSG, Trellis, Step1X-3D | Ablations and a Claude-scored radar chart. No ULIP or Uni3D numbers in own paper |
| Shape VRAM | About 6 GB, verified | About 6 GB, verified | About 10 GB, verified | More than 8 GB, verified. About 9 GB peak on a 3080 Ti, reported |
| Shape plus texture VRAM | n/a | About 16 GB, verified | About 29 GB, verified. 21 GB texture alone | n/a. HF demo with MV-Adapter texture ran out of memory on a 4090, reported |
| Speed on 24 GB | Under 0.5 s on A100, authors' claim | Unknown. Reports range from 60 s to 10 min of texture time | Unknown | Unknown. Scribble uses 16 steps at 256 grid |
| CPU | Yes, slow | Shape unconfirmed. Texture no | No | No. `diso` import is hard and CUDA only |
| Compiled extensions | `torchmcubes` (skip with scikit-image shim) | `custom_rasterizer` (nvcc), `differentiable_renderer` (pybind11, g++) | Same two, plus `bpy`, `deepspeed`, `cupy` | `diso` (sdist only, CUDA) |
| Python and torch | 3.8 or later, no torch pin. Old pins on transformers and others | No torch pin. 3.10 is the tested Python | Python 3.10, torch 2.5.1+cu124, verified | Python 3.10 suggested. `numpy==1.22.3` pin |
| Direct `.glb` | Yes with `--model-save-format glb` | Yes, trimesh export with embedded texture | Unknown for PBR export | Yes, untextured |
| Licence | MIT | Tencent community, excludes EU, UK, South Korea. India is covered | Same | MIT |
| Gating | None | None found | None found | None found. RMBG-1.4 download licence unknown |
| Install effort (estimate) | 10 to 15 min | Shape 10 min. Texture adds 5 to 60 min | 1 to 3 h | 15 min |

## TripoSR

### Output quality

- The paper reports Chamfer distance 0.111 and F-score at 0.1 of 0.651 on GSO, and 0.102 and 0.677 on OmniObject3D. It beats One-2-3-45, ZeroShape, TGS and OpenLRM ([arXiv HTML](https://arxiv.org/html/2403.02151), verified). The authors ran it. It does not say who ran the baselines.
- No head-to-head with Hunyuan3D or TripoSG exists in any primary source I read. Both are later diffusion shape models. (unknown)
- Colour is a NeRF MLP output baked to vertex colours. The triplane upsampler output is 64 by 64 by 40 ([paper](https://arxiv.org/html/2403.02151), verified). Mesh detail is set by `--mc-resolution` ([run.py](https://github.com/VAST-AI-Research/TripoSR/blob/main/run.py), verified).
- Users report lumpy, low-fidelity meshes on the bundled examples ([issue 149](https://github.com/VAST-AI-Research/TripoSR/issues/149), reported) and jagged edges at high marching cubes resolution ([issue 60](https://github.com/VAST-AI-Research/TripoSR/issues/60), reported).
- The paper names no back-side behaviour. Back plausibility is unknown. The model guesses camera pose, so expect a smoothed back ([paper](https://arxiv.org/html/2403.02151), verified for the camera point).

### Sketch, cartoon and clean images

- No README, paper or issue says anything about sketches or line art. Searches for "sketch" and "cartoon" in the issue tracker returned zero hits ([issues](https://github.com/VAST-AI-Research/TripoSR/issues), verified absence).
- Training is on rendered Objaverse objects, so a clean product-style image is the intended input ([paper](https://arxiv.org/html/2403.02151), verified). Raw line art is off-distribution. (inference)
- `run.py` removes the background and resizes the foreground to 0.85 of the frame by default. Pass our own RGBA to skip this.

### Runtime, VRAM, CPU

- About 6 GB at defaults ([README](https://github.com/VAST-AI-Research/TripoSR), verified). Under 0.5 s on an A100 is the authors' claim (verified as a claim). A 4090 figure is unknown.
- CPU works. See `backend-feasibility.md` for the 25 s to 6 min reports.

### Install

- Pinned and fragile packages. `torchmcubes` from git, `transformers==4.35.0`, `Pillow==10.1.0`, `xatlas==0.0.9`, `moderngl==5.10.0` ([requirements.txt](https://raw.githubusercontent.com/VAST-AI-Research/TripoSR/main/requirements.txt), verified).
- `torchmcubes` is not on PyPI (404 today, verified) and has no wheels. Use the scikit-image shim from `backend-feasibility.md`.
- One 2026 thread posts a working list with newer pins (`transformers==4.45.0`, `huggingface-hub==0.34.0`) and no `torchmcubes` line ([issue 148](https://github.com/VAST-AI-Research/TripoSR/issues/148), reported).
- `--bake-texture` has open bugs. It fails on GPU with `--device cuda` but works with `cuda:0` ([issue 100](https://github.com/VAST-AI-Research/TripoSR/issues/100), reported). A device mismatch error remains open ([issue 156](https://github.com/VAST-AI-Research/TripoSR/issues/156), reported). A baked GLB that Blender refuses to open is also reported ([issue 150](https://github.com/VAST-AI-Research/TripoSR/issues/150), reported). `moderngl` needs an OpenGL context. Headless behaviour is unknown.
- Minimum steps. Python 3.11 venv, torch, the vendored `tsr` package, scikit-image shim, `rembg` with a pinned model. About 10 to 15 min. (estimate)

### Output and licence

- Default save format is `obj`, `glb` is selectable ([run.py](https://github.com/VAST-AI-Research/TripoSR/blob/main/run.py), verified).
- MIT for code, weights and demo ([README](https://github.com/VAST-AI-Research/TripoSR), verified). No token.

## Hunyuan3D-2mini, Turbo and Paint

### Version choice for 24 GB

| | 2.0 and 2mini | 2.1 |
| --- | --- | --- |
| Shape params | 1.1B (2.0), 0.6B (mini) | 3.0B |
| VRAM | 6 GB shape, 16 GB both | 10 GB shape, 21 GB texture, 29 GB both |
| Texture | Albedo (inferred) | PBR |
| Tested env | No pin. Python 3.10 widely used | Python 3.10, torch 2.5.1+cu124 |
| Install blockers | `custom_rasterizer` nvcc build | Same, plus `bpy==4.0`, `deepspeed`, `cupy`, `basicsr`, `RealESRGAN` weights |

Sources are the [2.0 README](https://github.com/Tencent-Hunyuan/Hunyuan3D-2) and the [2.1 README](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) (both verified).

- 2.1 is better on paper. Paint-2.1 beats Paint-2.0 on all four texture metrics, for example CLIP-I 0.9207 against 0.8893 and CLIP-FID 24.78 against 26.44 ([2.1 paper](https://arxiv.org/html/2506.15442), verified). Tencent ran it. The paper does not say who ran the baselines.
- 2.1 does not fit one-shot on 24 GB. A `--low_vram_mode` flag exists, but the README does not say what it does. Users offload with `mmgp` instead ([issue 15](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/issues/15), reported).
- 2.1 `requirements.txt` pins `bpy==4.0`, which is not on PyPI (404 today, verified). A Docker build fails on it and the fix is an extra index at `download.blender.org/pypi` ([issue 200](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/issues/200), reported). The file also pins `numpy==1.24.4`, `gradio==5.33.0`, `deepspeed` and Tencent mirror indexes ([requirements.txt](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/requirements.txt), verified).
- Verdict. Use 2.0 or 2mini with Paint 2.0 now. Revisit 2.1 only if the 2.0 texture is clearly the weak point and there are spare hours.
- Mini against full 2.0 is a real question. 24 GB can hold the full 1.1B model, so mini is not forced on us. The mini card publishes no metrics ([card](https://huggingface.co/tencent/Hunyuan3D-2mini), verified). Mini quality against 2.0 is unknown. Benchmark both.
- Paint 2.0 works with the mini shape model. The README Gradio command pairs `--model_path tencent/Hunyuan3D-2mini` with `--texgen_model_path tencent/Hunyuan3D-2`, and the repo example `textured_shape_gen_mini.py` does the same (verified).

### Output quality

- Shape and asset metrics for 2.0, from Tencent's tables. CMMD 3.193, FID_CLIP 49.165, FID 282.429, CLIP-score 0.809 against anonymised "top open-source" and "closed-source" models ([README](https://github.com/Tencent-Hunyuan/Hunyuan3D-2), verified). The paper names Trellis as the open-source baseline and shows it at CMMD 3.591 ([paper](https://arxiv.org/html/2501.12202), verified). A user study with 50 volunteers and 300 results exists, but only as a figure with no numbers in the text (verified).
- Against TripoSG on shape. Tencent's 2.1 paper lists TripoSG at ULIP-I 0.1225 and Uni3D-I 0.3129, and Hunyuan3D-DiT 2.1 at 0.1395 and 0.3213 ([paper](https://arxiv.org/html/2506.15442), verified). The margin is small and Tencent produced the table. Treat it as roughly equal, not a win.
- Texture method. 8 to 12 views, trained at 512 by 512 with a super-resolution pass per view, then baked to UV. Gaps are filled by weighted interpolation from vertex colours ([paper](https://arxiv.org/html/2501.12202), verified). Expect seams and soft patches in occluded areas. (inference)
- Early texture complaints. One user called the first release texture "like 128x128 res" and washed out ([issue 42](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/issues/42), reported, closed). A texture enhancement module shipped on 14 Feb 2025 ([README news](https://github.com/Tencent-Hunyuan/Hunyuan3D-2), verified). Current texture sharpness is unknown.
- Geometry detail, back side and floaters have no numbers in any source I read. (unknown)

### Sketch, cartoon and clean images

- The 2.0 paper, section 6.1, says sketches are first converted to detailed images and that image goes to the 3D model. The shape model does not take a sketch directly ([paper](https://arxiv.org/html/2501.12202), verified). This is our pipeline, and it is the authors' own recommended route.
- Searches for "sketch" and "line art" in the Hunyuan3D-2 issue tracker returned nothing (verified absence).
- Clean, single-object, background-removed images are the documented input ([README](https://github.com/Tencent-Hunyuan/Hunyuan3D-2), verified).
- The bundled `BackgroundRemover` calls `rembg.new_session()` with no model name ([rembg.py](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2/main/hy3dgen/rembg.py), verified). Feed it RGBA from our own pinned `rembg` step so it never runs. The example only runs it on RGB input.

### Runtime, VRAM, CPU

- 6 GB shape and 16 GB both is the official figure. The Turbo models and FlashVDM claim a 32 times generation speedup, with no absolute seconds and no GPU named ([FlashVDM](https://arxiv.org/abs/2503.16302), verified).
- A maintainer says about 1 s is possible locally with Turbo generation plus standard decoding ([issue 169](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/issues/169), reported).
- Early 4090 reports were slow. 4 min 26 s shape only and 8 min with texture, with 24 GB fully used ([issue 36](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/issues/36), reported, early 2025, likely before Turbo). A later report has 14 s for shape and about 10 min for texture, with no fix found ([issue 352](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/issues/352), reported). Another comment claims about 60 s total on a 4090 (reported, unreproduced).
- Conclusion. Shape is seconds. Texture time is the risk and ranges from 1 to 10 minutes in reports. Measure it first.
- CPU. Texture needs CUDA kernels, so no. Shape on CPU is unconfirmed ([backend-feasibility.md](backend-feasibility.md)).

### Install

- Compiled pieces. `custom_rasterizer` is a CUDA extension that needs `nvcc` ([setup.py](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2/main/hy3dgen/texgen/custom_rasterizer/setup.py), verified). `differentiable_renderer` is a pybind11 C++14 extension and needs a C++ compiler but not `nvcc` ([setup.py](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2/main/hy3dgen/texgen/differentiable_renderer/setup.py), verified).
- Official steps are `python3 setup.py install` for each, with torch from pytorch.org and no version pin ([README](https://github.com/Tencent-Hunyuan/Hunyuan3D-2), verified).
- Shape-only needs none of that and installs from `requirements.txt` plus `pip install -e .`.
- Known breakages. Twelve or more open `custom_rasterizer` issues, including `nvcc` not found, `No module named 'custom_rasterizer'`, and DLL load failures ([issue list](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/issues?q=custom_rasterizer), verified count of open items from search). One write-up says pip build isolation hides torch and CUDA 12.4 clashes with GCC 13 ([CSDN write-up](https://blog.csdn.net/weixin_44212848/article/details/150225609), reported). Python 3.11 was blamed in one thread ([issue 140](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/issues/140), reported). `transformers` 5.x breaks shape loading (from `backend-feasibility.md`, reported).
- Prebuilt wheels. None on PyPI (`custom-rasterizer` returns 404, verified). The only wheel I found is a third-party `cp312 win_amd64` build for ComfyUI ([guide](https://comfyui-wiki.com/en/tutorial/advanced/3d/huanyuan3d-2), reported). No Linux wheel found. (unknown)
- Fix for our case. Build once on the pod and keep the wheel. Both 4090 and L4 are Ada GPUs, compute capability 8.9 (NVIDIA spec, not re-read here), so one wheel covers both. Build with `TORCH_CUDA_ARCH_LIST=8.9`, a CUDA devel image whose toolkit major version matches the torch build, and `--no-build-isolation`.

```bash
# adapted from the README, untested
uv venv --python 3.10 .venv-hy && source .venv-hy/bin/activate
uv pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu124
git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2 && cd Hunyuan3D-2
uv pip install -r requirements.txt "transformers<5" && uv pip install -e .
export CUDA_HOME=/usr/local/cuda TORCH_CUDA_ARCH_LIST=8.9
uv pip install --no-build-isolation ./hy3dgen/texgen/custom_rasterizer
uv pip install --no-build-isolation ./hy3dgen/texgen/differentiable_renderer
pip wheel --no-build-isolation --no-deps -w ~/wheels ./hy3dgen/texgen/custom_rasterizer
```

- Time. Shape-only is about 10 min plus weight downloads. Texture adds 5 min if the toolchain matches and up to an hour if not. (estimate) Weight sizes are unknown.
- Python conflict. The plan pins Python 3.11 for `rembg` and the app. Hunyuan is tested on 3.10. Run it in its own 3.10 venv behind a subprocess or the repo's API server ([README](https://github.com/Tencent-Hunyuan/Hunyuan3D-2), verified that an API server exists).

### Output and licence

- `pipeline_texgen(mesh, image=image)` returns a trimesh and the example exports `demo_textured_mini.glb` ([example](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2/main/examples/textured_shape_gen_mini.py), verified). That is a GLB with an embedded texture. Blender opens GLB natively. A Blender addon also exists ([README](https://github.com/Tencent-Hunyuan/Hunyuan3D-2), verified).
- Face count and cleanliness are unknown. Default `octree_resolution=380` on the card suggests a dense mesh ([card](https://huggingface.co/tencent/Hunyuan3D-2mini), verified for the value). Check size in Blender and decimate if over a few hundred thousand faces.
- Licence is the Tencent community licence. The territory is the world excluding the EU, UK and South Korea, so India is covered. It bars using outputs to improve other AI models, and it needs a separate licence above 1M monthly active users ([LICENSE](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2/main/LICENSE), verified). No token or gating found. The mini card shows an "invalid JSON" warning on `config.json` ([card](https://huggingface.co/tencent/Hunyuan3D-2mini), verified). The Space `tencent/Hunyuan3D-2mini-Turbo` is running today ([HF API](https://huggingface.co/api/spaces/tencent/Hunyuan3D-2mini-Turbo), verified).

## TripoSG and TripoSG-scribble

### Output quality

- The paper's own numbers are ablations. Normal-FID falls from 9.47 at 512 tokens to 8.38 at 2048 and 3.36 for the final model. Data scale matters most, 5.81 at 2M samples against 11.61 for raw Objaverse ([paper](https://arxiv.org/html/2502.06608), verified). It has no ULIP or Uni3D table.
- Comparisons are qualitative, run by the authors through public HF demos. The scored radar chart used Claude 3.5 as judge. Hunyuan3D-2.0 and TripoSR are not named baselines ([paper](https://arxiv.org/html/2502.06608), verified).
- The only head-to-head with Hunyuan is Tencent's table above. Roughly equal, slightly behind.
- Geometry. VAE trained with SDF, normal and eikonal losses, 4096 tokens at inference. The authors admit thin shells reconstruct poorly and heavy normal guidance can alias. Non-manifold meshes are reported ([issue 50](https://github.com/VAST-AI-Research/TripoSG/issues/50), reported).
- Texture. The main model is "textureless geometry" and texture comes from a separate multi-view pipeline ([paper](https://arxiv.org/html/2502.06608), verified).

### Sketch, cartoon and clean images

- The README claims it handles photoreal, cartoon and sketch inputs ([README](https://github.com/VAST-AI-Research/TripoSG), authors' claim, no numbers). The paper says comic and cartoon styles ([paper](https://arxiv.org/html/2502.06608), verified).
- TripoSG-scribble takes a scribble image plus a text prompt and is CFG-distilled, so run it at CFG 0. It uses 512 latent tokens against 2048 for the base, which the README calls "fast shape prototyping" ([card](https://huggingface.co/VAST-AI/TripoSG-scribble), verified). The script runs 16 steps at a 256 grid in fp16 ([script](https://raw.githubusercontent.com/VAST-AI-Research/TripoSG/main/scripts/inference_triposg_scribble.py), verified).
- Output is shape only, saved as `.glb` with no colour. The card and README never mention texture (verified). Expect lower detail than base TripoSG or Hunyuan. (inference)
- Texturing the shape.
  - Hunyuan3D-Paint accepts any mesh. The README lists texture generation for handcrafted meshes ([README](https://github.com/Tencent-Hunyuan/Hunyuan3D-2), verified). It needs a reference image aligned with the mesh view. Whether TripoSG's axis orientation matches is unknown.
  - MV-Adapter is what the official TripoSG HF demo uses ([issue 10](https://github.com/VAST-AI-Research/TripoSG/issues/10), maintainer statement). It ships `texture_i2tex` and needs CV-CUDA ([MV-Adapter README](https://github.com/huanngzh/MV-Adapter), verified). `cvcuda-cu12` 0.19.0 is on PyPI (verified), wheel coverage unknown. An SD2.1 variant needs under 10 GB. A non-watertight mesh breaks it, per a user ([issue 50](https://github.com/VAST-AI-Research/TripoSG/issues/50), reported).
  - The repo has no texture code. The maintainers said a full release was coming and it is still open ([issue 20](https://github.com/VAST-AI-Research/TripoSG/issues/20), verified open).
- The SD image is lost on the scribble route. If we use scribble for shape we still need the SD image as the texture reference. How well the two agree is unknown.

### Runtime, VRAM, CPU

- At least 8 GB, no timings ([README](https://github.com/VAST-AI-Research/TripoSG), verified). A user sees about 9 GB peak on a 3080 Ti (reported). A 4090 OOM was the HF app with texture, not the shape script (reported).
- Time on a 4090 or L4 is unknown. A 27 minute shape run on 12 GB is reported but looks like a broken setup ([issue 32](https://github.com/VAST-AI-Research/TripoSG/issues/32), reported).
- CPU support is a feature request, still open ([issue 6](https://github.com/VAST-AI-Research/TripoSG/issues/6), verified). `inference_utils.py` imports `diso` at the top, so it needs CUDA at import ([source](https://raw.githubusercontent.com/VAST-AI-Research/TripoSG/main/triposg/inference_utils.py), verified).

### Install

- Compiled extension. `diso` ships only as an sdist on PyPI (0.1.4, 24 KB, no wheels, verified). It compiles with CUDA. Three open issues are about it failing ([53](https://github.com/VAST-AI-Research/TripoSG/issues/53), [54](https://github.com/VAST-AI-Research/TripoSG/issues/54), [48](https://github.com/VAST-AI-Research/TripoSG/issues/48), reported). A working Linux recipe is `pip install diso --no-build-isolation` ([issue 54](https://github.com/VAST-AI-Research/TripoSG/issues/54), reported).
- The scribble script sets `use_flash_decoder=False`, which takes the scikit-image path. `diso` is only used in the flash decoder ([source](https://raw.githubusercontent.com/VAST-AI-Research/TripoSG/main/triposg/inference_utils.py), verified). So a lazy import of `DiffDMC` should remove the compile for scribble. (inference, untested)
- Other pins. `numpy==1.22.3`, which predates Python 3.11 wheels, so 3.10 is effectively forced (inference). `torch-cluster` only for the full VAE encoder. A `Dinov2Model` error with `transformers` 4.57 is fixed by 4.56.2 ([issue 61](https://github.com/VAST-AI-Research/TripoSG/issues/61), reported). `pymeshlab` is used for face reduction ([requirements.txt](https://raw.githubusercontent.com/VAST-AI-Research/TripoSG/main/requirements.txt), verified).
- Minimum steps. Python 3.10 venv, torch from the CUDA index, `requirements.txt`, `pip install diso --no-build-isolation`. About 15 min. (estimate)

### Output and licence

- `--output-path x.glb`, `--faces N` decimates ([README](https://github.com/VAST-AI-Research/TripoSG), verified). Opens in Blender as plain geometry.
- MIT ([card](https://huggingface.co/VAST-AI/TripoSG-scribble), verified). The scripts download RMBG-1.4 from `briaai`. Its licence and any gating are unknown. Skip it by passing our own RGBA if the script allows.
- The Spaces `VAST-AI/TripoSG` (last updated 15 May 2025) and `VAST-AI/TripoSG-scribble` (18 Apr 2025) are both running ([HF API](https://huggingface.co/api/spaces/VAST-AI/TripoSG-scribble), verified).

## Combinations

- **Hunyuan shape plus Hunyuan Paint** is the supported pairing and the one to build. One repo, one install, one set of conventions.
- **TripoSG shape plus Hunyuan Paint** adds a second environment, `diso`, and an orientation check for about the same shape quality. Not worth it unless the pod benchmark shows a clear shape win.
- **TripoSG-scribble plus any texture** skips the SD stage, which is a nice story, but it loses the texture reference image and its shape is lower detail by design. Keep it as an optional mode.
- **TripoSR for the CPU and local tier, Hunyuan for the GPU tier** beats one model everywhere. TripoSR is the only candidate with a CPU path, and Hunyuan texture cannot run without CUDA. The cost is two output styles, vertex colour and UV texture. Normalise both to one `.glb` writer and one Blender check.

## Could not verify

- Quality of any model on our sketch-derived images. No source tests this.
- Mini against full 2.0 against 2.1, on our inputs.
- Real 4090 or L4 time and peak VRAM for 2mini plus Paint 2.0. Issue reports are old and contradictory.
- Whether `custom_rasterizer` builds on the exact pod image.
- Face counts and file sizes of Hunyuan output.
- Whether TripoSG meshes line up with Hunyuan Paint's expected orientation.
- How Blender shows TripoSR vertex colours. Blender imports `COLOR_0` as an attribute but may need a material node (my background knowledge, not checked).
- RMBG-1.4 licence and gating.
- Whether Paint 2.1 exports a PBR GLB straight from its pipeline.
- Current texture sharpness after the Feb 2025 enhancement module.

## Benchmark first on the pod

1. Before booking the pod, run the 12 test sketches through the three running Spaces. Quota is 2 min a day unauthenticated, 5 with a token ([ZeroGPU docs](https://huggingface.co/docs/hub/spaces-zerogpu)). This ranks quality with no install.
2. Build the Hunyuan venv and time the `custom_rasterizer` build. Save the wheel.
3. 2mini-Turbo against 2.0-Turbo shape, then Paint 2.0 on both. Record seconds, peak VRAM, face count, GLB size.
4. TripoSR at mc-resolution 192 and 256 on the same SD output. Record the same four numbers.
5. TripoSG-scribble with the lazy `diso` import against SD plus Hunyuan on the same sketches.
6. Hunyuan Paint on a TripoSG shape, only if step 5 shows better shape.
7. Open every GLB in Blender. Check texture visible, mesh non-empty, back side, scale.

## Recommendation

1. GPU tier. Hunyuan3D-2 family shape (try 2mini-Turbo and 2.0-Turbo) plus Paint 2.0, in its own Python 3.10 venv, fed RGBA from our pinned `rembg`.
2. Build `custom_rasterizer` once on the pod with `TORCH_CUDA_ARCH_LIST=8.9`, keep the wheel, and budget up to an hour for the first install.
3. Skip Hunyuan3D-2.1 for now. It needs 29 GB, `bpy==4.0` and a heavier install, and its win is texture metrics only.
4. CPU and fallback tier. TripoSR with the scikit-image shim and vertex colours. Avoid `--bake-texture` until its bugs are tested.
5. TripoSG-scribble is an optional shape-only novelty mode, not a default, and its `diso` import needs a patch.
6. Pick the default after step 3 of the pod benchmark, and keep the Hunyuan Spaces as a remote fallback with a clear error.
