#!/usr/bin/env python3
"""Reuse verified embeddings for a two-direction, five-seed descriptive smoke."""

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import socket


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--prompts", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        parser.error("Run analysis inside Slurm")
    import yaml
    from conch.open_clip_custom.constants import OPENAI_DATASET_MEAN, OPENAI_DATASET_STD
    from conch.open_clip_custom.transform import image_transform
    from floater_finder.artifacts import TextEmbeddings, write_json
    from floater_finder.conch import preprocessing_signature
    from floater_finder.experiments import read_config, run_stress
    from floater_finder.reporting import load_rows, plot_rates

    source = Path(args.input).resolve()
    prior = json.loads((source / "smoke.json").read_text())
    if prior["status"] != "passed" or prior["failed_trials"]:
        raise ValueError("A completed, passing one-pair GPU smoke is required")
    text = TextEmbeddings.load(source / "host_encoded/text.npz")
    # Recreate the observed 448-pixel CONCH transform in this independent process.
    actual = preprocessing_signature(image_transform(448, mean=OPENAI_DATASET_MEAN, std=OPENAI_DATASET_STD))
    if actual != text.model["preprocessing"] or " at 0x" in actual:
        raise ValueError("Preprocessing provenance is not stable across processes")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    config = read_config(args.prompts)
    config.update(category="smoke", split="eval", text_embeddings=str(source / "host_encoded/text.npz"),
        pairs=[{"host": str(source / "host_encoded/slide.npz"), "donor": str(source / "donor_encoded/slide.npz")},
               {"host": str(source / "donor_encoded/slide.npz"), "donor": str(source / "host_encoded/slide.npz")}],
        seeds=list(range(5)), sampling_note="Two patients, each a host and reciprocal donor; connected 128-tile subsets; no independent detector calibration.")
    path = output / "run.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False))
    result = run_stress(path, output / "stress")
    if result["failed_trials"] or result["rows"] != 180:
        raise RuntimeError("Incomplete bidirectional smoke; stop before interpreting results")
    rows = load_rows(output / "stress")
    plot_rates(output / "stress", output / "contamination.png")
    report = {"status": "passed", "category": "smoke", "slurm_job_id": os.environ["SLURM_JOB_ID"],
        "hostname": socket.gethostname(), "source_gpu_job": prior["slurm_job_id"],
        "host_slides": 2, "distinct_patients": 2, "seeds": 5, "contamination_levels": 6,
        "rows": len(rows), "oracle_verified_trials": 60, "failed_trials": 0,
        "prediction_changes": sum(row["prediction_changed"] for row in rows),
        "cross_process_preprocessing_verified": True,
        "plot_matplotlib_version": importlib.metadata.version("matplotlib"),
        "limitations": config["sampling_note"],
        "interpretation": "Descriptive software/research smoke. Seeds and reciprocal directions are not independent additional patients."}
    write_json(output / "smoke.json", report)
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
