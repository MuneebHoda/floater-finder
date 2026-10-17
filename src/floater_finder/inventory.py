"""Bounded local data discovery; missing provenance stays missing."""

import csv
import os
from pathlib import Path
import re

from .artifacts import write_json

FIELDS = ("slide_id", "patient_id", "project", "tissue_source_site", "institution_id", "institution",
          "institution_provenance", "diagnostic_slide", "diagnostic_provenance", "diagnostic_verified", "organ", "label", "split", "slide_path",
          "report_path", "report_provenance", "report_available", "tile_manifest", "tiles_available",
          "coordinate_units", "tile_step_x", "tile_step_y", "microns_per_unit", "magnification", "embedding_path")


def barcode(slide_id):
    match = re.match(r"^(TCGA-([A-Z0-9]{2})-[A-Z0-9]{4})(?:-|$)", slide_id.upper())
    return (match[1], match[2]) if match else (None, None)


def read_csv(path):
    with Path(path).open(newline="") as handle:
        return list(csv.DictReader(handle))


def discover(roots, max_files=1000, max_depth=3):
    """No symlink traversal, hidden files, image reads, or unbounded filesystem walk."""
    if max_files < 1 or max_depth < 0:
        raise ValueError("Invalid discovery bounds")
    found, errors = [], []
    pending = [(Path(root), 0) for root in roots]
    truncated = False
    while pending:
        directory, depth = pending.pop(0)
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if entry.name.startswith(".") or entry.is_symlink():
                        continue
                    if entry.is_dir(follow_symlinks=False) and depth < max_depth:
                        pending.append((Path(entry.path), depth + 1))
                    elif entry.is_file(follow_symlinks=False) and Path(entry.name).suffix.lower() in {".svs", ".tif", ".tiff", ".ndpi"}:
                        found.append({"slide_id": Path(entry.name).stem, "slide_path": str(Path(entry.path).resolve())})
                        if len(found) >= max_files:
                            truncated = True
                            return found, errors, truncated
        except OSError as error:
            errors.append({"path": str(directory), "error": type(error).__name__})
    return found, errors, truncated


def inventory(roots=(), manifest=None, institution_map=None, max_files=1000, max_depth=3):
    records, errors, truncated = discover(roots, max_files, max_depth) if roots else ([], [], False)
    manifest_base = Path(manifest).resolve().parent if manifest else Path.cwd()
    supplied = read_csv(manifest) if manifest else []
    # A manifest is authoritative for metadata, not evidence that a file exists.
    by_path = {str(Path(row["slide_path"]).resolve()): row for row in records}
    for row in supplied:
        if row.get("slide_path"):
            key = str((manifest_base / row["slide_path"]).resolve())
            by_path[key] = {**by_path.get(key, {}), **row, "slide_path": key}
        else:
            by_path[f'manifest:{len(by_path)}'] = row
    institutions = {}
    if institution_map:
        for row in read_csv(institution_map):
            if not all(row.get(key) for key in ("tissue_source_site", "institution_id", "institution", "provenance")):
                raise ValueError("Institution mapping requires a named institution and verified provenance")
            if row["tissue_source_site"] in institutions:
                raise ValueError("Duplicate tissue source site mapping")
            institutions[row["tissue_source_site"]] = row
    result, missing = [], []
    patients, slide_ids = {}, set()
    for raw in by_path.values():
        row = {key: raw.get(key) or None for key in FIELDS}
        row["slide_id"] = row["slide_id"] or (Path(row["slide_path"]).stem if row["slide_path"] else None)
        if not row["slide_id"] or row["slide_id"] in slide_ids:
            raise ValueError("Missing or duplicate slide ID in cohort inventory")
        slide_ids.add(row["slide_id"])
        patient, site = barcode(row["slide_id"])
        if patient and row["patient_id"] and patient != row["patient_id"]:
            raise ValueError("Manifest patient contradicts the TCGA barcode")
        row["patient_id"] = row["patient_id"] or patient
        row["tissue_source_site"] = row["tissue_source_site"] or site
        # Raw source-site equality is never treated as a verified institution match.
        mapped = institutions.get(row["tissue_source_site"])
        row["institution_id"] = mapped["institution_id"] if mapped else None
        row["institution"] = mapped["institution"] if mapped else None
        row["institution_provenance"] = mapped["provenance"] if mapped else None
        if row["diagnostic_slide"] is None and patient:
            row["diagnostic_slide"] = bool(re.search(r"-DX\d(?:[.-]|$)", row["slide_id"], re.I))
            row["diagnostic_provenance"] = "filename convention only; not independently verified"
            row["diagnostic_verified"] = False
        elif row["diagnostic_slide"] is not None:
            value = str(row["diagnostic_slide"]).lower()
            if value not in {"true", "false", "1", "0"}:
                raise ValueError("diagnostic_slide must be true/false")
            row["diagnostic_slide"] = value in {"true", "1"}
            row["diagnostic_verified"] = bool(row["diagnostic_provenance"])
        else:
            row["diagnostic_verified"] = False
        for key in ("slide_path", "report_path", "tile_manifest", "embedding_path"):
            if row[key]:
                row[key] = str((manifest_base / row[key]).resolve())
        row["report_available"] = bool(row["report_path"] and Path(row["report_path"]).is_file())
        row["tiles_available"] = bool(row["tile_manifest"] and Path(row["tile_manifest"]).is_file())
        if row["split"] not in {None, "dev", "eval"}:
            raise ValueError("Cohort split must be dev/eval or explicitly unknown")
        if row["patient_id"] and row["split"]:
            previous = patients.setdefault(row["patient_id"], row["split"])
            if previous != row["split"]:
                raise ValueError("Patient leakage across development and evaluation splits")
        absent = [key for key in ("patient_id", "project", "organ", "label", "split", "institution_id",
                                  "coordinate_units", "tile_step_x", "tile_step_y", "microns_per_unit", "magnification") if row[key] is None]
        if not row["slide_path"] or not Path(row["slide_path"]).is_file(): absent.append("slide_file")
        if not row["report_available"] or not row["report_provenance"]: absent.append("linked_report_with_provenance")
        if not row["tiles_available"]: absent.append("tile_manifest")
        if row["diagnostic_slide"] is not True or not row["diagnostic_verified"]: absent.append("confirmed_diagnostic_slide")
        result.append(row)
        missing.append({"slide_id": row["slide_id"], "missing": absent})
    return result, {"candidate_count": len(result), "missing_by_slide": missing,
                    "discovery_errors": errors, "discovery_truncated": truncated,
                    "max_files": max_files, "max_depth": max_depth,
                    "note": "File/metadata inventory only; no slide pixels, reports, or model weights read."}


def save_inventory(records, report, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    with (output / "cohort_inventory.csv").open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
    write_json(output / "missing_data.json", report)


def select_pairs(records, host_organ, donor_organ, split, seed=0):
    import numpy as np
    eligible = [row for row in records if row.get("patient_id") and row.get("split") == split and
                row.get("diagnostic_slide") is True and row.get("diagnostic_verified") is True]
    rng = np.random.default_rng(seed)
    pairs = []
    for host in sorted((row for row in eligible if row.get("organ") == host_organ), key=lambda row: row["slide_id"]):
        donors = [row for row in eligible if row.get("organ") == donor_organ and row["patient_id"] != host["patient_id"]]
        same_institution = [row for row in donors if host.get("institution_id") and host.get("institution_provenance") and
                            row.get("institution_provenance") and row.get("institution_id") == host["institution_id"]]
        candidates = sorted(same_institution or donors, key=lambda row: row["slide_id"])
        if not candidates:
            raise ValueError("No eligible different-patient donor in this split")
        donor = candidates[int(rng.integers(len(candidates)))]
        pairs.append({"host": host["slide_id"], "donor": donor["slide_id"], "verified_institution_match": bool(same_institution)})
    return pairs
