#!/usr/bin/env python3
"""Resolve the approved profile's exact real inputs after CPU success."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def resolve(project, source_manifest_sha256, config_sha256, cpu_job):
    project = Path(project).resolve(); source_path = project.parent/"source_manifest.json"
    if sha(source_path) != source_manifest_sha256:
        raise ValueError("Frozen source manifest differs")
    source = json.loads(source_path.read_text())
    for name, digest in source["files"].items():
        p = (project/name).resolve()
        if not p.is_relative_to(project) or sha(p) != digest:
            raise ValueError("Frozen source file differs")
    from floater_finder.research.pixel_program import load_config
    c, _ = load_config(project, project/"configs/panda_gpu_program_v1/protocol.json", config_sha256)
    prep = Path(c["cpu_output"]); completion = prep/"completion.json"
    m = json.loads(completion.read_text())
    if ((prep/"failure.json").exists() or not m["cpu_feasibility_gate_passed"] or
            m["source_kind"] != "real" or m["slurm_job_id"] != cpu_job or
            m["protocol_sha256"] != config_sha256 or m["checkpoint_current_sha256"] != c["checkpoint_sha256"] or
            m["target_records"] != 10000 or not 8000 <= m["generated_records"] <= 10000 or
            m["generated_records"]+m["excluded_records"] != 10000 or
            m["sources_checked"] != 57 or m["benchmark_sources"] != 45 or m["dense_sources"] != 12 or
            m["inference_executed"] or m["original_final_test_accessed"]):
        raise ValueError("Exact successful real CPU preparation and approved scope required")
    for name, key in (("records.jsonl", "records_sha256"), ("unique_images.json", "unique_images_sha256"),
                      ("exclusions.json", "exclusions_sha256")):
        if sha(prep/name) != m[key]:
            raise ValueError("CPU manifest differs")
    if len(m["source_facts_sha256"]) != 57:
        raise ValueError("All 57 verified source facts required")
    for name, digest in m["source_facts_sha256"].items():
        p = (prep/"sources"/name).resolve()
        if not p.is_relative_to((prep/"sources").resolve()) or sha(p) != digest:
            raise ValueError("Source provenance differs")
    images = json.loads((prep/"unique_images.json").read_text())
    if (not 1 <= len(images) <= 6155 or len(images) != m["exact_unique_images_requiring_inference"] or
            len({r["pixel_sha256"] for r in images}) != len(images) or
            {r["split"] for r in images} != {"fit", "calibration", "validation"}):
        raise ValueError("Deduplicated inference scope differs or exceeds 6155 images")
    counts = {split: sum(r["split"] == split for r in images) for split in ("fit", "calibration", "validation")}
    if counts != m["unique_images_by_split"]:
        raise ValueError("Deduplicated split denominators differ")
    count = min(512, counts["fit"])
    if count < 1:
        raise ValueError("Nonempty training-source profile required")
    output = prep.parent/"pixel-program-10k-v1-profile"
    if output.exists():
        raise FileExistsError("Existing profile output; inspect before any retry")
    receipt = dict(status="actual_cpu_receipt_and_profile_range_frozen_before_inference",
        cpu_job_id=cpu_job, source_manifest_sha256=source_manifest_sha256, parent_commit=source["parent_commit"],
        protocol_sha256=config_sha256, preparation=str(prep), preparation_sha256=sha(completion),
        exact_unique_images=len(images), split="fit", offset=0, images=count, maximum_profile_minutes=15,
        benchmark_gpu_ceiling_equivalent_hours=.75, inference_executed=False, remaining_batches_submitted=False)
    return c, str(output), receipt


def execute(a):
    if not os.environ.get("SLURM_JOB_ID") or not os.environ.get("SLURM_JOB_GPUS"):
        raise RuntimeError("Approved one-GPU Slurm profile required")
    c, output, receipt = resolve(a.project, a.source_manifest_sha256, a.config_sha256, a.cpu_job)
    receipt["gpu_job_id"] = os.environ["SLURM_JOB_ID"]
    path = Path(output).parent/("pixel-program-10k-v1-profile-launch-"+receipt["gpu_job_id"]+".json")
    with path.open("x") as f:
        json.dump(receipt, f, indent=2, allow_nan=False); f.write("\n")
    command = ["/bin/bash", str(Path(a.project)/"scripts/slurm/panda_pixel_program_encode.sbatch"),
        a.project, a.runtime, a.config_sha256, receipt["preparation_sha256"], output, "fit", "0", str(receipt["images"])]
    print(json.dumps(receipt), flush=True)
    os.execv(command[0], command)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("project", "runtime", "source-manifest-sha256", "config-sha256", "cpu-job"):
        p.add_argument("--"+name, required=True)
    execute(p.parse_args())
