#!/usr/bin/env python3
"""Scheduled frozen-protocol LOPO selection; never open evaluation artifacts."""

import argparse
import json
import os
from pathlib import Path
import platform
import socket


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        parser.error("Run development selection inside Slurm")
    import numpy as np
    from floater_finder.artifacts import Slide, TextEmbeddings, write_json
    from floater_finder.cohort import frozen_protocol, select_development
    from floater_finder.experiments import file_sha256

    project = Path(__file__).resolve().parents[1]
    config, freeze, preflight = frozen_protocol(project)
    root = Path(args.development)
    encoding = json.loads((root / "development_encoding.json").read_text())
    expected = {s["patient_id"]:s for s in config["slides"] if s["split"] == "dev"}
    if encoding["status"] != "passed" or encoding["protocol_sha256"] != freeze["protocol_sha256"] or \
            len(encoding["patients"]) != 10 or {p["patient_id"] for p in encoding["patients"]} != set(expected):
        raise ValueError("Complete frozen development encoding required")
    slides, text, input_hashes = [], None, {}
    for record in encoding["patients"]:
        patient = record["patient_id"]
        slide_path, text_path = [root / patient / "encoded" / name for name in ("slide.npz", "text.npz")]
        for path, key in ((slide_path,"slide_sha256"), (text_path,"text_sha256")):
            digest = file_sha256(path)
            if digest != record[key]:
                raise ValueError("Development artifact changed")
            input_hashes[str(path)] = digest
        slide = Slide.load(slide_path)
        candidate = TextEmbeddings.load(text_path)
        item = expected[patient]
        cells = next(p["selected_physical_cells"] for p in preflight["patients"] if p["patient_id"] == patient)
        if slide.metadata["patient_id"] != patient or slide.metadata["split"] != "dev" or slide.metadata["organ"] != item["organ"] or \
                slide.metadata["source_kind"] != "real" or slide.feats.shape != (384,512) or \
                not np.array_equal(slide.coords, np.asarray(cells)*config["sampling"]["field_um"]):
            raise ValueError("Development identity/split/geometry mismatch")
        if candidate.prompts != config["prompts"] or candidate.source_kind != "real" or candidate.model["name"] != "conch_v1" or \
                candidate.model["checkpoint_sha256"] != config["checkpoint"]["checksum"]["value"] or \
                candidate.model["pillow_version"] != "12.3.0" or candidate.fingerprint() != encoding["text_fingerprint"]:
            raise ValueError("Frozen prompt/model/runtime mismatch")
        text = candidate
        slides.append(slide)
    output = Path(args.output)
    report = select_development(slides, text, config["detector"], config["threshold_selection"], output)
    report.update(slurm_job_id=os.environ["SLURM_JOB_ID"], hostname=socket.gethostname(),
        protocol_sha256=freeze["protocol_sha256"], input_sha256=input_hashes, model=text.model,
        text_fingerprint=text.fingerprint(), runtime=dict(python=platform.python_version(),numpy=np.__version__),
        source_sha256={str(p.relative_to(project)):file_sha256(p) for p in [Path(__file__),project/"src/floater_finder/cohort.py"]})
    write_json(output / "selection.json", report)
    if report["selected_quantile"] is not None:
        write_json(output / "calibration_freeze.json", dict(protocol_sha256=freeze["protocol_sha256"],
            calibration_sha256=file_sha256(output / "final_calibration.json"), selection_sha256=file_sha256(output / "selection.json"),
            development_input_sha256=input_hashes, text_fingerprint=text.fingerprint(), source_sha256=report["source_sha256"],
            scope="Final development-only numerical calibration; held-out scoring may not refit or select settings."))
    for p in [output, *output.rglob("*")]:
        p.chmod(p.stat().st_mode & ~0o077)
    print(json.dumps({k:report[k] for k in ("status","selected_quantile","folds","selection_rows")}), flush=True)


if __name__ == "__main__":
    main()
