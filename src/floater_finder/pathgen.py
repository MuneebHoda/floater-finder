"""Optional PathGen-CLIP adapter. Local checkpoint only; inference requires Slurm/CUDA."""

import importlib.metadata
import inspect
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
        raise ValueError("PathGen-CLIP requires both image and text encoders")


class PathGenClipEncoder:
    def __init__(self, checkpoint):
        if not os.environ.get("SLURM_JOB_ID"):
            raise RuntimeError("Real PathGen-CLIP encoding requires an authorized Slurm GPU job")
        checkpoint = Path(checkpoint).resolve()
        if not checkpoint.is_file():
            raise ValueError("Supply a verified, already-local PathGen-CLIP checkpoint file; downloads are disabled")
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
        import torch
        import open_clip

        if not torch.cuda.is_available():
            raise RuntimeError("No CUDA GPU visible; do not encode on a login node or CPU fallback")
        started = time.perf_counter()
        self.torch = torch
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            "ViT-B-16", pretrained=str(checkpoint))
        self.model = self.model.to("cuda")
        self.model.eval()
        check_interface(self.model)
        self.tokenizer = open_clip.get_tokenizer("ViT-B-32")
        source_file = Path(inspect.getfile(type(self.model)))
        try:
            version = importlib.metadata.version("open_clip_torch")
        except importlib.metadata.PackageNotFoundError:
            version = "source-checkout"
        self.provenance = {
            "name": "pathgen_clip_v1",
            "revision": f"open_clip_torch:{version};architecture:ViT-B-16;tokenizer:ViT-B-32;source-sha256:{file_sha256(source_file)}",
            "checkpoint_sha256": file_sha256(checkpoint),
            "projection": True,
            "normalized": True,
            "preprocessing": repr(self.preprocess),
            "torch_version": str(torch.__version__),
        }
        torch.cuda.synchronize()
        self.load_seconds = time.perf_counter() - started

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
            tokens = self.tokenizer(phrases).to("cuda")
            values = self.encode_text_batch(tokens).detach().float().cpu().numpy()
        return ensemble_prompts(normalize(values), prompts)

    def encode_image_batch(self, batch):
        return self.model.encode_image(batch)

    def encode_text_batch(self, batch):
        return self.model.encode_text(batch)


def encode_tiles(tile_manifest, metadata_path, prompts_path, checkpoint, output, max_tiles=128, batch_size=16):
    from .encoding import encode_tiles
    return encode_tiles(tile_manifest, metadata_path, prompts_path, checkpoint, output,
                        PathGenClipEncoder, max_tiles, batch_size)
