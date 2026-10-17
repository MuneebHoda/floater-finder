import numpy as np
import pytest

from floater_finder.artifacts import Slide, TextEmbeddings, normalize


MODEL = {"name": "unit-fixture", "revision": "fixture-v1", "checkpoint_sha256": "not-real-weights",
         "projection": True, "normalized": True, "preprocessing": "artificial arrays"}


def make_slide(name="host", n=100, organ="prostate", split="eval", feats=None, coords=None):
    if feats is None:
        feats = np.tile([1.0, 0.0] if organ == "prostate" else [0.0, 1.0], (n, 1))
    feats = normalize(np.asarray(feats, dtype=float))
    n = len(feats)
    if coords is None:
        coords = np.column_stack([np.arange(n), np.zeros(n)])
    metadata = {"slide_id": name, "patient_id": f"patient-{name}", "project": "FIXTURE",
                "organ": organ, "label": organ, "split": split, "source_kind": "fixture",
                "coordinate_units": "grid", "tile_step": [1, 1], "microns_per_unit": 1000,
                "model": MODEL.copy()}
    return Slide(feats, coords, np.array([f"tile-{i}" for i in range(n)]), metadata)


@pytest.fixture
def host():
    return make_slide()


@pytest.fixture
def donor():
    return make_slide("donor", organ="bladder")


@pytest.fixture
def text():
    return TextEmbeddings(np.eye(2), ["prostate", "bladder"],
                          {"prostate": ["fixture prostate"], "bladder": ["fixture bladder"]}, MODEL.copy(), "fixture")
