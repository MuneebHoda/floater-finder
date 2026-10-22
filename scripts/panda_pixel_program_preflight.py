#!/usr/bin/env python3
"""Read-only receipt inspection; prints proposed exact ranges, never submits."""
import argparse
import json
from pathlib import Path
import shlex
from floater_finder.experiments import file_sha256
from floater_finder.research.pixel_program import load_config

p = argparse.ArgumentParser()
p.add_argument("--project", required=True)
p.add_argument("--config-sha256", required=True)
p.add_argument("--runtime", required=True)
a = p.parse_args(); project = Path(a.project)
c, _ = load_config(project, project/"configs/panda_gpu_program_v1/protocol.json", a.config_sha256)
completion = Path(c["cpu_output"])/"completion.json"
if not completion.is_file():
    print(json.dumps(dict(status="CPU_completion_pending", GPU_authorized=False)))
    raise SystemExit(0)
receipt = json.loads(completion.read_text())
if receipt["protocol_sha256"] != a.config_sha256:
    raise ValueError("CPU receipt belongs to another protocol")
result = dict(status="CPU_feasibility_passed" if receipt["cpu_feasibility_gate_passed"] else "CPU_feasibility_failed",
              receipt_sha256=file_sha256(completion), cpu_summary=receipt, GPU_authorized=False)
if receipt["cpu_feasibility_gate_passed"]:
    commands = []
    def command(split, offset, count, phase, minutes):
        args = ["sbatch", "--parsable", "--time="+minutes,
            str(project/"scripts/slurm/panda_pixel_program_encode.sbatch"),
            str(project), a.runtime, a.config_sha256, file_sha256(completion),
            str(Path(c["cpu_output"]).parent/("pixel-program-10k-v1-"+phase)),split,str(offset),str(count)]
        return shlex.join(args)
    n = min(512,receipt["unique_images_by_split"]["fit"])
    commands.append(dict(phase="profile_only_after_explicit_approval",command=command("fit",0,n,"profile","00:15:00")))
    for split in ("fit", "calibration", "validation"):
        start = n if split == "fit" else 0
        count = receipt["unique_images_by_split"][split]-start
        if count:
            commands.append(dict(phase="remaining_scope_requires_profile_billing_reconciliation_and_approval",
                command=command(split,start,count,"remaining-"+split,"00:10:00")))
    result["proposed_unsubmitted_commands"] = commands
print(json.dumps(result,indent=2,allow_nan=False))
