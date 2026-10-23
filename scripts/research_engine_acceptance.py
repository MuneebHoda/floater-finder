#!/usr/bin/env python3
"""Bounded real-training-input acceptance for shared interventions; no encoder inference."""
import argparse
import json
from floater_finder.research.acceptance import run

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--manifest', required=True)
p.add_argument('--tiling-directories', required=True)
p.add_argument('--encoded-root', required=True)
p.add_argument('--verification', required=True)
p.add_argument('--acquisition-receipts', required=True)
p.add_argument('--protocol', required=True)
p.add_argument('--source-commit', required=True)
p.add_argument('--output', required=True)
p.add_argument('--predictor', help='Optional previously training-selected portable frozen predictor directory')
a = p.parse_args()
print(json.dumps(run(a.manifest, a.tiling_directories, a.encoded_root, a.verification,
    a.acquisition_receipts, a.protocol, a.source_commit, a.output, a.predictor), allow_nan=False))
