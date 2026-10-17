"""Shared tile-manifest validation and artifact writing for model adapters."""

import csv
import itertools
import json
from pathlib import Path

import numpy as np

from .artifacts import Slide, TextEmbeddings, write_json
from .experiments import file_sha256, read_config


def encode_tiles(tile_manifest, metadata_path, prompts_path, checkpoint, output, encoder_type,
                 max_tiles=128, batch_size=16):
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
    encoder = encoder_type(checkpoint)
    feats, seconds = encoder.images(paths, batch_size)
    text_feats = encoder.texts(prompts)
    metadata.update(model=encoder.provenance, source_kind="real",
                    tile_selection={"method": "first manifest rows", "cap": max_tiles, "truncated": truncated,
                                    "tile_manifest_sha256": file_sha256(manifest)})
    slide = Slide(feats, coords, ids, metadata)
    text = TextEmbeddings(text_feats, list(prompts), prompts, encoder.provenance, "real")
    if slide.feats.shape[1] != text.feats.shape[1]:
        raise ValueError(f"{encoder.provenance['name']} image/text embedding dimensions do not match")
    output.mkdir(parents=True, exist_ok=False)
    slide.save(output / "slide.npz")
    text.save(output / "text.npz")
    timing = {"category": "real-data encoding", "tiles": len(feats), "image_encoding_seconds": seconds,
              "model_load_seconds": encoder.load_seconds, "tiles_per_second": len(feats) / seconds,
              "timing_scope": "image I/O, specified preprocessing, GPU encoding and device transfers; excludes model load/text",
              "manifest_truncated": truncated, "model": encoder.provenance}
    write_json(output / "timing.json", timing)
    return {key: timing[key] for key in ("category", "tiles", "image_encoding_seconds", "tiles_per_second")}
