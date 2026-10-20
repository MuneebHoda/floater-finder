"""Frozen-protocol checks and development-only patient-separated selection."""

import csv
import json
from pathlib import Path

import numpy as np

from .artifacts import check_compatible, write_json
from .detection import VARIANTS, _check_calibration, _combine, _signals, calibrate, development_anomaly_scores
from .experiments import file_sha256
from .scoring import tile_scores


def frozen_protocol(project):
    project = Path(project)
    freeze = json.loads((project / "reports/conch_pilot_protocol_freeze_20261019.json").read_text())
    for key, digest in (("protocol", "protocol_sha256"), ("protocol_document", "protocol_document_sha256"),
                        ("verification", "verification_sha256")):
        if file_sha256(project / freeze[key]) != freeze[digest]:
            raise ValueError("Frozen protocol/document/verification hash mismatch")
    for relative, digest in freeze["source_sha256"].items():
        if file_sha256(project / relative) != digest:
            raise ValueError(f"Frozen base source changed: {relative}")
    config = json.loads((project / freeze["protocol"]).read_text())
    patients = config["slides"]
    dev = {s["patient_id"] for s in patients if s["split"] == "dev"}
    evaluation = {s["patient_id"] for s in patients if s["split"] == "eval"}
    if len(patients) != 18 or len(dev) != 10 or len(evaluation) != 8 or dev & evaluation or \
            set(config["evaluation"]["retired_evaluation_patients"]) & (dev | evaluation):
        raise ValueError("Frozen patient split/retirement contract violated")
    preflight_path = project / config["technical_validation"]["report"]
    if file_sha256(preflight_path) != config["technical_validation"]["report_sha256"]:
        raise ValueError("Technical preflight report changed")
    preflight = json.loads(preflight_path.read_text())
    if preflight["status"] != "passed" or {p["patient_id"] for p in preflight["patients"]} != dev | evaluation:
        raise ValueError("All frozen patients require passing technical preflight")
    return config, freeze, preflight


def omitted_development_scores(slide, text, calibration):
    """Score an original development patient excluded from this fold's calibration."""
    _check_calibration(slide, text, calibration)
    if slide.metadata["split"] != "dev" or slide.foreign_mask.any() or "injection" in slide.metadata or \
            slide.metadata["patient_id"] in calibration["development_patients"]:
        raise ValueError("LOPO scoring requires an omitted, unmodified development patient")
    return _combine(_signals(slide, text, calibration), slide, calibration)


def select_development(slides, text, detector, policy, output):
    """Use clean LOPO controls only; return no cutoff if any frozen constraint fails."""
    ids = [s.metadata["patient_id"] for s in slides]
    if len(slides) < 3 or len(set(ids)) != len(ids):
        raise ValueError("Distinct development patients are required")
    for slide in slides:
        check_compatible(slide, text)
        if slide.metadata["split"] != "dev" or slide.foreign_mask.any() or "injection" in slide.metadata:
            raise ValueError("Selection accepts only original, unmodified development patients")
    quantiles = policy["quantiles"]
    budget = policy["clean_host_removal_budget_per_patient"]
    if not quantiles or quantiles != sorted(set(quantiles)) or any(not 0 < q < 1 for q in quantiles) or not 0 <= budget < 1:
        raise ValueError("Ordered quantiles and a bounded removal budget are required")
    output = Path(output)
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    kwargs = {k:detector[k] for k in ("exclusion_mm", "smoothing_mm", "weight", "chunk_size")}
    rows = []
    for omitted in slides:
        patient = omitted.metadata["patient_id"]
        training = [s for s in slides if s.metadata["patient_id"] != patient]
        base = calibrate(training, text, quantile=quantiles[0], **kwargs)
        held_scores = omitted_development_scores(omitted, text, base)
        training_scores = [development_anomaly_scores(s, text, base) for s in training]
        fold = output / "folds" / patient
        write_json(fold / "base_calibration.json", base)
        np.savez_compressed(fold / "omitted_scores.npz", tile_ids=omitted.tile_ids, coords=omitted.coords,
                            class_scores=tile_scores(omitted, text), **held_scores)
        thresholds = []
        for q in quantiles:
            for variant in VARIANTS:
                value = float(np.quantile(np.concatenate([s[variant] for s in training_scores]), q, method="higher"))
                removed = int((held_scores[variant] > value).sum())
                n = len(omitted.feats)
                row = dict(omitted_patient=patient, quantile=q, variant=variant, threshold=value,
                           removed_tiles=removed, host_tiles=n, original_host_removal=removed/n,
                           within_budget=removed/n <= budget)
                rows.append(row)
                thresholds.append(row)
        write_json(fold / "thresholds_and_counts.json", thresholds)
    feasible = [q for q in quantiles if all(r["within_budget"] for r in rows if r["quantile"] == q)]
    selected = feasible[0] if feasible else None
    with (output / "selection.csv").open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    if selected is not None:
        final = calibrate(slides, text, quantile=selected, **kwargs)
        write_json(output / "final_calibration.json", final)
    return dict(status="passed" if selected is not None else "no_feasible_cutoff", selected_quantile=selected,
                feasible_quantiles=feasible, development_patients=sorted(ids), folds=len(slides),
                selection_rows=len(rows), controls=rows, clean_host_removal_budget_per_patient=budget,
                evaluation_artifacts_loaded=False, synthetic_trials_used_for_selection=False,
                source_kind=text.source_kind, final_calibration_written=selected is not None,
                interpretation="LOPO guides cutoff selection; not independent validation or a clinical false-positive guarantee.")
