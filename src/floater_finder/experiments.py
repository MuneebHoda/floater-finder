"""Trial-level scores and per-seed, per-host slide denominators."""

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import csv
import hashlib
import json
import subprocess

import numpy as np
import yaml

from .artifacts import Slide, TextEmbeddings, check_compatible, write_json
from .injection import inject, verify_oracle
from .scoring import POOLING, predictions

CATEGORIES = ("fixture", "smoke", "pilot", "benchmark")
SUPPORTED_REAL_MODELS = {"conch_v1", "pathgen_clip_v1"}


def read_config(path):
    with Path(path).open() as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError("Configuration must be a mapping")
    return value


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summarize(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["pooling"], row["requested_percent"], row["seed"])].append(row)
    summary = []
    for (rule, percent, seed), group in sorted(grouped.items()):
        if len({row["host_slide_id"] for row in group}) != len(group):
            raise ValueError("A host may appear only once within a percent/seed/pooling stratum")
        eligible = [row for row in group if row["original_correct"]]
        flips = sum(row["prediction_changed"] for row in eligible)
        summary.append({"pooling": rule, "requested_percent": percent, "seed": seed,
            "eligible_flips": flips, "eligible_slides": len(eligible), "all_slides": len(group),
            "eligible_flip_rate": flips / len(eligible) if eligible else None,
            "raw_prediction_change_rate": sum(row["prediction_changed"] for row in group) / len(group),
            "denominator_unit": "unique host slides within this seed; one donor per host"})
    return summary


def run_stress(config_path, output):
    config = read_config(config_path)
    category = config.get("category")
    if category not in CATEGORIES:
        raise ValueError("Explicit fixture/smoke/pilot/benchmark category required")
    if config.get("split") not in {"dev", "eval"}:
        raise ValueError("Explicit dev/eval run split required")
    if not isinstance(config.get("text_embeddings"), str) or not config.get("pairs"):
        raise ValueError("Supply verified text_embeddings and host/donor artifact pairs; this template is not ready for a real run")
    base = Path(config_path).resolve().parent
    text_path = base / config["text_embeddings"]
    text = TextEmbeddings.load(text_path)
    pairs = config.get("pairs", [])
    if not pairs:
        raise ValueError("At least one explicit host/donor pair is required")
    percents = config.get("contamination_percent", [0, .5, 1, 2, 5, 10])
    seeds = config.get("seeds", [0])
    if not percents or len(set(percents)) != len(percents) or not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("Unique, nonempty percentages and seeds required")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value) or not 0 <= value <= 100 for value in percents):
        raise ValueError("Contamination percentages must be finite numbers in [0,100]")
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in seeds):
        raise ValueError("Seeds must be nonnegative integers")
    rows, failures, hashes = [], [], {str(text_path): file_sha256(text_path)}
    loaded = []
    seen_hosts, patient_splits = set(), {}
    for pair in pairs:
        host_path, donor_path = base / pair["host"], base / pair["donor"]
        host, donor = Slide.load(host_path), Slide.load(donor_path)
        if host.metadata["slide_id"] in seen_hosts:
            raise ValueError("Use one donor per host in a run; run donor replicates separately")
        seen_hosts.add(host.metadata["slide_id"])
        for slide in (host, donor):
            if slide.metadata["split"] != config["split"]:
                raise ValueError("Do not combine development and evaluation strata in a run")
            expected_kind = "fixture" if category == "fixture" else "real"
            if slide.metadata["source_kind"] != expected_kind:
                raise ValueError("Output category does not match actual artifact provenance")
            if category != "fixture" and slide.metadata["model"]["name"] not in SUPPORTED_REAL_MODELS:
                raise ValueError("Unsupported real model; use CONCH v1 or PathGen-CLIP v1 artifacts")
            check_compatible(slide, text)
            patient = slide.metadata["patient_id"]
            if patient_splits.setdefault(patient, slide.metadata["split"]) != slide.metadata["split"]:
                raise ValueError("Patient leakage across development/evaluation splits")
        if host.metadata.get("label") not in text.classes:
            raise ValueError("Host requires an independently supplied ground-truth class label")
        hashes[str(host_path)] = file_sha256(host_path)
        hashes[str(donor_path)] = file_sha256(donor_path)
        loaded.append((host, donor))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for host, donor in loaded:
        original = predictions(host, text)
        for percent in percents:
            for seed in seeds:
                try:
                    contaminated = inject(host, donor, percent, seed)
                    verify_oracle(host, contaminated, text)
                    after = predictions(contaminated, text)
                    for rule in POOLING:
                        rows.append({"host_slide_id": host.metadata["slide_id"], "donor_slide_id": donor.metadata["slide_id"],
                            "host_project": host.metadata["project"], "donor_project": donor.metadata["project"],
                            "host_organ": host.metadata["organ"], "donor_organ": donor.metadata["organ"],
                            "expected_label": host.metadata["label"],
                            "model": host.metadata["model"]["name"], "pooling": rule,
                            "requested_percent": percent, "realized_percent": 100 * contaminated.foreign_mask.sum().item() / len(host.feats),
                            "seed": seed, "host_tiles": len(host.feats), "foreign_tiles": int(contaminated.foreign_mask.sum()),
                            "original_prediction": original[rule]["prediction"], "contaminated_prediction": after[rule]["prediction"],
                            "original_correct": original[rule]["prediction"] == host.metadata["label"],
                            "prediction_changed": original[rule]["prediction"] != after[rule]["prediction"],
                            "original_scores": json.dumps(original[rule]["scores"], sort_keys=True),
                            "contaminated_scores": json.dumps(after[rule]["scores"], sort_keys=True), "oracle_verified": True,
                            "category": category})
                except (ValueError, KeyError) as error:
                    failures.append({"host_slide_id": host.metadata["slide_id"], "donor_slide_id": donor.metadata["slide_id"],
                                     "percent": percent, "seed": seed, "error": str(error)})
    fields = list(rows[0]) if rows else ["host_slide_id", "category"]
    with (output / "results.csv").open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    write_json(output / "summary.json", summarize(rows))
    write_json(output / "failures.json", failures)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    write_json(output / "experiment.json", {"category": category, "config": config, "input_sha256": hashes,
        "config_sha256": file_sha256(config_path), "model": text.model,
        "source_sha256": {path.name: file_sha256(path) for path in sorted(Path(__file__).parent.glob("*.py"))},
        "text_fingerprint": text.fingerprint(), "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": revision or None, "working_tree_note": "Git HEAD alone does not capture uncommitted changes; preserve this source tree.",
        "successful_rows": len(rows), "failed_trials": len(failures), "prompt_classes": text.classes,
        "exact_prompts": text.prompts, "source_kind": text.source_kind,
        "interpretation": "Synthetic embedding-level contamination; no pixel-level simulation or clinical validation."})
    return {"category": category, "rows": len(rows), "failed_trials": len(failures), "output": str(output)}
