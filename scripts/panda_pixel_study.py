#!/usr/bin/env python3
"""Prepare four real training pixel pairs, or execute separately approved re-encoding."""
import argparse
import json
from pathlib import Path
from floater_finder.research.pixel_study import preflight, prepare_real, encode_real

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--config',required=True);p.add_argument('--config-sha256',required=True)
p.add_argument('--check-inputs',action='store_true')
mode=p.add_mutually_exclusive_group()
mode.add_argument('--prepare',action='store_true');mode.add_argument('--encode',action='store_true')
p.add_argument('--output');p.add_argument('--source-commit')
p.add_argument('--preparation');p.add_argument('--manifest-sha256')
a=p.parse_args();project=Path(__file__).resolve().parents[1]
if a.prepare or a.encode:
    if not a.output or not a.source_commit:p.error('Execution requires output and source commit')
    if a.prepare:
        r=prepare_real(a.config,a.config_sha256,project,a.output,a.source_commit)
        print(json.dumps(dict(status='prepared_verified_no_inference',images=r['images'],pairs=4)))
    else:
        if not a.preparation or not a.manifest_sha256:p.error('Encoding requires frozen preparation and manifest SHA256')
        r=encode_real(a.config,a.config_sha256,project,a.preparation,a.manifest_sha256,a.output,a.source_commit)
        print(json.dumps(dict(status='verified',images=len(r['records']),pairs=4)))
else:
    c=preflight(a.config,a.config_sha256,project,a.check_inputs)
    print(json.dumps(dict(status='preflight_no_inference',pairs=c['pairs'],images=c['maximum_images'],gpu_submission_authorized=False)))
