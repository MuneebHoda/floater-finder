"""Validated, pickle-free NPZ image/text artifacts with explicit model provenance."""

from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import json

import numpy as np


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        handle.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def normalize(values):
    values = np.asarray(values)
    if values.ndim != 2 or not np.isfinite(values).all():
        raise ValueError("Embeddings must be a finite [N,D] matrix")
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    if not np.all(norms > 0):
        raise ValueError("Zero-norm embeddings are invalid")
    return values / norms


def validate_features(feats, model):
    if not isinstance(model, dict):
        raise ValueError("Model provenance must be a mapping")
    if feats.ndim != 2 or min(feats.shape) == 0 or feats.dtype.kind != "f":
        raise ValueError("Expected nonempty floating-point [N,D] embeddings")
    if not np.isfinite(feats).all():
        raise ValueError("Nonfinite embeddings")
    for key in ("name", "revision", "checkpoint_sha256", "preprocessing"):
        if not isinstance(model.get(key), str) or not model[key].strip():
            raise ValueError(f"Missing model provenance: {key}")
    if model.get("projection") is not True or model.get("normalized") is not True:
        raise ValueError("Shared image/text space requires projection and normalization")
    if not np.allclose(np.linalg.norm(feats, axis=1), 1, atol=1e-4, rtol=1e-4):
        raise ValueError("Embeddings are not unit normalized")


@dataclass
class Slide:
    feats: np.ndarray
    coords: np.ndarray
    tile_ids: np.ndarray
    metadata: dict
    foreign_mask: np.ndarray = field(default=None)

    def __post_init__(self):
        self.feats = np.asarray(self.feats)
        if not isinstance(self.metadata, dict):
            raise ValueError("Slide metadata must be a mapping")
        validate_features(self.feats, self.metadata.get("model", {}))
        self.coords = np.asarray(self.coords, dtype=np.float64)
        raw_ids = np.asarray(self.tile_ids)
        if raw_ids.dtype.kind not in "US":
            raise ValueError("Tile IDs must be strings")
        self.tile_ids = raw_ids.astype(str)
        n = len(self.feats)
        if self.foreign_mask is None:
            self.foreign_mask = np.zeros(n, dtype=bool)
        else:
            self.foreign_mask = np.asarray(self.foreign_mask)
        if self.coords.shape != (n, 2) or not np.isfinite(self.coords).all():
            raise ValueError("Coordinates must be finite [N,2]")
        if self.tile_ids.shape != (n,) or len(set(self.tile_ids)) != n or np.any(self.tile_ids == ""):
            raise ValueError("Tile IDs must be unique, nonempty, and aligned")
        if self.foreign_mask.shape != (n,) or self.foreign_mask.dtype.kind != "b":
            raise ValueError("Foreign mask must be boolean and aligned")
        for key in ("slide_id", "patient_id", "project", "organ", "coordinate_units"):
            if not isinstance(self.metadata.get(key), str) or not self.metadata[key]:
                raise ValueError(f"Missing slide metadata: {key}")
        if self.metadata.get("split") not in {"dev", "eval"}:
            raise ValueError("Explicit patient split dev/eval is required")
        if self.metadata.get("source_kind") not in {"real", "fixture"}:
            raise ValueError("source_kind must be real or fixture")
        if self.metadata["source_kind"] == "real":
            digest = self.metadata["model"]["checkpoint_sha256"]
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError("Real artifacts require an actual checkpoint SHA-256")
        for key in ("microns_per_unit",):
            value = self.metadata.get(key)
            if value is not None and (not np.isfinite(value) or value <= 0):
                raise ValueError(f"Invalid physical scale: {key}")
        json.dumps(self.metadata, allow_nan=False)

    def subset(self, keep, metadata=None):
        return Slide(self.feats[keep], self.coords[keep], self.tile_ids[keep],
                     self.metadata.copy() if metadata is None else metadata, self.foreign_mask[keep])

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            np.savez_compressed(handle, feats=self.feats, coords=self.coords, tile_ids=self.tile_ids,
                                foreign_mask=self.foreign_mask, metadata=json.dumps(self.metadata, allow_nan=False))

    @classmethod
    def load(cls, path):
        with np.load(path, allow_pickle=False) as data:
            return cls(data["feats"], data["coords"], data["tile_ids"], json.loads(str(data["metadata"].item())),
                       data["foreign_mask"] if "foreign_mask" in data else None)


@dataclass
class TextEmbeddings:
    feats: np.ndarray
    classes: list
    prompts: dict
    model: dict
    source_kind: str

    def __post_init__(self):
        self.feats = np.asarray(self.feats)
        validate_features(self.feats, self.model)
        if len(self.classes) != len(self.feats) or len(set(self.classes)) != len(self.classes) or len(self.classes) < 2 or any(not isinstance(value, str) or not value for value in self.classes):
            raise ValueError("At least two unique, aligned classes required")
        if set(self.prompts) != set(self.classes) or any(not self.prompts[c] for c in self.classes):
            raise ValueError("Exact prompt provenance required for every class")
        if self.source_kind not in {"real", "fixture"}:
            raise ValueError("Invalid text source_kind")
        if self.source_kind == "real" and any(not 3 <= len(self.prompts[name]) <= 5 for name in self.classes):
            raise ValueError("Real prompt ensembles require 3-5 fixed phrases per class")

    def fingerprint(self):
        content = json.dumps({"classes": self.classes, "prompts": self.prompts, "model": self.model}, sort_keys=True)
        return hashlib.sha256(content.encode() + self.feats.tobytes()).hexdigest()

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata = dict(classes=self.classes, prompts=self.prompts, model=self.model, source_kind=self.source_kind)
        with path.open("xb") as handle:
            np.savez_compressed(handle, feats=self.feats, metadata=json.dumps(metadata, allow_nan=False))

    @classmethod
    def load(cls, path):
        with np.load(path, allow_pickle=False) as data:
            return cls(data["feats"], **json.loads(str(data["metadata"].item())))


def check_compatible(slide, other):
    other_model = other.model if isinstance(other, TextEmbeddings) else other.metadata["model"]
    other_kind = other.source_kind if isinstance(other, TextEmbeddings) else other.metadata["source_kind"]
    if slide.metadata["model"] != other_model or slide.feats.shape[1] != other.feats.shape[1]:
        raise ValueError("Embedding model/revision/preprocessing/dimension mismatch")
    if slide.metadata["source_kind"] != other_kind:
        raise ValueError("Cannot mix fixture and real embeddings")
