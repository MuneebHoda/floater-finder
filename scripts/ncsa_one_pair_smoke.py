#!/usr/bin/env python3
"""Scheduled raw-WSI tiling, matched CONCH v1 encoding and one-pair oracle smoke."""

import argparse
import json
import os
from pathlib import Path
import socket


def validate_pair_config(config):
    mode = config.get("mode")
    if mode not in {None, "calibration"}:
        raise ValueError("Unknown encoding mode")
    slides = config["slides"]
    split = "dev" if mode == "calibration" else "eval"
    if len(slides) != 2 or len({item["patient_id"] for item in slides}) != 2 or any(item["split"] != split for item in slides):
        raise ValueError("Two distinct patients in the correct dev/eval split are required")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--prompts", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        parser.error("Run only inside an authorized Slurm GPU job")
    import numpy as np
    import torch
    import yaml
    from floater_finder.artifacts import Slide, TextEmbeddings, write_json
    from floater_finder.conch import encode_tiles
    from floater_finder.experiments import file_sha256, read_config, run_stress
    from floater_finder.scoring import predictions, tile_scores
    from floater_finder.tiling import extract_tiles

    config = json.loads(Path(args.config).read_text())
    validate_pair_config(config)
    if config["category"] != "smoke" or len(config["slides"]) != 2 or not torch.cuda.is_available():
        raise ValueError("This run requires one pair, smoke category and a visible CUDA GPU")
    if config["max_tiles_per_slide"] > 128:
        raise ValueError("This smoke is capped at 128 tiles per slide")
    torch.set_num_threads(4)
    torch.manual_seed(0)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    geometry = []
    for item in config["slides"]:
        tiled = extract_tiles(item, output / (item["role"] + "_tiles"), config["max_tiles_per_slide"],
                              config["field_um"], config["export_pixels"])
        geometry.append(tiled["metadata"])
    for key in ("coordinate_units", "microns_per_unit", "tile_step"):
        if geometry[0][key] != geometry[1][key]:
            raise ValueError("Host/donor physical resampling mismatch")
    for item in config["slides"]:
        role = item["role"]
        encode_tiles(output / (role + "_tiles/tiles.csv"), output / (role + "_tiles/metadata.json"),
                     args.prompts, config["checkpoint"]["path"], output / (role + "_encoded"),
                     config["max_tiles_per_slide"], config["batch_size"])
    if config.get("mode") == "calibration":
        write_json(output / "smoke.json", {"status": "passed", "category": "clean calibration encoding",
            "slurm_job_id": os.environ["SLURM_JOB_ID"], "hostname": socket.gethostname(),
            "gpu": torch.cuda.get_device_name(0), "patients": [item["patient_id"] for item in config["slides"]],
            "roles": [item["role"] for item in config["slides"]], "model_loaded": True,
            "input_config_sha256": file_sha256(args.config), "prompts_sha256": file_sha256(args.prompts)})
        print(json.dumps({"status": "passed", "output": str(output), "mode": "clean calibration encoding"}), flush=True)
        return
    host = Slide.load(output / "host_encoded/slide.npz")
    donor = Slide.load(output / "donor_encoded/slide.npz")
    text = TextEmbeddings.load(output / "host_encoded/text.npz")
    donor_text = TextEmbeddings.load(output / "donor_encoded/text.npz")
    if text.fingerprint() != donor_text.fingerprint():
        raise RuntimeError("Repeated text encoding differs; stop before contamination")
    for role, slide in (("host", host), ("donor", donor)):
        np.savez_compressed(output / (role + "_raw_scores.npz"), tile_ids=slide.tile_ids,
                            class_scores=tile_scores(slide, text), classes=np.asarray(text.classes))
    stress = read_config(args.prompts)
    stress.update(category="smoke", split="eval", text_embeddings="host_encoded/text.npz",
                  pairs=[{"host": "host_encoded/slide.npz", "donor": "donor_encoded/slide.npz"}])
    stress_path = output / "stress_config.yaml"
    stress_path.write_text(yaml.safe_dump(stress, sort_keys=False))
    result = run_stress(stress_path, output / "stress")
    if result["failed_trials"] or result["rows"] != 18:
        raise RuntimeError("Incomplete one-pair stress smoke; inspect failures before continuing")
    report = {"status": "passed", "category": "smoke", "slurm_job_id": os.environ["SLURM_JOB_ID"],
        "hostname": socket.gethostname(), "gpu": torch.cuda.get_device_name(0),
        "cuda_version": torch.version.cuda, "precision": "float32; TF32 disabled; no autocast",
        "host_tiles": len(host.feats), "donor_tiles": len(donor.feats),
        "embedding_dimensions": host.feats.shape[1], "checkpoint": config["checkpoint"],
        "conch_source_revision": config["conch_source_revision"],
        "input_config_sha256": file_sha256(args.config), "prompts_sha256": file_sha256(args.prompts),
        "host_prediction": predictions(host, text), "donor_prediction": predictions(donor, text),
        "oracle_verified_trials": 6, "stress_rows": result["rows"], "failed_trials": 0,
        "limitations": ["One pair, connected 128-tile subsets; not full slides or a population benchmark.",
                        "No independent development cohort or detector calibration in this run.",
                        "Synthetic embedding-level contamination, not confirmed real floaters.",
                        "Clinical reports and a verified institution match are unavailable."]}
    write_json(output / "smoke.json", report)
    print(json.dumps({"status": "passed", "output": str(output), "stress_rows": result["rows"]}), flush=True)


if __name__ == "__main__":
    main()
