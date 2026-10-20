#!/usr/bin/env python3
"""Bounded CPU audit and sampling profile of the existing three PANDA inputs."""
import argparse
import csv
import json
import os
from pathlib import Path
import socket
import time
import zipfile

from floater_finder.artifacts import write_json
from floater_finder.experiments import file_sha256
from floater_finder.panda import extract_panda_tiles, panda_input, panda_readers
from floater_finder.panda_masks import audit_mask, save_mask_overlay


def run(root, output):
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Run the real-data profile only in Slurm")
    root, output = Path(root), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    before = {p: file_sha256(root/p) for p in ("pilot.csv", "annotated_cohort.csv", "train.csv")}
    mask_id = "55d91c32710982de78a975ed0f45395c"
    destination = root / "train_label_masks" / (mask_id + "_mask.tiff")
    archive = root / (mask_id + "_mask.tiff.zip")
    restored = None
    if not destination.exists() and archive.is_file():
        with zipfile.ZipFile(archive) as handle:
            members = handle.infolist()
            if len(members) != 1 or members[0].filename != destination.name or members[0].file_size > 10_000_000:
                raise ValueError("Unexpected local mask archive")
            data = handle.read(members[0])  # Zip CRC is checked by read().
        with destination.open("xb") as handle:
            handle.write(data)
        restored = {"path": str(destination), "bytes": destination.stat().st_size,
                    "sha256": file_sha256(destination), "archive_sha256": file_sha256(archive),
                    "source": "existing local ZIP; CRC verified; no network download"}
    ids = ["afe7eb15c8438861ca43f2b20dccf260", mask_id, "dd1110c6430e3b1ac732be548a089886"]
    records = []
    for image_id in ids:
        started = time.perf_counter()
        item = panda_input(root, image_id, root / "annotated_cohort.csv")
        record = {"image_id": image_id, "isup_grade": item["isup_grade"], "source_kind": "real"}
        with panda_readers(item["image_path"], item["mask_path"]) as (image, mask, meta):
            record["reader"] = meta
            if mask is not None:
                record["mask_audit"] = audit_mask(mask, meta["measured_mpp_xy"])
                save_mask_overlay(image, mask, output / (image_id + "-overlay.png"))
        for mode in (["representative", "donor"] if item["isup_grade"] >= 4 else ["representative"]):
            destination = output / image_id / mode
            result = extract_panda_tiles(root, image_id, destination, max_tiles=512,
                max_candidates=20000, manifest_path=root / "annotated_cohort.csv", selection=mode)
            with (destination / "tiles.csv").open() as handle:
                rows = list(csv.DictReader(handle))
            record[mode] = {"tiles": len(rows), "gp45_positive_tiles": sum(
                float(r["gleason4_fraction"] or 0) + float(r["gleason5_fraction"] or 0) > 0 for r in rows),
                "png_bytes": sum(p.stat().st_size for p in destination.glob("*.png")),
                "manifest_sha256": file_sha256(destination / "tiles.csv"),
                "metadata_sha256": file_sha256(destination / "metadata.json"),
                "png_sha256": {p.name: file_sha256(p) for p in sorted(destination.glob("*.png"))},
                "extraction": result["metadata"]["extraction"]}
        record["seconds"] = time.perf_counter() - started
        records.append(record)
        write_json(output / (image_id + "-profile.json"), record)
    assert all(file_sha256(root/p) == h for p, h in before.items()), "Original manifests changed"
    report = {"source_kind": "real", "category": "CPU engineering profile; no cancer scorer evaluation",
        "slurm_job_id": os.environ["SLURM_JOB_ID"], "host": socket.gethostname(),
        "restored_mask": restored, "preserved_manifest_sha256": before, "slides": records,
        "gpu_inference_run": False, "downloaded_dataset_bytes": 0}
    write_json(output / "profile.json", report)
    print(json.dumps({"status": "completed", "slides": len(records), "output": str(output)}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.root, args.output)
