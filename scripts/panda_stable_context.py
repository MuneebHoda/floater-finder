#!/usr/bin/env python3
"""Preflight or execute the fixed original-training stable-context candidate."""
import argparse
import json
from pathlib import Path
from floater_finder.detectors.stable_context import preflight,run
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--config',required=True);p.add_argument('--config-sha256',required=True)
p.add_argument('--check-inputs',action='store_true');p.add_argument('--execute',action='store_true')
p.add_argument('--output');p.add_argument('--source-commit');a=p.parse_args();project=Path(__file__).resolve().parents[1]
if a.execute:
    if not a.output or not a.source_commit:p.error('--execute requires --output and --source-commit')
    r=run(a.config,a.config_sha256,project,a.output,a.source_commit,execute=True)
    print(json.dumps(dict(status='verified',primary=r['primary'],training_gate_passed=r['methods'][r['primary']]['metrics']['training_candidate_gate_passed'],final_test_ready=False)))
else:
    c=preflight(a.config,a.config_sha256,project,check_inputs=a.check_inputs)
    print(json.dumps(dict(status='prepared_not_executed',slides=c['slides'],positive_cases=c['positive_cases'],resources=c['resources'])))
