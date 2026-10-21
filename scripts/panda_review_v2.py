#!/usr/bin/env python3
"""Separate v2 investigation from hash-pinned saved development measurements, CPU Slurm only."""
import argparse
import json
import os
from pathlib import Path
from floater_finder.artifacts import write_json
from floater_finder.experiments import file_sha256
from floater_finder.panda_review_v2 import investigate

p = argparse.ArgumentParser(description=__doc__)
for name in ('cases', 'config', 'output', 'source-commit'):
    p.add_argument('--' + name, required=True)
a = p.parse_args()
if not os.environ.get('SLURM_JOB_ID') or os.environ.get('SLURM_JOB_GPUS'):
    raise RuntimeError('A bounded CPU Slurm allocation is required')
config = json.loads(Path(a.config).read_text())
if file_sha256(a.cases) != config['measurement_sha256']:
    raise ValueError('Saved measurements differ from preregistration')
cases = json.loads(Path(a.cases).read_text())
if len(cases) != config['expected_cases'] or config['splits'] != ['train', 'calibration'] or any(c['split'] not in config['splits'] for c in cases):
    raise ValueError('Expected only the 256 existing development cases')
output = Path(a.output)
if output.exists():
    raise FileExistsError('Preserve previous experiments; use a new versioned output')
v1_path = Path(__file__).resolve().parents[1] / 'reports/panda_review_selection_v1.json'
v1 = json.loads(v1_path.read_text())
result, raw, decomposition_rows = investigate(cases, config, v1['selected_rule'])
result.update(source_commit=a.source_commit, config_sha256=file_sha256(a.config), component_cases_sha256=file_sha256(a.cases),
    v1_reference_selection_sha256=file_sha256(v1_path), slurm_job_id=os.environ['SLURM_JOB_ID'], source_kind='real',
    operations='saved feature ranking/evaluation only; no WSI, embedding or counterfactual recomputation')
for value in (result, raw, decomposition_rows):
    json.dumps(value, allow_nan=False)
output.mkdir(parents=True, exist_ok=False)
write_json(output / 'review_v2_results.json', result)
write_json(output / 'review_v2_metrics_by_case.json', raw)
write_json(output / 'review_v2_decomposition_by_component.json', decomposition_rows)
write_json(output / 'completion.json', dict(source_commit=a.source_commit, slurm_job_id=os.environ['SLURM_JOB_ID'],
    files={f.name: file_sha256(f) for f in output.iterdir()}))
print(json.dumps(dict(primary_strategy=result['primary_strategy'], operating_point_supported=result['operating_point_supported'], final_test_slides_scored=False)))
