#!/usr/bin/env python3
"""Freeze the existing Radboud60 candidates and four existing predictors; no downloads."""
import argparse
import json
from pathlib import Path
from floater_finder.validation_cohort import prepare_fresh_baseline

parser=argparse.ArgumentParser(description=__doc__)
for name in ('train','catalog','pilot','output'): parser.add_argument('--'+name,required=True)
args=parser.parse_args()
print(json.dumps(prepare_fresh_baseline(Path(__file__).resolve().parents[1],args.train,args.catalog,args.pilot,args.output),indent=2))
