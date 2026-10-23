#!/usr/bin/env python3
"""Resume selection/reporting from immutable component measurements; never rerun image/model processing."""
import argparse,json,os
from pathlib import Path
from floater_finder.experiments import file_sha256
from floater_finder.artifacts import write_json
from floater_finder.panda_review_run import choose_and_validate
p=argparse.ArgumentParser(description=__doc__)
for name in ('cases','expected-cases-sha256','config','output'):p.add_argument('--'+name,required=True)
a=p.parse_args()
if not os.environ.get('SLURM_JOB_ID'):raise RuntimeError('Selection requires bounded CPU Slurm')
if file_sha256(a.cases)!=a.expected_cases_sha256:raise ValueError('Preserved measurements changed')
cases=json.loads(Path(a.cases).read_text())
if len(cases)!=256 or any(c['split'] not in ('train','calibration') for c in cases):raise ValueError('Development-only saved cases required')
output=Path(a.output)
if output.exists():raise FileExistsError('Preserve earlier outputs')
selection,raw,controls=choose_and_validate(cases,json.loads(Path(a.config).read_text()))
selection.update(source_kind='real',slurm_job_id=os.environ['SLURM_JOB_ID'],component_cases_sha256=a.expected_cases_sha256,
    config_sha256=file_sha256(a.config),test_slides_scored=False,patient_independence_verified=False,clinical_validity_verified=False,
    resumed_reporting_only=True)
# Validate serialization before publishing any files.
for v in (selection,raw,controls):json.dumps(v,allow_nan=False)
output.mkdir(parents=True,exist_ok=False)
write_json(output/'selection.json',selection);write_json(output/'metrics_by_case.json',raw);write_json(output/'matched_controls_by_case.json',controls)
print(json.dumps(dict(operating_point_supported=selection['operating_point_supported'],gates=selection['gates'])))
