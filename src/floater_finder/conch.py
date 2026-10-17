"""Optional real CONCH adapter. Local checkpoint only; inference requires Slurm/CUDA."""

import csv
import importlib.metadata
import inspect
import itertools
import json
import os
from pathlib import Path
import time

import numpy as np
from PIL import Image

from .artifacts import normalize
from .experiments import file_sha256
from .scoring import ensemble_prompts


def check_interface(model):
    if not callable(getattr(model, "encode_image", None)) or not callable(getattr(model, "encode_text", None)):
        raise ValueError("CONCH requires both image and text encoders")
    image_args = inspect.signature(model.encode_image).parameters
    text_args = inspect.signature(model.encode_text).parameters
    if not {"proj_contrast", "normalize"}.issubset(image_args) or "normalize" not in text_args:
        raise ValueError("Installed CONCH lacks the projected, normalized image/text interface")


def verify_encoder_weights(model_state, checkpoint_state):
    if not isinstance(checkpoint_state, dict):
        raise ValueError("Checkpoint must be a state dictionary")
    state = checkpoint_state.get("state_dict", checkpoint_state)
    if not isinstance(state, dict) or not state:
        raise ValueError("Checkpoint must contain a nonempty model state dictionary")
    if all(key.startswith("module.") for key in state):
        state = {key.removeprefix("module."): value for key, value in state.items()}
    required = {key for key in model_state if not key.startswith("text_decoder.")}
    if not required:
        raise ValueError("No active encoder parameters were found")
    missing = required - set(state)
    if missing:
        raise ValueError(f"Checkpoint lacks {len(missing)} required encoder parameters/buffers")
    if any(tuple(model_state[key].shape) != tuple(state[key].shape) for key in required):
        raise ValueError("Checkpoint encoder tensor shapes do not match the installed architecture")


class ConchEncoder:
    def __init__(self, checkpoint):
        if not os.environ.get("SLURM_JOB_ID"):
            raise RuntimeError("Real CONCH encoding requires an authorized Slurm GPU job")
        checkpoint = Path(checkpoint).resolve()
        if not checkpoint.is_file():
            raise ValueError("Supply a verified, already-local CONCH checkpoint file; downloads are disabled")
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
        import torch
        from conch.open_clip_custom import create_model_from_pretrained, get_tokenizer, tokenize

        if not torch.cuda.is_available():
            raise RuntimeError("No CUDA GPU visible; do not encode on a login node or CPU fallback")
        started = time.perf_counter()
        self.torch = torch
        self.model, self.preprocess = create_model_from_pretrained(
            "conch_ViT-B-16", checkpoint_path=str(checkpoint), device="cuda")
        self.model.eval()
        check_interface(self.model)
        state = torch.load(checkpoint, map_location="cpu", weights_only=True)
        verify_encoder_weights(self.model.state_dict(), state)
        del state
        self.tokenizer, self.tokenize = get_tokenizer(), tokenize
        source_file = Path(inspect.getfile(type(self.model)))
        try:
            version = importlib.metadata.version("conch")
        except importlib.metadata.PackageNotFoundError:
            version = "source-checkout"
        self.provenance = {
            "name": "conch_v1",
            "revision": f"package:{version};source-sha256:{file_sha256(source_file)}",
            "checkpoint_sha256": file_sha256(checkpoint),
            "projection": True,
            "normalized": True,
            "preprocessing": repr(self.preprocess),
            "torch_version": str(torch.__version__),
            "encoder_weight_coverage_verified": True,
        }
        torch.cuda.synchronize()
        self.load_seconds = time.perf_counter() - started

    def encode_image_batch(self, batch):
        return self.model.encode_image(batch, proj_contrast=True, normalize=True)

    def encode_text_batch(self, batch):
        return self.model.encode_text(batch, normalize=True)

    def images(self, paths, batch_size):
        if not isinstance(batch_size, int) or batch_size < 1:
            raise ValueError("Positive batch size required")
        arrays = []
        self.torch.cuda.synchronize()
        started = time.perf_counter()
        with self.torch.inference_mode():
            for start in range(0, len(paths), batch_size):
                tensors = []
                for path in paths[start:start + batch_size]:
                    with Image.open(path) as image:
                        tensors.append(self.preprocess(image.convert("RGB")))
                batch = self.torch.stack(tensors).to("cuda")
                values = self.encode_image_batch(batch).detach().float().cpu().numpy()
                arrays.append(normalize(values))
        self.torch.cuda.synchronize()
        return np.concatenate(arrays), time.perf_counter() - started

    def texts(self, prompts):
        phrases = [phrase for group in prompts.values() for phrase in group]
        with self.torch.inference_mode():
            tokens = self.tokenize(texts=phrases, tokenizer=self.tokenizer).to("cuda")
            values = self.encode_text_batch(tokens).detach().float().cpu().numpy()
        return ensemble_prompts(normalize(values), prompts)


def encode_tiles(tile_manifest, metadata_path, prompts_path, checkpoint, output, max_tiles=128, batch_size=16):
    from .encoding import encode_tiles
    return encode_tiles(tile_manifest, metadata_path, prompts_path, checkpoint, output,
                        ConchEncoder, max_tiles, batch_size)
