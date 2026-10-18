"""Optional real CONCH adapter. Local checkpoint only; inference requires Slurm/CUDA."""

import csv
import importlib.metadata
import inspect
import itertools
import json
import os
from pathlib import Path
import re
import time

import numpy as np
from PIL import Image

from .artifacts import Slide, TextEmbeddings, normalize, write_json
from .experiments import file_sha256, read_config
from .scoring import ensemble_prompts


def preprocessing_signature(preprocess):
    # Callable addresses vary by process, although their transformations do not.
    return re.sub(r" at 0x[0-9a-fA-F]+(?=>)", "", repr(preprocess))


def check_interface(model):
    if not hasattr(model, "encode_image") or not hasattr(model, "encode_text"):
        raise ValueError("CONCH requires both image and text encoders")
    image_args = inspect.signature(model.encode_image).parameters
    text_args = inspect.signature(model.encode_text).parameters
    if not {"proj_contrast", "normalize"}.issubset(image_args) or "normalize" not in text_args:
        raise ValueError("Installed CONCH lacks the verified projected, normalized image/text interface")


def verify_encoder_weights(model_state, checkpoint_state):
    """Upstream loads non-strictly; reject a checkpoint missing active encoder weights."""
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
        self.model, self.preprocess = create_model_from_pretrained("conch_ViT-B-16", checkpoint_path=str(checkpoint), device="cuda")
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
        source_hash = file_sha256(source_file)
        self.provenance = {"name": "conch_v1", "revision": f"package:{version};source-sha256:{source_hash}",
            "checkpoint_sha256": file_sha256(checkpoint), "projection": True, "normalized": True,
            "preprocessing": preprocessing_signature(self.preprocess),
            "preprocessing_source_sha256": file_sha256(Path(inspect.getfile(create_model_from_pretrained)).with_name("transform.py")),
            "tokenizer_source_sha256": file_sha256(Path(inspect.getfile(get_tokenizer))),
            "torch_version": str(torch.__version__),
            "encoder_weight_coverage_verified": True}
        torch.cuda.synchronize()
        self.load_seconds = time.perf_counter() - started

    def encode_image_batch(self, batch):
        return self.model.encode_image(batch, proj_contrast=True, normalize=True)

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
                arrays.append(self.encode_image_batch(batch).detach().float().cpu().numpy())
        self.torch.cuda.synchronize()
        return np.concatenate(arrays), time.perf_counter() - started

    def texts(self, prompts):
        phrases = [phrase for group in prompts.values() for phrase in group]
        with self.torch.inference_mode():
            tokens = self.tokenize(texts=phrases, tokenizer=self.tokenizer).to("cuda")
            values = self.model.encode_text(tokens, normalize=True).detach().float().cpu().numpy()
        return ensemble_prompts(values, prompts)


def encode_tiles(tile_manifest, metadata_path, prompts_path, checkpoint, output, max_tiles=128, batch_size=16):
    if max_tiles < 1:
        raise ValueError("A positive explicit tile cap is required")
    manifest = Path(tile_manifest).resolve()
    with manifest.open(newline="") as handle:
        rows = list(itertools.islice(csv.DictReader(handle), max_tiles + 1))
    truncated = len(rows) > max_tiles
    rows = rows[:max_tiles]
    if not rows or not {"tile_id", "path", "x", "y"}.issubset(rows[0]):
        raise ValueError("Tile manifest requires tile_id,path,x,y and at least one row")
    ids = np.array([row["tile_id"] for row in rows])
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate tile identifiers")
    paths = [(manifest.parent / row["path"]).resolve() for row in rows]
    if not all(path.is_file() for path in paths):
        raise ValueError("Some tile files are unavailable; no encoding attempted")
    coords = np.array([[float(row["x"]), float(row["y"])] for row in rows])
    if not np.isfinite(coords).all():
        raise ValueError("Nonfinite tile coordinates")
    metadata = json.loads(Path(metadata_path).read_text())
    prompts = read_config(prompts_path)["prompts"]
    if not isinstance(prompts, dict) or len(prompts) < 2 or any(not isinstance(group, list) or not 3 <= len(group) <= 5
            or any(not isinstance(phrase, str) or not phrase.strip() for phrase in group) for group in prompts.values()):
        raise ValueError("Define 3-5 fixed nonempty phrases for each of at least two classes")
    output = Path(output)
    if output.exists():
        raise FileExistsError("Choose a new output directory; existing artifacts are preserved")
    encoder = ConchEncoder(checkpoint)
    feats, seconds = encoder.images(paths, batch_size)
    text_feats = encoder.texts(prompts)
    metadata.update(model=encoder.provenance, source_kind="real",
                    tile_selection={"method": "first manifest rows", "cap": max_tiles, "truncated": truncated,
                                    "tile_manifest_sha256": file_sha256(manifest)})
    slide = Slide(feats, coords, ids, metadata)
    text = TextEmbeddings(text_feats, list(prompts), prompts, encoder.provenance, "real")
    if slide.feats.shape[1] != text.feats.shape[1]:
        raise ValueError("CONCH image/text projection dimensions do not match")
    output.mkdir(parents=True, exist_ok=False)
    slide.save(output / "slide.npz")
    text.save(output / "text.npz")
    timing = {"category": "real-data encoding", "tiles": len(feats), "image_encoding_seconds": seconds,
              "model_load_seconds": encoder.load_seconds, "tiles_per_second": len(feats) / seconds,
              "timing_scope": "image I/O, specified preprocessing, GPU encoding and device transfers; excludes model load/text",
              "manifest_truncated": truncated, "model": encoder.provenance}
    write_json(output / "timing.json", timing)
    return {key: timing[key] for key in ("category", "tiles", "image_encoding_seconds", "tiles_per_second")}
