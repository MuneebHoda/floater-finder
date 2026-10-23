#!/usr/bin/env python3
"""Generate a hash-checked status report without modifying experiment artifacts."""
import argparse
import json
from pathlib import Path
from floater_finder.research import ExperimentRun, Registry

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('run_directory', type=Path)
parser.add_argument('--summary', action='store_true', help='Verify every artifact, then omit the long artifact listing')
args = parser.parse_args()
metadata = json.loads((args.run_directory/'run.json').read_text())
run = ExperimentRun(**metadata['run'])
report = Registry(args.run_directory, run).report()
if args.summary:
    report.pop('artifacts')
print(json.dumps(report, indent=2, allow_nan=False))
