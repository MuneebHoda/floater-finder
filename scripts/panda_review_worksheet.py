#!/usr/bin/env python3
"""Prepare blank review metadata or validate human response records; no inference."""
import argparse
import json
from pathlib import Path
from floater_finder.research.review_worksheet import preflight,prepare,validate_packet

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--config',required=True);p.add_argument('--config-sha256',required=True)
action=p.add_mutually_exclusive_group();action.add_argument('--prepare',action='store_true');action.add_argument('--responses')
p.add_argument('--source-commit');a=p.parse_args();project=Path(__file__).resolve().parents[1]
if a.prepare:
    if not a.source_commit:p.error('--prepare requires --source-commit')
    r=prepare(a.config,a.config_sha256,project,a.source_commit)
    print(json.dumps(dict(status=r['status'],review_status=r['review_status'],slurm_jobs_submitted=0,human_judgments_generated=0)))
elif a.responses:print(json.dumps(validate_packet(a.config,a.config_sha256,project,a.responses)))
else:
    preflight(a.config,a.config_sha256,project)
    print(json.dumps(dict(status='prepared_source_not_executed',cases=24,human_judgments_generated=0,slurm_jobs_submitted=0)))
