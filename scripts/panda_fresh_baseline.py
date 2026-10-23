#!/usr/bin/env python3
"""Default metadata/model preflight; fresh predictions require an explicit CPU execution."""
import argparse
import json
from pathlib import Path
from floater_finder.predictors.fresh import frozen_inputs,run

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--protocol',required=True)
parser.add_argument('--protocol-sha256',required=True)
parser.add_argument('--execute-fresh',action='store_true')
for name in ('directories','encoded','verification','output','source-commit'): parser.add_argument('--'+name)
args=parser.parse_args(); project=Path(__file__).resolve().parents[1]
if args.execute_fresh:
    if any(getattr(args,k) is None for k in ('directories','encoded','verification','output','source_commit')):
        parser.error('Execution requires directories, encoded, verification, output and source-commit')
    run(args.protocol,args.protocol_sha256,project,args.directories,args.encoded,args.verification,args.output,args.source_commit,True)
else:
    protocol,rows,models=frozen_inputs(args.protocol,args.protocol_sha256,project)
    print(json.dumps(dict(status='frozen_preparation_verified',candidate_slides=len(rows),models_verified=len(models),
        excluded_slide_ids=len(protocol['excluded_slide_ids']),predictions_computed=False,
        fresh_data_readiness='unknown until separately approved acquisition, CPU input gates and GPU encoding',
        original_final_test_predictions_computed=False),indent=2))
