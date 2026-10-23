#!/usr/bin/env python3
"""CPU preparation or an explicitly approved, pinned GPU inference range."""
import argparse
import json
from floater_finder.research.pixel_program import prepare, encode

p = argparse.ArgumentParser()
p.add_argument("action", choices=("prepare", "encode"))
p.add_argument("--project", required=True)
p.add_argument("--config", required=True)
p.add_argument("--config-sha256", required=True)
p.add_argument("--output", required=True)
p.add_argument("--preparation-sha256")
p.add_argument("--split", choices=("fit", "calibration", "validation"))
p.add_argument("--offset", type=int, default=0)
p.add_argument("--limit", type=int)
a = p.parse_args()
if a.action == "prepare":
    result = prepare(a.project, a.config, a.config_sha256, a.output)
else:
    if not a.preparation_sha256 or not a.split or a.limit is None:
        p.error("GPU execution requires the frozen CPU receipt and an exact split/range")
    result = encode(a.project, a.config, a.config_sha256, a.preparation_sha256,
                    a.output, a.split, a.offset, a.limit)
print(json.dumps(result, allow_nan=False))
