#!/usr/bin/env python3
"""Scheduled encoding of the ten frozen development patients only."""

import argparse
import json
import os
from pathlib import Path
import socket


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        parser.error("Run development encoding inside Slurm")
    import torch
    from floater_finder.artifacts import Slide, TextEmbeddings, write_json
    from floater_finder.cohort import frozen_protocol
    from floater_finder.conch import encode_tiles
    from floater_finder.experiments import file_sha256
    from floater_finder.tiling import extract_tiles
    from ncsa_pilot_preflight import verify_input

    project = Path(__file__).resolve().parents[1]
    config, freeze, preflight = frozen_protocol(project)
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise ValueError("Exactly one scheduled CUDA GPU is required")
    torch.set_num_threads(4)
    torch.manual_seed(0)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    output = Path(args.output)
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    verify_input(config["checkpoint"])
    sampling = config["sampling"]
    n = sampling["window_count"] * sampling["tiles_per_window"]
    records, fingerprint = [], None
    for item in config["slides"]:
        if item["split"] != "dev":
            continue
        patient = item["patient_id"]
        verify_input(item)
        directory = output / patient
        tiled = extract_tiles(item, directory / "tiles", n, sampling["field_um"], sampling["export_pixels"],
                              windows=sampling["window_count"])
        expected = next(p for p in preflight["patients"] if p["patient_id"] == patient)
        if tiled["tiles"] != n or tiled["metadata"]["extraction"]["selected_physical_grid_cells"] != expected["selected_physical_cells"]:
            raise ValueError("Frozen preflight/extractor selection mismatch")
        encode_tiles(directory / "tiles/tiles.csv", directory / "tiles/metadata.json", project / freeze["protocol"],
                     config["checkpoint"]["path"], directory / "encoded", max_tiles=n, batch_size=16)
        slide = Slide.load(directory / "encoded/slide.npz")
        text = TextEmbeddings.load(directory / "encoded/text.npz")
        if slide.feats.shape != (n, 512) or text.model["checkpoint_sha256"] != config["checkpoint"]["checksum"]["value"] or text.model["pillow_version"] != "12.3.0":
            raise ValueError("Encoding shape/checkpoint/runtime differs from protocol")
        if fingerprint is not None and text.fingerprint() != fingerprint:
            raise ValueError("Repeated frozen text/model artifacts differ")
        fingerprint = text.fingerprint()
        record = dict(patient_id=patient, tiles=n, split="dev", slide_sha256=file_sha256(directory / "encoded/slide.npz"),
                      text_sha256=file_sha256(directory / "encoded/text.npz"), text_fingerprint=fingerprint)
        records.append(record)
        write_json(directory / "encoding.json", record)
        print(json.dumps(record), flush=True)
    if len(records) != 10:
        raise ValueError("Incomplete development cohort")
    write_json(output / "development_encoding.json", dict(status="passed", category="development encoding; no detector evaluation",
        slurm_job_id=os.environ["SLURM_JOB_ID"], hostname=socket.gethostname(), gpu=torch.cuda.get_device_name(0),
        protocol_sha256=freeze["protocol_sha256"], patients=records, total_tiles=sum(r["tiles"] for r in records),
        text_fingerprint=fingerprint, evaluation_patients_encoded=False, model=text.model))
    for p in [output, *output.rglob("*")]:
        p.chmod(p.stat().st_mode & ~0o077)
    print(json.dumps(dict(status="passed", patients=len(records), tiles=10*n)), flush=True)


if __name__ == "__main__":
    main()
