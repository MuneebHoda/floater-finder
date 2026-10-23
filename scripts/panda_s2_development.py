#!/usr/bin/env python3
"""Execute S2 development-only low/high stress on verified cached CONCH embeddings."""
import argparse
import json
from floater_finder.panda_s2 import run
parser=argparse.ArgumentParser(description=__doc__)
for name in ('manifest','tiling-directories','encoded-root','verification','protocol','baseline-predictions','output'):
    parser.add_argument('--'+name,required=True)
a=parser.parse_args()
print(json.dumps(run(a.manifest,a.tiling_directories,a.encoded_root,a.verification,a.protocol,a.baseline_predictions,a.output)))
