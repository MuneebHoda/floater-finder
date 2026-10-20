#!/usr/bin/env python3
"""Scheduled raw-header, coordinate, sampling and development-only pixel checks."""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import socket


def verify_input(item):
    path = Path(item["path"])
    if path.is_symlink() or not path.is_file() or path.stat().st_size != item["bytes"]:
        raise ValueError("Input identity/type/size mismatch")
    digest = hashlib.new(item["checksum"]["algorithm"])
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != item["checksum"]["value"]:
        raise ValueError("Input checksum mismatch")


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
    from floater_finder.artifacts import write_json
    from floater_finder.experiments import file_sha256
    from floater_finder.image_runtime import require_image_runtime
    from floater_finder.tiling import coordinate_candidates, extract_tiles, spatial_windows

    require_image_runtime()
    config = json.loads(Path(args.config).read_text())
    slides, sampling = config["slides"], config["sampling"]
    ids = {s["patient_id"] for s in slides}
    if len(ids) != len(slides) or len(ids) != 18 or not {s["split"] for s in slides} <= {"dev", "eval"}:
        raise ValueError("Expected 18 distinct declared development/evaluation patients")
    qc_ids = config["pixel_qc_patients"]
    if len(qc_ids) != 2 or not set(qc_ids) <= {s["patient_id"] for s in slides if s["split"] == "dev"}:
        raise ValueError("Pixel QC is restricted to two predeclared development patients")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    records = []
    for item in slides:
        record = {"patient_id": item["patient_id"], "split": item["split"], "path": item["path"],
                  "raw_header_verified": False, "coordinate_header_verified": False, "sampling_verified": False}
        try:
            verify_input(item)
            record.update(checksum=item["checksum"], bytes=item["bytes"])
            with openslide.OpenSlide(item["path"]) as slide, h5py.File(item["coordinate_h5"], "r") as handle:
                metadata, coords, cells, excluded, footprint = coordinate_candidates(
                    slide, handle["coords"], item["slide_id"], sampling["field_um"])
                record.update(raw_header_verified=True, coordinate_header_verified=True,
                    dimensions=list(slide.dimensions), measured_mpp_xy=metadata["measured_mpp_xy"],
                    objective_power=metadata["objective_power"], level_dimensions=list(slide.level_dimensions),
                    vendor=slide.properties.get("openslide.vendor"), coordinate_h5=item["coordinate_h5"],
                    coordinate_count=len(coords), coordinate_sha256=hashlib.sha256(coords.tobytes()).hexdigest(),
                    physical_candidate_cells=len(cells), out_of_bounds_cells_excluded=excluded,
                    source_footprint_level0=footprint, feature_values_read=False)
                np.save(output / (item["patient_id"] + "_candidates.npy"), cells, allow_pickle=False)
                selected, windows = spatial_windows(cells, sampling["window_count"], sampling["tiles_per_window"],
                                                     sampling["field_um"], sampling["min_gap_um"])
                record.update(sampling_verified=True, selected_tiles=len(selected), window_sampling=windows,
                    selected_physical_cells=cells[selected].tolist())
                np.save(output / (item["patient_id"] + "_selected.npy"), cells[selected], allow_pickle=False)
        except Exception as error:
            record.update(error_type=type(error).__name__, error=str(error))
        records.append(record)
        write_json(output / "patients" / (item["patient_id"] + ".json"), record)
        print(json.dumps({k:record[k] for k in ("patient_id", "raw_header_verified", "sampling_verified")}), flush=True)
    passed = all(r["sampling_verified"] for r in records)
    pixel_qc = []
    if passed:
        for item in slides:
            if item["patient_id"] not in qc_ids:
                continue
            try:
                result = extract_tiles(item, output / (item["patient_id"] + "_tiles"),
                    sampling["window_count"] * sampling["tiles_per_window"], sampling["field_um"],
                    sampling["export_pixels"], windows=sampling["window_count"])
                expected = next(r["selected_physical_cells"] for r in records if r["patient_id"] == item["patient_id"])
                if result["metadata"]["extraction"]["selected_physical_grid_cells"] != expected:
                    raise ValueError("Preflight/extractor sampling disagreement")
                pixel_qc.append({"patient_id":item["patient_id"], "tiles":result["tiles"], "status":"passed"})
            except Exception as error:
                passed = False
                pixel_qc.append({"patient_id":item["patient_id"], "status":"failed", "error_type":type(error).__name__, "error":str(error)})
    report = dict(status="passed" if passed else "failed", category="technical preflight; no scientific performance result",
        slurm_job_id=os.environ["SLURM_JOB_ID"], hostname=socket.gethostname(),
        input_config_sha256=file_sha256(args.config), patients=records, pixel_qc=pixel_qc,
        model_loaded=False, gpu_used=False, embeddings_created=False, feature_values_read=False,
        runtime={name:importlib.metadata.version(name) for name in ("numpy", "Pillow", "openslide-python", "openslide-bin", "h5py")},
        source_sha256={str(p.relative_to(Path(__file__).resolve().parents[1])):file_sha256(p) for p in [
            Path(__file__).resolve(), Path(__file__).resolve().parents[1]/"src/floater_finder/tiling.py"]})
    write_json(output / "preflight.json", report)
    for p in [output, *output.rglob("*")]:
        p.chmod(p.stat().st_mode & ~0o077)
    print(json.dumps({"status":report["status"], "patients":len(records), "output":str(output)}), flush=True)
    raise SystemExit(0 if passed else 2)


if __name__ == "__main__":
    main()
