"""Outcome-blind, metadata-only fresh PANDA validation proposals; no acquisition."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def propose(train_rows, catalog, excluded_ids, *, provider, per_group=20, seed=20261021):
    if provider not in ("radboud", "karolinska") or per_group < 1:
        raise ValueError("Specify a PANDA provider and a positive group size")
    if not catalog.get("complete") or catalog.get("error"):
        raise ValueError("Complete successful official catalog required")
    if len({r["image_id"] for r in train_rows}) != len(train_rows):
        raise ValueError("Duplicate metadata slide ID")
    files = {}
    for f in catalog["files"]:
        if f["name"] in files or type(f["bytes"]) is not int or f["bytes"] <= 0:
            raise ValueError("Invalid or duplicate catalog record")
        files[f["name"]] = f["bytes"]
    excluded_ids = set(excluded_ids)
    exposed_patients = {r["patient_id"] for r in train_rows
                        if r["image_id"] in excluded_ids and r.get("patient_id")}
    eligible = {g: [] for g in ("benign", "gg1", "high_grade")}
    for r in train_rows:
        sid, grade = r["image_id"], int(r["isup_grade"])
        if len(sid) != 32 or any(c not in "0123456789abcdef" for c in sid):
            raise ValueError("Invalid PANDA image ID")
        group = "benign" if grade == 0 else "gg1" if grade == 1 else "high_grade" if grade in (4, 5) else None
        patient = r.get("patient_id", "")
        image, mask = f"train_images/{sid}.tiff", f"train_label_masks/{sid}_mask.tiff"
        if (r["data_provider"] != provider or group is None or sid in excluded_ids
                or (patient and patient in exposed_patients) or image not in files):
            continue
        eligible[group].append(dict(image_id=sid, data_provider=provider,
            isup_grade=grade, gleason_score=r["gleason_score"], group=group,
            patient_id=patient, split="fresh_development_validation", seed=seed,
            image_file=image, image_catalog_bytes=files[image],
            mask_file=mask if mask in files else "", mask_catalog_bytes=files.get(mask, 0),
            mask_usable_verified=False, acquisition_status="not_checked"))
    chosen, selected_patients = [], set()
    for group, pool in eligible.items():
        pool.sort(key=lambda r: (not r["mask_file"], hashlib.sha256(
            f"{seed}:fresh-validation:{provider}:{r['image_id']}".encode()).hexdigest()))
        count = 0
        for r in pool:
            if r["patient_id"] and r["patient_id"] in selected_patients:
                continue
            chosen.append(r)
            if r["patient_id"]:
                selected_patients.add(r["patient_id"])
            count += 1
            if count == per_group:
                break
    counts = dict(Counter(r["group"] for r in chosen))
    return chosen, dict(provider=provider, seed=seed, target_per_group=per_group,
        eligible_after_exclusion={g: len(v) for g, v in eligible.items()},
        selected_counts={g: counts.get(g, 0) for g in eligible}, selected_slides=len(chosen),
        target_met=all(counts.get(g, 0) == per_group for g in eligible),
        excluded_slide_ids=len(excluded_ids), selected_excluded_overlap=0,
        selected_known_patient_ids=len(selected_patients),
        patient_independence="unknown unless every selected and excluded slide has a verified patient identifier",
        catalog_masks=sum(bool(r["mask_file"]) for r in chosen),
        usable_mask_coverage="unverified; catalog presence is not readable annotation",
        catalog_tiff_bytes=sum(r["image_catalog_bytes"] + r["mask_catalog_bytes"] for r in chosen),
        transfer_bytes="unmeasured; compression/ZIP overhead can change network volume",
        selection_rule="catalog mask first, then SHA256(seed:purpose:provider:image_id); no predictions or annotation contents",
        status="metadata-only proposal; acquisition, tiling, encoding and validation not executed")


def write_proposal(train, catalog_path, exclude_manifests, output, *, per_group=20, seed=20261021):
    train, catalog_path, output = Path(train), Path(catalog_path), Path(output)
    with train.open(newline="") as f:
        rows = list(csv.DictReader(f))
    excluded = set()
    for path in exclude_manifests:
        with Path(path).open(newline="") as f:
            excluded.update(r["image_id"] for r in csv.DictReader(f))
    catalog = json.loads(catalog_path.read_text())
    proposals = {p: propose(rows, catalog, excluded, provider=p, per_group=per_group, seed=seed)
                 for p in ("radboud", "karolinska")}
    output.mkdir(parents=True, exist_ok=False)
    report = dict(train_sha256=sha256(train), catalog_sha256=sha256(catalog_path),
        exclusion_manifest_sha256={str(p): sha256(p) for p in exclude_manifests},
        patient_id_column_present="patient_id" in rows[0], proposals={})
    for provider, (chosen, summary) in proposals.items():
        path = output / f"{provider}_fresh_validation_candidates.csv"
        if chosen:
            with path.open("x", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(chosen[0]))
                writer.writeheader()
                writer.writerows(chosen)
            summary["manifest_sha256"] = sha256(path)
        report["proposals"][provider] = summary
    (output / "proposal.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
