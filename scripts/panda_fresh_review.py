#!/usr/bin/env python3
"""Preflight fixed-rule S3 transfer; real execution requires approved CPU Slurm."""
import argparse
from pathlib import Path
import json
from floater_finder.detectors.fresh_review import preflight,run

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--config',required=True);p.add_argument('--config-sha256',required=True)
p.add_argument('--check-inputs',action='store_true');p.add_argument('--execute',action='store_true')
p.add_argument('--output');p.add_argument('--source-commit')
a=p.parse_args();project=Path(__file__).resolve().parents[1]
if a.execute:
    if not a.output or not a.source_commit:p.error('--execute requires --output and --source-commit')
    r=run(a.config,a.config_sha256,project,a.output,a.source_commit,execute=True)
    print(json.dumps(dict(status='verified',bags=r['bags'],model_policy_records=r['model_policy_records'])))
else:
    c,*_=preflight(a.config,a.config_sha256,project,check_inputs=a.check_inputs)
    print(json.dumps(dict(status='prepared_not_executed',maximum_bags=c['maximum_bags'],policies=c['policies'],
        visual_threshold=c['visual_threshold'],predictions_computed=False,resources=c['resources'])))
