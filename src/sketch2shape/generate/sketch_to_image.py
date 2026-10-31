from __future__ import annotations

import gc
import logging
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

from sketch2shape.types import IMAGE_SIZE, Device, PreparedSketch

if TYPE_CHECKING:
    from diffusers import StableDiffusionControlNetPipeline

log = logging.getLogger(__name__)

# Folder names under S2S_WEIGHTS_DIR. They match the repo names that
# scripts/download_weights.py downloads.
SD_DIR_NAME = "stable-diffusion-v1-5"
CONTROLNET_DIR_NAME = "control_v11p_sd15_scribble"

DEFAULT_SUBJECT = "a single object"
PROMPT_TEMPLATE = "{prompt}, product design render, single object, centred, plain white background, soft studio lighting"
NEGATIVE_PROMPT = (
    "clutter, text, watermark, multiple objects, cropped, out of frame, background scenery, "
    "blurry, low quality"
)

# Start values from docs/tasks/udit.md. Tune them in EXPERIMENTS.md, not per device: the hosted
# link and a local run must use the same numbers.
STEPS = 20
GUIDANCE_SCALE = 7.5
CONTROLNET_SCALE = 1.0


# Set S2S_OFFLOAD=1 to keep the models on the CPU and move each one to the GPU only while it runs.
# It fits cards under 8 GB at a speed cost. Off by default until EXPERIMENTS.md has the numbers.
OFFLOAD_ENV = "S2S_OFFLOAD"


class ModelFilesMissing(FileNotFoundError):
    """Stable Diffusion or ControlNet weights are not in the weights folder."""


def build_prompt(prompt: str | None) -> str:
    subject = (prompt or "").strip() or DEFAULT_SUBJECT
    return PROMPT_TEMPLATE.format(prompt=subject)


def is_degenerate(image: Image.Image) -> bool:
    """True for the all-black or flat output that fp16 overflow produces on some GPUs.

    NaN latents decode to black, so checking pixels also catches NaN without a separate pass.
    """
    arr = np.asarray(image.convert("RGB"), dtype=np.uint8)
    return int(arr.max()) < 8 or float(arr.std()) < 1.0


def weights_dir() -> Path:
    return Path(os.environ.get("S2S_WEIGHTS_DIR", "weights"))


def _model_paths(root: Path) -> tuple[Path, Path]:
    sd, controlnet = root / SD_DIR_NAME, root / CONTROLNET_DIR_NAME
    missing = [
        p
        for p in (sd, controlnet)
        if not (p / "model_index.json").is_file() and not (p / "config.json").is_file()
    ]
    if missing:
        names = ", ".join(str(p) for p in missing)
        raise ModelFilesMissing(
            f"Missing model files: {names}. Run `uv run python scripts/download_weights.py` first. "
            "It downloads about 7 GB in total and skips files you already have."
        )
    return sd, controlnet


@lru_cache(maxsize=2)
def _load_pipeline(device: Device, fp16: bool) -> StableDiffusionControlNetPipeline:
    # Imported here so importing sketch2shape.generate stays cheap for the UI and the tests.
    import torch
    from diffusers import (
        ControlNetModel,
        StableDiffusionControlNetPipeline,
        UniPCMultistepScheduler,
    )

    sd_path, controlnet_path = _model_paths(weights_dir())
    dtype = torch.float16 if fp16 else torch.float32
    started = time.perf_counter()

    controlnet = ControlNetModel.from_pretrained(
        controlnet_path, torch_dtype=dtype, local_files_only=True
    )
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        sd_path,
        controlnet=controlnet,
        torch_dtype=dtype,
        # The safety checker is a second model to ship and it blacks out harmless sketches.
        safety_checker=None,
        requires_safety_checker=False,
        local_files_only=True,
    )
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.set_progress_bar_config(disable=True)
    if fp16:
        # Suspected cause of the black frame: the VAE decoder overflows to NaN in fp16. It is
        # 83 M parameters, so 330 MB in fp32 is cheap. _run decodes the latents itself.
        pipe.vae.to(torch.float32)
    if device == "cuda" and os.environ.get(OFFLOAD_ENV) == "1":
        pipe.enable_model_cpu_offload()
    elif device == "cuda":
        pipe.to("cuda")
    else:
        # Cuts peak RAM on a 16 GB laptop at a small speed cost.
        pipe.enable_attention_slicing()
    log.info(
        "generate: loaded SD1.5 + ControlNet scribble on %s (%s) in %.1f s",
        device,
        dtype,
        time.perf_counter() - started,
    )
    return pipe


def _release_pipelines(device: Device) -> None:
    """Drop every cached pipeline and give the GPU memory back before the next load.

    Without this the fp16 pipeline stays in the lru_cache while the fp32 one loads, and a 4 GB
    card runs out of memory.
    """
    _load_pipeline.cache_clear()
    gc.collect()
    if device == "cuda":
        import torch

        torch.cuda.empty_cache()


def _run(
    pipe: StableDiffusionControlNetPipeline, sketch: PreparedSketch, prompt: str, seed: int
) -> Image.Image:
    import torch

    # A CPU generator gives the same starting noise on every device, which keeps CPU and CUDA
    # runs of one seed close to each other.
    generator = torch.Generator(device="cpu").manual_seed(seed)
    out = pipe(
        prompt=prompt,
        negative_prompt=NEGATIVE_PROMPT,
        image=sketch.scribble.convert("RGB"),
        num_inference_steps=STEPS,
        guidance_scale=GUIDANCE_SCALE,
        controlnet_conditioning_scale=CONTROLNET_SCALE,
        width=IMAGE_SIZE,
        height=IMAGE_SIZE,
        generator=generator,
        output_type="latent",
    )
    # Decode here instead of inside the pipeline so the VAE can run in fp32 while the UNet and
    # ControlNet stay in fp16. For an fp32 pipeline this is the same maths as the default path.
    with torch.no_grad():
        latents = out.images.to(device=pipe._execution_device, dtype=pipe.vae.dtype)
        decoded = pipe.vae.decode(latents / pipe.vae.config.scaling_factor, return_dict=False)[0]
    image = pipe.image_processor.postprocess(decoded, output_type="pil")[0]
    return image.convert("RGB")


def sketch_to_image(
    sketch: PreparedSketch, prompt: str | None, seed: int, device: Device
) -> Image.Image:
    """Turn a cleaned sketch into a 512 px RGB picture of one object on a plain background."""
    full_prompt = build_prompt(prompt)
    started = time.perf_counter()

    # Weights must exist before we touch torch, so the error is clear on a fresh clone.
    _model_paths(weights_dir())

    use_fp16 = device == "cuda"
    image = _run(_load_pipeline(device, use_fp16), sketch, full_prompt, seed)
    if use_fp16 and is_degenerate(image):
        # GTX 16xx cards overflow in fp16 and return black frames.
        log.warning("generate: fp16 output is black or flat, retrying in fp32")
        _release_pipelines(device)
        image = _run(_load_pipeline(device, False), sketch, full_prompt, seed)
    if is_degenerate(image):
        raise RuntimeError(
            "Stable Diffusion returned a blank image even in fp32. Check the weights."
        )

    log.info(
        "generate: seed %d, device %s, %.1f s, prompt %r",
        seed,
        device,
        time.perf_counter() - started,
        full_prompt,
    )
    return image
