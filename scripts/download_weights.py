"""Download every model the pipeline needs into `weights/`. All are ungated, no token needed.

    uv run python scripts/download_weights.py                 # everything
    uv run python scripts/download_weights.py triposr rembg   # only some

Existing files are skipped, so it is safe to rerun. Works on Linux, macOS and Windows.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from huggingface_hub import hf_hub_download

from sketch2shape.weights import (
    controlnet_scribble_dir,
    rembg_home,
    sd15_dir,
    triposr_dir,
    weights_dir,
)

logger = logging.getLogger("download_weights")


@dataclass(frozen=True)
class HfModel:
    key: str
    repo_id: str
    licence: str
    files: tuple[str, ...]
    target: Path

    def missing(self) -> list[str]:
        return [f for f in self.files if not (self.target / f).is_file()]


def hf_models() -> list[HfModel]:
    # SD 1.5 is fetched as fp32 safetensors, which loads on CPU and can be cast to fp16 on GPU.
    # The safety checker and the 4 to 7 GB single-file checkpoints are left out on purpose.
    # Load the pipeline with `safety_checker=None`.
    return [
        HfModel(
            "triposr",
            "stabilityai/TripoSR",
            "MIT",
            ("config.yaml", "model.ckpt"),
            triposr_dir(),
        ),
        HfModel(
            "sd15",
            "stable-diffusion-v1-5/stable-diffusion-v1-5",
            "CreativeML Open RAIL-M",
            (
                "model_index.json",
                "scheduler/scheduler_config.json",
                "feature_extractor/preprocessor_config.json",
                "tokenizer/merges.txt",
                "tokenizer/special_tokens_map.json",
                "tokenizer/tokenizer_config.json",
                "tokenizer/vocab.json",
                "text_encoder/config.json",
                "text_encoder/model.safetensors",
                "unet/config.json",
                "unet/diffusion_pytorch_model.safetensors",
                "vae/config.json",
                "vae/diffusion_pytorch_model.safetensors",
            ),
            sd15_dir(),
        ),
        HfModel(
            "controlnet",
            "lllyasviel/control_v11p_sd15_scribble",
            "OpenRAIL",
            ("config.json", "diffusion_pytorch_model.safetensors"),
            controlnet_scribble_dir(),
        ),
    ]


def fetch_hf(model: HfModel) -> None:
    missing = model.missing()
    if not missing:
        logger.info("%s: already present in %s", model.key, model.target)
    for name in missing:
        logger.info("%s: downloading %s from %s (%s)", model.key, name, model.repo_id, model.licence)
        hf_hub_download(repo_id=model.repo_id, filename=name, local_dir=model.target)
    report(model.key, [model.target / f for f in model.files])


def fetch_rembg() -> None:
    # Imported late. rembg reads REMBG_HOME when the class is used, not at import time.
    os.environ["REMBG_HOME"] = str(rembg_home())
    if os.environ.get("U2NET_HOME"):
        logger.warning("U2NET_HOME is set and overrides REMBG_HOME, rembg will use it.")
    from rembg.sessions.dis_general_use import DisSession

    # `isnet-general-use`, not the library default. See decision D9.
    path = Path(DisSession.download_models())
    report("rembg", [path])


def report(key: str, paths: list[Path]) -> None:
    total = sum(p.stat().st_size for p in paths if p.is_file())
    logger.info("%s: %d files, %.1f MB in total", key, len(paths), total / 1e6)


def main(argv: list[str] | None = None) -> int:
    keys = [m.key for m in hf_models()] + ["rembg"]
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("only", nargs="*", help=f"subset of {keys}, default all")
    args = parser.parse_args(argv)
    unknown = sorted(set(args.only) - set(keys))
    if unknown:
        parser.error(f"unknown model {unknown}, choose from {keys}")
    wanted = set(args.only) or set(keys)

    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    for noisy in ("httpx", "httpcore", "huggingface_hub"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    logger.info("Weights directory: %s", weights_dir())
    weights_dir().mkdir(parents=True, exist_ok=True)

    for model in hf_models():
        if model.key in wanted:
            fetch_hf(model)
    if "rembg" in wanted:
        fetch_rembg()
    logger.info("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
