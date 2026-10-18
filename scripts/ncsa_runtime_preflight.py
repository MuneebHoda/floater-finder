#!/usr/bin/env python3
"""Scheduled input-integrity, WSI-header and tokenizer checks; never load a model."""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import socket


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        parser.error("Run preflight inside Slurm")
    import h5py
    import numpy as np
    import openslide
    from conch.open_clip_custom import get_tokenizer, tokenize
    from floater_finder.artifacts import write_json

    config = json.loads(Path(args.config).read_text())
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    inspected = []
    for item in config["slides"] + [config["checkpoint"]]:
        path = Path(item["path"])
        digest = hashlib.new(item["checksum"]["algorithm"])
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        if path.stat().st_size != item["bytes"] or digest.hexdigest() != item["checksum"]["value"]:
            raise ValueError("Input size/checksum mismatch")
        record = {"path": str(path), "bytes": path.stat().st_size, "checksum": item["checksum"]}
        if item.get("patient_id"):
            with openslide.OpenSlide(path) as slide:
                record.update(dimensions=list(slide.dimensions),
                              level_dimensions=list(slide.level_dimensions),
                              level_downsamples=list(slide.level_downsamples),
                              properties={key: slide.properties.get(key) for key in (
                                  "openslide.mpp-x", "openslide.mpp-y", "openslide.objective-power", "openslide.vendor")})
            with h5py.File(item["coordinate_h5"], "r") as handle:
                dataset = handle["coords"]
                if dataset.shape[0] > 20000 or dataset.shape[1:] != (2,):
                    raise ValueError("Unexpected coordinate dataset")
                coords = dataset[:]
                if coords.dtype.kind not in "iu" or len(np.unique(coords, axis=0)) != len(coords):
                    raise ValueError("Coordinates must be unique integers")
                attrs = dataset.attrs
                if attrs["name"] != path.stem or [int(attrs["level0_width"]), int(attrs["level0_height"])] != record["dimensions"]:
                    raise ValueError("Coordinate source and WSI identity/dimensions do not match")
                record.update(coordinate_h5=item["coordinate_h5"], coordinate_count=len(coords),
                              coordinate_step=int(attrs["patch_size_level0"]),
                              source_patch_pixels=int(attrs["patch_size"]),
                              target_magnification=float(attrs["target_magnification"]),
                              coordinate_sha256=hashlib.sha256(coords.tobytes()).hexdigest(),
                              feature_values_read=False)
                np.save(output / (item["role"] + "_coords.npy"), coords, allow_pickle=False)
        inspected.append(record)
    tokens = tokenize(tokenizer=get_tokenizer(), texts=["a histopathology image of prostate tissue"])
    if tuple(tokens.shape) != (1, 128):
        raise ValueError("Unexpected tokenizer shape")
    packages = {name: importlib.metadata.version(name) for name in (
        "torch", "torchvision", "numpy", "Pillow", "PyYAML", "timm", "transformers", "conch", "openslide-python", "openslide-bin")}
    write_json(output / "preflight.json", {"slurm_job_id": os.environ["SLURM_JOB_ID"],
               "hostname": socket.gethostname(), "packages": packages, "inputs": inspected,
               "tokenizer_shape": list(tokens.shape), "model_loaded": False,
               "conch_source_revision": config["conch_source_revision"], "status": "passed"})
    print(json.dumps({"status": "passed", "output": str(output), "model_loaded": False}), flush=True)


if __name__ == "__main__":
    main()
