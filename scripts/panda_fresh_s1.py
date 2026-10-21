#!/usr/bin/env python3
"""Default: metadata-only preparation. Real follow-up requires approved CPU Slurm."""
import argparse
import json
from pathlib import Path
from floater_finder.research.fresh_stress import preflight, run

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--config', required=True)
p.add_argument('--config-sha256', required=True)
p.add_argument('--output')
p.add_argument('--source-commit')
p.add_argument('--execute', action='store_true')
a = p.parse_args()
project = Path(__file__).resolve().parents[1]
if a.execute:
    if not a.output or not a.source_commit:
        p.error('--execute needs --output and --source-commit')
    result = run(a.config, a.config_sha256, project, a.output, a.source_commit, execute=True)
    print(json.dumps(dict(status='verified', model_trial_records=result['eligible_model_trial_records'],
        exclusions=result['exclusions'], original_final_test_predictions_computed=False)))
else:
    c, protocol, rows, models = preflight(a.config, a.config_sha256, project)
    print(json.dumps(dict(status='prepared_not_executed', slides=len(rows), benign_hosts=20,
        primary=models['primary'].spec['model_id'], comparator=models['historical'].spec['model_id'],
        maximum_interventions=c['maximum_interventions'], maximum_counterfactual_bags=c['maximum_counterfactual_bags'],
        predictions_computed=False, output_intended=c['output'], resources=c['resources'])))
