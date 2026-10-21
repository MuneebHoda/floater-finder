#!/usr/bin/env python3
"""Generate a hash-checked status report without modifying experiment artifacts."""
import argparse
from dataclasses import fields
import json
from pathlib import Path
from floater_finder.research import ExperimentRun, Registry

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('run_directory', type=Path)
args = parser.parse_args()
metadata = json.loads((args.run_directory/'run.json').read_text())
run = ExperimentRun(**metadata['run'])
print(json.dumps(Registry(args.run_directory, run).report(), indent=2, allow_nan=False))
