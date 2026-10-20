#!/usr/bin/env python3
"""Compare newly encoded development artifacts with the preserved legacy runtime."""

import argparse
import json
import os
from pathlib import Path


def compare_arrays(before, after):
    import numpy as np
    if before.shape != after.shape:
        raise ValueError("Runtime comparison array shapes differ")
    return {"exactly_equal": bool(np.array_equal(before, after)),
        "maximum_absolute_difference": float(np.max(np.abs(before.astype(float) - after.astype(float)))),
        "close_at_1e_5": bool(np.allclose(before, after, atol=1e-5, rtol=1e-5))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--current", required=True)
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        parser.error("Run compatibility checks inside Slurm")
    import importlib.metadata
    import numpy as np
    from PIL import Image
    from floater_finder.artifacts import Slide, TextEmbeddings, write_json
    from floater_finder.experiments import file_sha256
    from floater_finder.image_runtime import require_image_runtime

    pillow = require_image_runtime()
    baseline, current = Path(args.baseline), Path(args.current)
    records, inputs = [], {}
    for role in ("dev_prostate", "dev_bladder"):
        old_path, new_path = [root / (role + "_encoded/slide.npz") for root in (baseline, current)]
        old, new = Slide.load(old_path), Slide.load(new_path)
        if old.metadata["split"] != "dev" or new.metadata["split"] != "dev" or old.metadata["patient_id"] != new.metadata["patient_id"]:
            raise ValueError("Compare matching development patients only")
        if new.feats.shape != (128, 512) or new.metadata["model"].get("pillow_version") != pillow:
            raise ValueError("Unexpected new artifact shape or Pillow provenance")
        legacy_model = {key: value for key, value in new.metadata["model"].items() if key != "pillow_version"}
        if legacy_model != old.metadata["model"]:
            raise ValueError("Model/checkpoint/transform provenance changed beyond the recorded Pillow version")
        if not np.array_equal(old.tile_ids, new.tile_ids) or not np.array_equal(old.coords, new.coords):
            raise ValueError("Physical tile selection/geometry differs")
        old_text_path, new_text_path = [path.with_name("text.npz") for path in (old_path, new_path)]
        old_text, new_text = TextEmbeddings.load(old_text_path), TextEmbeddings.load(new_text_path)
        if old_text.prompts != new_text.prompts or old_text.classes != new_text.classes:
            raise ValueError("Frozen prompt ensemble changed")
        unequal_tiles, maximum_pixel_delta = 0, 0
        for tile in old.tile_ids:
            paths = [root / (role + "_tiles") / (tile + ".png") for root in (baseline, current)]
            with Image.open(paths[0]) as first, Image.open(paths[1]) as second:
                a, b = np.asarray(first.convert("RGB")), np.asarray(second.convert("RGB"))
                if a.shape != b.shape:
                    raise ValueError("Export pixel geometry differs")
                unequal_tiles += int(not np.array_equal(a, b))
                maximum_pixel_delta = max(maximum_pixel_delta, int(np.max(np.abs(a.astype(np.int16) - b.astype(np.int16)))))
        for path in (old_path, new_path, old_text_path, new_text_path):
            inputs[str(path)] = file_sha256(path)
        records.append({"role": role, "patient_id": new.metadata["patient_id"], "tiles": len(new.feats),
            "image_embeddings": compare_arrays(old.feats, new.feats),
            "text_embeddings": compare_arrays(old_text.feats, new_text.feats),
            "tiles_with_changed_decoded_pixels": unequal_tiles, "maximum_rgb_pixel_difference": maximum_pixel_delta,
            "physical_geometry_equal": True, "model_equal_except_recorded_pillow_version": True})
    report = {"status": "passed", "category": "runtime_compatibility", "slurm_job_id": os.environ["SLURM_JOB_ID"],
        "baseline": str(baseline), "current": str(current), "packages": {name: importlib.metadata.version(name) for name in ("Pillow", "numpy", "torch", "torchvision", "conch")},
        "comparisons": records, "input_sha256": inputs, "workflow_sha256": file_sha256(__file__),
        "interpretation": "Execution and artifact checks passed. Pixel/vector differences are reported, not assumed absent. New Pillow provenance keeps new artifacts distinct from legacy artifacts; do not rewrite or silently mix them. No detector threshold or evaluation result selected."}
    write_json(current / "runtime_compatibility.json", report)
    print(json.dumps({"status": "passed", "slurm_job_id": os.environ["SLURM_JOB_ID"], "comparisons": records}), flush=True)


if __name__ == "__main__":
    main()
