#!/usr/bin/env python3
"""Prepare an unapproved metadata-only CONCH pilot acquisition plan; never download images."""

import argparse
import hashlib
import json
from pathlib import Path

SEED = "floater-pilot-20261018"
OLD_PATIENTS = {"TCGA-2A-A8VL", "TCGA-2F-A9KP", "TCGA-2A-A8VO", "TCGA-2F-A9KO"}
PROJECTS = {"TCGA-PRAD": "prostate", "TCGA-BLCA": "bladder"}


def select_candidates(hits, per_split=4):
    """Outcome-blind hash ranking, one new patient per TCGA source-site prefix."""
    valid = []
    for item in hits:
        cases = item.get("cases", [])
        if len(cases) != 1:
            continue
        patient = cases[0]["submitter_id"]
        project = cases[0]["project"]["project_id"]
        if patient in OLD_PATIENTS or project not in PROJECTS or item["access"] != "open" or item["experimental_strategy"] != "Diagnostic Slide":
            continue
        if not item["file_name"].startswith(patient + "-") or not item["file_name"].endswith(".svs"):
            raise ValueError("GDC patient and slide identity differ")
        digest = item["md5sum"]
        if len(digest) != 32 or any(c not in "0123456789abcdef" for c in digest) or item["file_size"] <= 0:
            raise ValueError("Verified GDC size/MD5 required")
        valid.append({**item, "patient_id": patient, "project": project, "source_site": patient.split("-")[1]})
    valid.sort(key=lambda item: (hashlib.sha256((SEED + ":" + item["patient_id"]).encode()).hexdigest(), item["file_name"]))
    # Old development patients have source prefixes 2A and 2F; old evaluation is retired.
    used_sites, used_patients, selected = {"2A", "2F"}, set(OLD_PATIENTS), []
    for project in PROJECTS:
        for split in ("dev", "eval"):
            chosen = []
            for item in valid:
                if item["project"] != project or item["source_site"] in used_sites or item["patient_id"] in used_patients:
                    continue
                chosen.append({**item, "split": split})
                used_sites.add(item["source_site"])
                used_patients.add(item["patient_id"])
                if len(chosen) == per_split:
                    break
            if len(chosen) != per_split:
                raise ValueError("Not enough source-site-separated, metadata-verified patients; expand metadata inventory")
            selected.extend(chosen)
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(args.metadata)
    metadata = json.loads(source.read_text())
    selected = select_candidates(metadata["response"]["data"]["hits"])
    matched = set(metadata["proposed_candidate_filenames"])
    files = []
    for item in selected:
        if item["file_name"] not in matched:
            raise ValueError("Missing matched shared coordinate filename")
        files.append({"kind": "diagnostic_wsi", "patient_id": item["patient_id"], "project": item["project"],
            "organ": PROJECTS[item["project"]], "split": item["split"], "source_site_prefix": item["source_site"],
            "file_id": item["file_id"], "filename": item["file_name"], "bytes": item["file_size"],
            "checksum": {"algorithm": "md5", "value": item["md5sum"]},
            "source_url": "https://api.gdc.cancer.gov/data/" + item["file_id"],
            "proposed_destination": "/work/nvme/bfqi/mhoda/floater-finder/inputs/" + item["project"] + "/" + item["file_name"],
            "verified_coordinate_filename": metadata["shared_coordinate_root"] + "/" + item["project"] + "/" + item["file_name"][:-4] + ".h5",
            "raw_wsi_header_verified": False, "downloaded": False})
    plan = {"approved": False, "category": "proposed expanded CONCH v1 feasibility pilot", "files": files,
        "total_input_bytes": sum(item["bytes"] for item in files), "new_patients": len(files),
        "additional_checkpoints": 0, "metadata_source": str(source), "metadata_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "selection": {"seed": SEED, "rank": "SHA256(seed + ':' + patient_id); lexicographic file tie-break", "per_split_per_organ": 4,
            "source_site_policy": "One new patient per TCGA source-site prefix; no prefix overlap with existing development or between new splits. Prefix is not normalized institution. No outcome/embedding selection."},
        "retained_development_patients": ["TCGA-2A-A8VO", "TCGA-2F-A9KO"],
        "retired_smoke_evaluation_patients": ["TCGA-2A-A8VL", "TCGA-2F-A9KP"],
        "proposed_sampling": {"tiles_per_patient_cap": 512, "connected_windows": 4, "tiles_per_window_cap": 128,
            "field_um": 256, "export_pixels": 512, "status": "Broader spatial sampler needs implementation and verification before pilot submission."},
        "proposed_clean_removal_target": "At most 1% per unmodified development patient; declare/freeze selection rule before held-out evaluation. No unseen-patient guarantee.",
        "proposed_resources": {"gpu_partition": "gpuA100x4", "gpu_account": "bfqi-delta-gpu", "gpu_qos": "bfqi-delta-gpu-mhoda",
            "download_cpus": 1, "download_memory_gb": 2, "download_wall_minutes_cap": 30,
            "gpus_at_once": 1, "encoding_wall_minutes_cap": 30, "encoding_cpus": 4, "encoding_memory_gb": 16,
            "cpu_account": "bfqi-delta-cpu", "cpu_partition": "cpu", "detector_cpus": 2, "detector_memory_gb": 8,
            "detector_wall_minutes_cap": 30, "status": "Proposed caps, not measured runtime or submitted requests."},
        "unresolved": ["Scope authorization for this bulk cohort acquisition", "Allocation/project storage quota/headroom", "Raw WSI measured MPP and matched-coordinate header/content validation",
            "Broader spatial sampler and cohort runner", "Patient-separated development selection validation", "Normalized institution mapping and report linkage", "Pathologist-confirmed native floater annotations"],
        "scientific_limit": "Metadata-selected feasibility pilot, not a representative population or clinically validated cohort."}
    with Path(args.output).open("x") as handle:
        json.dump(plan, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"plan": args.output, "new_patients": len(files), "total_bytes": plan["total_input_bytes"], "approved": False}))


if __name__ == "__main__":
    main()
