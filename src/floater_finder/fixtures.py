"""Artificial arrays for software checks only, never model or cohort evidence."""

from pathlib import Path
import numpy as np
import yaml

from .artifacts import Slide, TextEmbeddings, normalize, write_json


def create_fixture(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    model = {"name": "unit-fixture", "revision": "fixture-v1", "checkpoint_sha256": "not-real-weights",
             "projection": True, "normalized": True, "preprocessing": "artificial arrays, no image encoding"}
    rng = np.random.default_rng(2026)
    for name, organ, split in (("host", "prostate", "eval"), ("donor", "bladder", "eval"),
                                ("dev", "prostate", "dev"), ("clean_eval", "prostate", "eval")):
        center = [1., .05] if organ == "prostate" else [.05, 1.]
        feats = normalize(np.asarray(center) + rng.uniform(-.01, .01, (100, 2)))
        coords = np.array([(x, y) for y in range(10) for x in range(10)])
        metadata = {"slide_id": f"fixture-{name}", "patient_id": f"fixture-patient-{name}",
            "project": "ARTIFICIAL-UNIT-FIXTURE", "organ": organ, "label": organ, "split": split,
            "source_kind": "fixture", "coordinate_units": "grid", "tile_step": [1, 1],
            "microns_per_unit": 1000, "scale_provenance": "artificial test scale, not a measured tissue scale", "model": model}
        Slide(feats, coords, np.array([f"fixture-tile-{i}" for i in range(100)]), metadata).save(output / f"{name}.npz")
    prompts = {name: [f"fixture-only {name} phrase {index}" for index in range(3)] for name in ("prostate", "bladder")}
    TextEmbeddings(np.eye(2), list(prompts), prompts, model, "fixture").save(output / "text.npz")
    config = {"category": "fixture", "split": "eval", "text_embeddings": "text.npz",
              "pairs": [{"host": "host.npz", "donor": "donor.npz"}],
              "contamination_percent": [0, .5, 1, 2, 5, 10], "seeds": [0, 1]}
    (output / "run.yaml").write_text(yaml.safe_dump(config, sort_keys=False))
    write_json(output / "NOTICE.json", {"category": "fixture", "real_model_used": False,
        "notice": "Artificial arrays and identities. No scientific performance conclusions are supported."})
    return {"category": "fixture", "output": str(output), "real_model_used": False}
