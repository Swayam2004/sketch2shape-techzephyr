# Backend feasibility

Research date 31 Oct 2026. Scope is the sketch to 3D pipeline in `docs/PLAN.md`. Nothing here was run on our machines. Every time figure is either quoted from a source or marked as an estimate to measure.

## How to read the labels

- **verified** means I read it on an official repo, model card or doc page, or queried the HF API or PyPI today.
- **reported** means a user, a fork or a third party said it, usually in a GitHub issue. It may be wrong or out of date.
- **unknown** means no source found. Any number next to it is my estimate and must be measured.

Hardware used in the tables.

- **A** Linux, GTX 1650 Ti 4 GB, 22 GB RAM, 12 cores.
- **B** Windows 11, Ryzen 7 PRO 7840U, Radeon 780M iGPU, 16 GB RAM. CPU only in practice.
- **C** MacBook Air M2, 16 GB unified memory, MPS.

## Findings that change the plan

1. TripoSR is MIT and needs about 6 GB VRAM at defaults ([README](https://github.com/VAST-AI-Research/TripoSR), verified). A 4 GB card ran out of memory even with chunk size 8 ([issue 54](https://github.com/VAST-AI-Research/TripoSR/issues/54), reported). Plan for CPU or a remote GPU on machine A.
2. `run.py` forces CPU when CUDA is missing, even if you pass `--device mps` ([run.py](https://github.com/VAST-AI-Research/TripoSR/blob/main/run.py), verified). Machine C needs a code patch to try MPS.
3. `torchmcubes` is not on PyPI ([PyPI JSON returns 404](https://pypi.org/pypi/torchmcubes/json), verified). It builds from git and needs CMake 3.24 or newer, a C++20 compiler and `scikit-build-core>=1.0` ([README](https://github.com/tatsy/torchmcubes), verified). The official TripoSR Space is down today with exactly that error ([HF API](https://huggingface.co/api/spaces/stabilityai/TripoSR), verified). Plan to vendor a scikit-image marching cubes fallback.
4. `rembg` now defaults to `bria-rmbg`, a 1 GB model under a BRIA licence that needs a paid agreement for commercial use ([rembg README](https://github.com/danielgatis/rembg), verified). TripoSR calls `rembg.new_session()` with no model name, so it inherits that default. Pin `u2net` or `isnet-general-use`.
5. The 780M is not on AMD's ROCm list for PyTorch on Windows ([AMD docs](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/index.html), verified absence). `torch-directml` is in maintenance mode ([DirectML README](https://github.com/microsoft/DirectML), verified). Treat machine B as CPU only.
6. SF3D is gated on Hugging Face, so judges would need an HF account and token to download weights ([model card](https://huggingface.co/stabilityai/stable-fast-3d), verified). Its README tells Macs with under 32 GB unified memory to use the CPU path ([README](https://github.com/Stability-AI/stable-fast-3d), verified).
7. Hunyuan3D shape generation is the only part with a plausible low-end path. Texture needs CUDA extensions and 16 GB or more ([Hunyuan3D-2 README](https://github.com/Tencent-Hunyuan/Hunyuan3D-2), verified).
8. GTX 16xx cards have a long record of black or NaN images in fp16 ([A1111 wiki](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Troubleshooting), verified for that UI). Test fp16 first on machine A and keep an fp32 or upcast fallback.
9. `TripoSG-scribble` takes a scribble plus a prompt and returns a 3D shape directly. It is MIT and skips the SD stage ([model card](https://huggingface.co/VAST-AI/TripoSG-scribble), verified). It wants more than 8 GB VRAM, so it is a remote option only.

## Machine A, GTX 1650 Ti 4 GB, Linux

| Model | Fits? | Est. time | Source | Confidence |
| --- | --- | --- | --- | --- |
| SD 1.5 fp16 + ControlNet scribble, model CPU offload | Likely. The ControlNet card itself uses fp16 plus `enable_model_cpu_offload`. | 20 to 60 s for 30 steps. Estimate. | [card](https://huggingface.co/lllyasviel/control_v11p_sd15_scribble), [A1111 4 GB advice](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Troubleshooting) | unknown for time, reported for 4 GB fit |
| Same with LCM-LoRA, 4 steps | Same memory, plus a 67.5M LoRA. | 5 to 15 s. Estimate. | [LCM docs](https://huggingface.co/docs/diffusers/main/en/using-diffusers/inference_with_lcm_lora), [LoRA card](https://huggingface.co/latent-consistency/lcm-lora-sdv1-5) | unknown |
| TripoSR on GPU, defaults | No. About 6 GB needed. | n/a | [README](https://github.com/VAST-AI-Research/TripoSR) | verified |
| TripoSR on GPU, smaller chunks | Not confirmed. Chunk 8 still ran out of memory. | n/a | [issue 54](https://github.com/VAST-AI-Research/TripoSR/issues/54) | reported |
| TripoSR with marching cubes on CPU, chunk 4096 and halving on OOM | One 4 GB project says it works. | 60 to 105 s per object, but that figure may be a cloud run. | [3d-opensource-playground](https://github.com/Hitesh-s0lanki/3d-opensource-playground) | reported, low |
| TripoSR on CPU (`--device cpu`) | Yes. About 3 GB RAM in one report. | 25 to 45 s in one repo, almost 6 minutes in one issue. CPU models not stated. | [Meshforge](https://github.com/GamesB24/Meshforge_prototype-1), [issue 54](https://github.com/VAST-AI-Research/TripoSR/issues/54) | reported, low |
| Stable Fast 3D on GPU | No. About 6 GB. | n/a | [README](https://github.com/Stability-AI/stable-fast-3d) | verified |
| Stable Fast 3D on CPU (`SF3D_USE_CPU=1`) | Yes in principle. | unknown | [README](https://github.com/Stability-AI/stable-fast-3d) | verified for the flag, unknown for time |
| Hunyuan3D-2mini shape only | Not confirmed. Official figure is 6 GB for 2.0 shape. A Windows bundle says 4 GB "may work but very slow". | unknown | [README](https://github.com/Tencent-Hunyuan/Hunyuan3D-2), [WinPortable](https://github.com/TheRealSarcasmO/Hunyuan3D-2-WinPortable-AMD-GPU) | verified for 6 GB, reported for 4 GB |
| Hunyuan3D-2mini with texture | No. 16 GB total. | n/a | [README](https://github.com/Tencent-Hunyuan/Hunyuan3D-2) | verified |
| Hunyuan3D-2.1 | No. 10 GB shape, 21 GB texture, 29 GB both. | n/a | [README](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) | verified |
| TRELLIS | No. 16 GB minimum, Linux only. | n/a | [README](https://github.com/microsoft/TRELLIS) | verified |
| TRELLIS.2 | No. 24 GB minimum, Linux only. A fork claims 4 GB at about 3 minutes per model. | about 180 s, fork claim | [README](https://github.com/microsoft/TRELLIS.2), [Blodsom-1](https://github.com/Methurcoder/Blodsom-1) | verified for the minimum, reported for the fork |
| TripoSG and TripoSG-scribble | No. More than 8 GB. | n/a | [README](https://github.com/VAST-AI-Research/TripoSG) | verified |

Notes for A.

- Turing has no fast fp16 path on 16xx parts and many users saw black images. The A1111 wiki lists `--upcast-sampling` first, then `--no-half-vae`, then `--no-half`. In diffusers the matching moves are fp32 VAE, then fp32 UNet. Reported, not tested on diffusers.
- The 3D stage is the bottleneck. CPU TripoSR with 12 cores is the realistic local path. Measure it in hour one.
- 22 GB RAM is enough for CPU offload of SD 1.5 plus ControlNet.

## Machine B, Ryzen 7 PRO 7840U, Radeon 780M, Windows 11

Torch from PyPI on Windows is CPU only ([uv docs](https://docs.astral.sh/uv/guides/integration/pytorch/), verified). The 512 MB dedicated memory is irrelevant without a working GPU backend.

| Model | Fits? | Est. time | Source | Confidence |
| --- | --- | --- | --- | --- |
| SD 1.5 + ControlNet scribble on CPU, 20 to 30 steps | Fits in 16 GB RAM. | 1 to 4 minutes. Estimate. Reference point is 32.3 s for plain diffusers on a 32-core Xeon, which is much faster hardware. | [HF Intel CPU post](https://huggingface.co/blog/stable-diffusion-inference-intel) | unknown for this CPU |
| SD 1.5 + LCM-LoRA + ControlNet, 4 steps, CPU | Fits. | 15 to 45 s. Estimate. | [LCM docs](https://huggingface.co/docs/diffusers/main/en/using-diffusers/inference_with_lcm_lora) | unknown |
| SD-Turbo via OpenVINO (FastSD CPU) | Fits. No ControlNet. 5 s, or 1.7 s with a tiny VAE, on an i7-12700. | 5 s on a different CPU | [fastsdcpu](https://github.com/rupeshs/fastsdcpu) | reported |
| TripoSR on CPU | Yes. Needs a compiled `torchmcubes` (Visual Studio Build Tools, CMake) or a scikit-image shim. | 25 s to 6 minutes, see machine A | [torchmcubes](https://github.com/tatsy/torchmcubes), [Meshforge shim](https://github.com/GamesB24/Meshforge_prototype-1) | reported, low |
| Stable Fast 3D on CPU | Windows is experimental and needs Visual Studio 2022. | unknown | [README](https://github.com/Stability-AI/stable-fast-3d) | verified for the requirement |
| Hunyuan3D-2mini shape on CPU | No confirmed end-to-end CPU run found. Texture needs CUDA kernels, so no texture. | unknown, likely many minutes | [issue 53](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/issues/53) | unknown |
| Hunyuan3D-2.1, TRELLIS, TRELLIS.2, TripoSG | No. CUDA only. | n/a | repo READMEs linked above | verified |
| Any model via ROCm on Windows | No. AMD lists AI Max 300 and select AI 300 and 400 APUs, plus Radeon 9000 and select 7000. The 780M, Phoenix and gfx1103 are not named. | n/a | [AMD docs](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/index.html) | verified absence |
| Any model via `torch-directml` | Last release found supports PyTorch 2.3.1 only. No SD or 3D model here documents it. | n/a | [DirectML README](https://github.com/microsoft/DirectML) for maintenance mode, [release notes](https://github.com/microsoft/DirectML/releases) for 2.3.1 | verified for maintenance mode, reported for 2.3.1 |

Notes for B.

- Ship a CPU path that works with `uv sync` and no compiler. That means the scikit-image marching cubes shim.
- ROCm PyTorch wheels exist only for Linux on the PyTorch index ([uv docs](https://docs.astral.sh/uv/guides/integration/pytorch/), verified).
- If a faster path is needed, use the hosted options in the section below.

## Machine C, MacBook Air M2, 16 GB

| Model | Fits? | Est. time | Source | Confidence |
| --- | --- | --- | --- | --- |
| SD 1.5 + ControlNet scribble on MPS, fp16 | Yes. Diffusers supports MPS and advises attention slicing under 64 GB RAM. | 15 to 40 s for 20 to 30 steps. Estimate. | [diffusers MPS](https://huggingface.co/docs/diffusers/optimization/mps) | verified for support, unknown for time |
| SD 1.5 + LCM-LoRA + ControlNet, MPS | Yes. | 4 to 12 s. Estimate. | [LCM docs](https://huggingface.co/docs/diffusers/main/en/using-diffusers/inference_with_lcm_lora) | unknown |
| TripoSR on MPS | Not tested by anyone I found. `run.py` falls back to CPU unless CUDA exists, so MPS needs a patch. | unknown | [run.py](https://github.com/VAST-AI-Research/TripoSR/blob/main/run.py) | verified for the CPU fallback, unknown for MPS ops |
| TripoSR on CPU | Yes. `xatlas==0.0.9` has no macOS arm64 wheel, so bump it. | unknown, est. 30 to 120 s | [PyPI files for 0.0.9](https://pypi.org/pypi/xatlas/0.0.9/json), [0.0.11 has arm64 wheels](https://pypi.org/pypi/xatlas/json) | verified |
| Stable Fast 3D, MPS | Supported but experimental. Needs `PYTORCH_ENABLE_MPS_FALLBACK=1`. README says use CPU below 32 GB unified memory. | unknown | [README](https://github.com/Stability-AI/stable-fast-3d) | verified |
| Stable Fast 3D, CPU | Yes. | unknown | [README](https://github.com/Stability-AI/stable-fast-3d) | verified for the advice, unknown for time |
| Hunyuan3D-2mini shape on MPS | Maintainer says shape works on macOS with `--device mps` and the fallback env var. Several M2 and M4 users got cube-shaped output from the mini models. One user fixed older torch with a float32 timestep cast, another said newer torch does not need it. | about 30 s on an M1 Max with 64 GB. Nothing for 16 GB. | [issue 151](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/issues/151) | reported |
| Hunyuan3D texture on Mac | Not upstream. Community ports only. One MLX port reports about 38 GB peak for paint on an M4 Max. | n/a | [issue 151](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/issues/151) | reported |
| TRELLIS.2 on Apple Silicon | Upstream is Linux plus NVIDIA only. A fork claims about 6 GB on Apple Silicon at about 3 minutes. | about 180 s, fork claim | [Blodsom-1](https://github.com/Methurcoder/Blodsom-1) | reported, low |

Notes for C.

- MPS gaps found. Diffusers warns that NDArray sizes above 2**32 fail and that batched inference can crash ([diffusers MPS](https://huggingface.co/docs/diffusers/optimization/mps), verified). Generate one image at a time.
- `PYTORCH_ENABLE_MPS_FALLBACK=1` makes ops without a Metal kernel run on CPU, at a speed cost. SF3D documents it. One Hunyuan user said setting it in code had no effect, so export it in the shell before launch ([issue 151](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/issues/151), reported).
- A fanless Air will throttle on long runs. No source. Measure a batch of 10, not one run.

## Faster or lighter substitutes for the SD stage

| Option | Memory and speed | Fit | Source | Confidence |
| --- | --- | --- | --- | --- |
| LCM-LoRA on SD 1.5 with a ControlNet | 4 steps, guidance 1.0 to 2.0, scheduler `LCMScheduler`. Docs show canny, not scribble. | Best first swap. Same base model and same ControlNet family. | [docs](https://huggingface.co/docs/diffusers/main/en/using-diffusers/inference_with_lcm_lora) | verified for settings, unknown for scribble quality |
| T2I-Adapter sketch for SD 1.5 | Apache-2.0. The card makes no speed or memory claim. | Worth a test. Smaller than a ControlNet by design but unmeasured here. | [card](https://huggingface.co/TencentARC/t2iadapter_sketch_sd15v2) | unknown |
| SD-Turbo or SDXL-Turbo | 1 to 4 steps at 512x512, no guidance. Neither card mentions ControlNet. Img2img from the sketch is documented. | Use as img2img on the cleaned sketch, not as a control model. | [sd-turbo](https://huggingface.co/stabilityai/sd-turbo), [sdxl-turbo](https://huggingface.co/stabilityai/sdxl-turbo) | verified |
| SDXL scribble ControlNet | Apache-2.0 weights, but SDXL fp16 is heavy for 4 GB. | Remote only. | [xinsir](https://huggingface.co/xinsir/controlnet-scribble-sdxl-1.0) | unknown for VRAM |
| FastSD CPU with OpenVINO | 0.8 s to 5 s per 512x512 image on an i7-12700 for distilled models. | CPU fallback for machine B if no ControlNet is acceptable. Intel focused. | [repo](https://github.com/rupeshs/fastsdcpu) | reported |
| Skip generation, feed the cleaned sketch to the 3D model | TripoSR trained on Objaverse renders, so line art is off-distribution. | Add as a "lite" mode and score it with silhouette IoU. | [TripoSR card](https://huggingface.co/stabilityai/TripoSR) | verified for training data, unknown for quality |
| TripoSG-scribble | One model, scribble plus prompt to shape. Needs more than 8 GB. | Remote only. | [card](https://huggingface.co/VAST-AI/TripoSG-scribble) | verified |

## Free hosted GPUs

| Option | Limits | Token needed? | Source | Confidence |
| --- | --- | --- | --- | --- |
| HF Spaces ZeroGPU, as a caller | Daily GPU quota of 2 minutes unauthenticated, 5 minutes with a free account, 40 minutes on PRO. Default call length 60 s unless the Space sets a longer duration. Quota resets 24 hours after first use. GPU is a half RTX Pro 6000 with 48 GB. | No for public Spaces. Passing a token charges your own quota and gives better limits than the shared anonymous pool. | [ZeroGPU docs](https://huggingface.co/docs/hub/spaces-zerogpu), [API docs](https://huggingface.co/docs/hub/spaces-api-endpoints) | verified |
| HF Spaces ZeroGPU, as a host | Free accounts older than 30 days with a verified email can host 2 ZeroGPU Spaces. | Yes, the host account. | [ZeroGPU docs](https://huggingface.co/docs/hub/spaces-zerogpu) | verified |
| Kaggle notebooks | About 30 GPU hours a week, floating. Sessions up to 12 hours. P100 or T4. | Kaggle login. Phone verification and the internet toggle for GPU sessions are common knowledge, not confirmed on a primary page today. | [GPU doc](https://www.kaggle.com/docs/efficient-gpu-usage), [notebooks doc](https://www.kaggle.com/docs/notebooks) | reported. The doc pages did not render in my fetch, only search snippets. |
| Google Colab free | Up to 12 hours a session, resources not guaranteed, limits not published, idle timeout, GPU type varies. Free runtimes may not "bypass the notebook UI to interact mainly through a web UI", and SSH is also barred. | Google account. | [Colab FAQ](https://research.google.com/colaboratory/faq.html) | verified |

Status of public Spaces on 31 Oct 2026, read from the HF API.

| Space | Stage | Hardware | Notes | Confidence |
| --- | --- | --- | --- | --- |
| [stabilityai/TripoSR](https://huggingface.co/spaces/stabilityai/TripoSR) | RUNTIME_ERROR | none | `torchmcubes` build fails, `scikit-build-core` 0.12.2 below the 1.0 minimum | verified |
| [stabilityai/stable-fast-3d](https://huggingface.co/spaces/stabilityai/stable-fast-3d) | RUNNING | ZeroGPU | Endpoint `/run_button` takes image, foreground ratio, remesh option, vertex count, texture size. Returns a preview and a 3D model. | verified |
| [tencent/Hunyuan3D-2.1](https://huggingface.co/spaces/tencent/Hunyuan3D-2.1) | RUNNING | ZeroGPU | Endpoints `/shape_generation` and `/generation_all` (shape plus texture). Takes image, steps, guidance, seed, octree resolution, rembg flag, chunks. | verified |
| [tencent/Hunyuan3D-2mini-Turbo](https://huggingface.co/spaces/tencent/Hunyuan3D-2mini-Turbo) | RUNNING | ZeroGPU | Endpoint list not retrievable by script. Use the "Use via API" page. | verified for status, unknown for endpoints |
| [VAST-AI/TripoSG-scribble](https://huggingface.co/spaces/VAST-AI/TripoSG-scribble) | RUNNING | ZeroGPU | Last modified Apr 2025. | verified for status |
| [microsoft/TRELLIS](https://huggingface.co/spaces/microsoft/TRELLIS) | CONFIG_ERROR | none | | verified |
| [microsoft/TRELLIS.2](https://huggingface.co/spaces/microsoft/TRELLIS.2) | RUNNING | ZeroGPU | | verified |

### Is a public Space via `gradio_client` a reasonable fallback?

Yes, as an optional fallback. No, as the only path.

- It works. Every Gradio Space exposes an API and `Client("owner/space")` needs no token for public Spaces ([docs](https://huggingface.co/docs/hub/spaces-api-endpoints), verified).
- The anonymous quota is 2 minutes of GPU a day, shared with everyone behind the same pool. A judge with a free HF token gets 5 minutes ([ZeroGPU docs](https://huggingface.co/docs/hub/spaces-zerogpu), verified). That is roughly a dozen runs if each takes 20 to 30 GPU seconds. The per-run figure is my estimate.
- Spaces change without notice. The official TripoSR Space is broken right now and the TRELLIS Space has a config error. Pin the Space id and `api_name`, wrap the call, and fail with a clear message.
- Inputs leave the machine. Say so in the README and AI disclosure.
- Safer shape for the README. Local backend by default. `--backend remote` points at a Space id read from an env var, with the token read from `HF_TOKEN`. A duplicated Space under our own account removes the dependency on someone else's edits and counts against the caller's quota.
- Do not tell judges to run the Gradio app inside free Colab. The FAQ restriction above makes that risky. Ship a notebook that runs the pipeline in cells.

## Licences and disclosure

| Item | Licence | Restrictions that matter | Source | Confidence |
| --- | --- | --- | --- | --- |
| TripoSR | MIT | Usage policy bars disturbing or stereotyping outputs. Trained on Objaverse (CC-BY subset). | [card](https://huggingface.co/stabilityai/TripoSR) | verified |
| Stable Fast 3D | Stability AI Community Licence, gated | Free for research and non-commercial use, and for commercial use under US$1M annual revenue. Above that needs an Enterprise licence. Users must accept terms on HF. | [card](https://huggingface.co/stabilityai/stable-fast-3d) | verified |
| Hunyuan3D-2, 2mini, 2.1 | Tencent Hunyuan community licences (HF tag `other`) | Territory excludes the EU, UK and South Korea. More than 1M monthly active users needs a separate licence. No using outputs to train other AI models. No military use. Hosted services must name the real provider and say Tencent is not affiliated. | [2.0 licence](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2/main/LICENSE), [2.1 licence](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/LICENSE), [mini licence](https://huggingface.co/tencent/Hunyuan3D-2mini/raw/main/LICENSE) | verified |
| TRELLIS, TRELLIS.2 | MIT, with separate terms for submodules such as diffoctreerast and FlexiCubes, and for nvdiffrast and nvdiffrec | Check submodule licences if redistributed | [TRELLIS](https://github.com/microsoft/TRELLIS), [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) | verified |
| TripoSG, TripoSG-scribble | MIT | None found | [HF API tag](https://huggingface.co/api/models/VAST-AI/TripoSG-scribble) | verified |
| SD 1.5 | CreativeML OpenRAIL-M | Use-based restrictions pass to downstream users. The repo is a mirror of the deprecated Runway one. | [card](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5) | verified |
| ControlNet v1.1 scribble | OpenRAIL | Same family of use restrictions | [card](https://huggingface.co/lllyasviel/control_v11p_sd15_scribble) | verified |
| HED annotator weights (`lllyasviel/Annotators`) | HF tag `other`, card empty | Terms unknown. Avoid or replace with our own thresholding. | [repo](https://huggingface.co/lllyasviel/Annotators) | unknown |
| LCM-LoRA SD 1.5 | OpenRAIL++ | Use-based restrictions | [card](https://huggingface.co/latent-consistency/lcm-lora-sdv1-5) | verified |
| T2I-Adapter sketch, xinsir SDXL scribble | Apache-2.0 | None found | [adapter](https://huggingface.co/TencentARC/t2iadapter_sketch_sd15v2), [xinsir](https://huggingface.co/xinsir/controlnet-scribble-sdxl-1.0) | verified (HF tag) |
| SD-Turbo, SDXL-Turbo | Stability terms. The SDXL-Turbo page shows `sai-nc-community` and also says commercial use is intended with a licence from stability.ai. The SD-Turbo page names no licence. | Treat as non-commercial research until read in full | [sd-turbo](https://huggingface.co/stabilityai/sd-turbo), [sdxl-turbo](https://huggingface.co/stabilityai/sdxl-turbo) | verified that the text is ambiguous |
| rembg library | MIT | Weights have their own licences | [README](https://github.com/danielgatis/rembg) | verified |
| rembg default `bria-rmbg` (RMBG-2.0) | BRIA licence | Paid agreement for commercial use | [README](https://github.com/danielgatis/rembg) | verified |
| torchmcubes | MPL-2.0 | File-level copyleft if modified and redistributed | [pyproject](https://github.com/tatsy/torchmcubes/blob/main/pyproject.toml) | verified |

The event asks for disclosure, not for commercial use. All of the above are fine for a hackathon demo. List each model, its licence and its source in the README third-party table. If a judge is in the EU, UK or South Korea, Hunyuan3D is not licensed for them at all. That is a reason to keep it optional.

## Install pitfalls with uv

### Torch index

- On Linux, the default PyPI torch is a CUDA build with large NVIDIA dependencies. On Windows and macOS, PyPI torch is CPU only for Windows and the normal build for macOS. PyTorch publishes no CUDA build for macOS and no ROCm build for macOS or Windows ([uv docs](https://docs.astral.sh/uv/guides/integration/pytorch/), verified).
- Available indexes include `cpu`, `cu118`, `cu126`, `cu128`, `cu130` and `rocm7.2` ([uv docs](https://docs.astral.sh/uv/guides/integration/pytorch/), verified).
- `--torch-backend=auto` detects CUDA, AMD and Intel GPUs and falls back to CPU, but only in the `uv pip` interface, not `uv sync` ([uv docs](https://docs.astral.sh/uv/guides/integration/pytorch/), verified).
- Our driver is 580. Check `torch.cuda.get_arch_list()` includes `sm_75` after install. I did not verify that the cu130 wheel keeps Turing. Prefer `cu126` or `cu128` for machine A.
- A pattern to test, using extras so judges pick `cpu` or `cu128` by hand. This is adapted from the uv docs and is untested here.

```toml
[project.optional-dependencies]
cpu = ["torch"]
cu128 = ["torch"]

[tool.uv]
conflicts = [[{ extra = "cpu" }, { extra = "cu128" }]]

[tool.uv.sources]
torch = [
  { index = "pytorch-cpu", extra = "cpu" },
  { index = "pytorch-cu128", extra = "cu128" },
]

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true

[[tool.uv.index]]
name = "pytorch-cu128"
url = "https://download.pytorch.org/whl/cu128"
explicit = true
```

macOS needs neither extra. Plain PyPI torch is the build to use there. That is the uv docs' statement about macOS, and I did not confirm MPS support on that page. MPS support itself is covered by the diffusers docs.

### Python version

- `rembg` needs Python 3.11 or newer ([pyproject](https://raw.githubusercontent.com/danielgatis/rembg/main/pyproject.toml), verified).
- `xatlas==0.0.9`, pinned by TripoSR, has wheels up to Python 3.12 and none for macOS arm64 ([PyPI](https://pypi.org/pypi/xatlas/0.0.9/json), verified). Version 0.0.11 ships arm64 wheels for 3.10 to 3.13 ([PyPI](https://pypi.org/pypi/xatlas/json), verified).
- TripoSR also pins `transformers==4.35.0`, `Pillow==10.1.0`, `trimesh==4.0.5`, `moderngl==5.10.0` and leaves `gradio` unpinned ([requirements.txt](https://raw.githubusercontent.com/VAST-AI-Research/TripoSR/main/requirements.txt), verified). Pin Python 3.11 in `.python-version`. `tokenizers` 0.14.1 has cp312 wheels, so 3.12 may also work, but I did not test it.
- Do not install TripoSR's `requirements.txt` as is. Vendor the `tsr` package and own the dependency list.

### rembg and onnxruntime

- Use `rembg[cpu]` on every platform to start. `onnxruntime-gpu` is excluded on macOS in rembg's own markers, and `onnxruntime-rocm` is Linux only ([pyproject](https://raw.githubusercontent.com/danielgatis/rembg/main/pyproject.toml), verified).
- `rembg[gpu]` adds CUDA and cuDNN requirements on NVIDIA ([README](https://github.com/danielgatis/rembg), verified). Only worth it on machine A, and only if CPU rembg proves slow.
- rembg has no DirectML extra, so Windows on AMD means CPU ([pyproject](https://raw.githubusercontent.com/danielgatis/rembg/main/pyproject.toml), verified absence).
- Pass the model name explicitly. `u2net` or `isnet-general-use` avoids the 1 GB BRIA download and its licence. Models land in `~/.rembg/models/` and `REMBG_HOME` moves them ([README](https://github.com/danielgatis/rembg), verified).

### torchmcubes

- Not on PyPI. Needs the PyTorch install first, `scikit-build-core>=1.0`, `pybind11`, CMake 3.24 or newer, a C++20 compiler, and `--no-build-isolation` ([README](https://github.com/tatsy/torchmcubes), verified). The repo's own `pyproject.toml` sets `no-build-isolation = true` under `[tool.uv]`.
- CUDA build needs CUDA Toolkit 12 or newer with `nvcc`. Without it you get a CPU build and CUDA tensors are processed on the CPU with a warning. ROCm is not supported ([README](https://github.com/tatsy/torchmcubes), verified).
- Windows builds fail often without Visual C++ Build Tools. One reporter also needed the Windows 11 SDK ([TripoSR issues](https://github.com/VAST-AI-Research/TripoSR/issues/125), reported).
- TripoSR itself catches the missing-CUDA error and reruns marching cubes on CPU, which only helps if the package already installed ([isosurface.py](https://github.com/VAST-AI-Research/TripoSR/blob/main/tsr/models/isosurface.py), verified).
- Recommended fix. Try `import torchmcubes`, else call `skimage.measure.marching_cubes` and convert to tensors. The upstream attempt, [PR 26](https://github.com/VAST-AI-Research/TripoSR/pull/26), was closed unmerged. It reported no speed loss, plus a `NameError` for a leftover `marching_cubes` assignment, and one report says axis order can differ from the reference code (reported). Check orientation on a known mesh.
- Expect scikit-image on CPU to be slower than the CUDA kernel at mc-resolution 256. No source has numbers. Drop to 192 or 128 on CPU.

### Other model installs

- Hunyuan3D texture builds `custom_rasterizer` and `DifferentiableRenderer` from source and needs CUDA. On Apple Silicon the build fails on a missing `CUDA_HOME` ([issue 320](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/issues/320), reported). Shape only needs none of that.
- Hunyuan3D shape with transformers 5.x fails on a renamed DINOv2 key. Pin transformers below 5 ([PR 382](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/pull/382), reported).
- SF3D builds `texture_baker` and `uv_unwrapper` extensions. The README documents a Metal path for MPS and says Windows needs Visual Studio 2022 ([README](https://github.com/Stability-AI/stable-fast-3d), verified).
- TRELLIS needs a CUDA toolkit to compile submodules, plus flash-attn or xformers and spconv ([README](https://github.com/microsoft/TRELLIS), verified). Not a uv-friendly install. Keep it out of the main environment.

## Open items to measure in hour one

1. Does SD 1.5 fp16 plus ControlNet scribble produce non-black images on machine A, and what is peak VRAM with `enable_model_cpu_offload`?
2. TripoSR CPU wall time at mc-resolution 128, 192 and 256 on A, B and C.
3. Does TripoSR run on MPS after patching `run.py`, or does it need `PYTORCH_ENABLE_MPS_FALLBACK=1`?
4. SF3D on CPU on A. Is the gated download worth the README burden?
5. Hunyuan3D-2mini shape on A with offload. Only if the time is acceptable.
6. LCM-LoRA with the scribble ControlNet. Sketch fidelity at 4 steps compared to 25.

## Recommendation

1. Machine A. SD 1.5 + scribble ControlNet fp16 with model offload (fp32 VAE if images go black), rembg `u2net`, TripoSR with CPU marching cubes at resolution 192, remote Space for the high-quality run.
2. Machine B. Everything on CPU. LCM-LoRA + ControlNet at 4 steps, TripoSR with the scikit-image shim, no compiled extension, `--backend remote` as the quick path.
3. Machine C. SD 1.5 + LCM-LoRA + ControlNet on MPS with attention slicing, TripoSR on CPU (try MPS after a patch), `xatlas>=0.0.10`, SF3D on CPU as the second model.
4. Judges. Default to the CPU-safe local stack on Python 3.11 with a pinned CPU torch extra, and an optional `HF_TOKEN` remote backend that tolerates failure.
5. Keep Hunyuan3D, TRELLIS and TripoSG-scribble as remote-only experiments and list their licences in the README.
