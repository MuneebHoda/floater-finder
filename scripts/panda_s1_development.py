#!/usr/bin/env python3
"""Run bounded S1 development stress tests on existing verified PANDA embeddings; no GPU."""
import argparse,json
from floater_finder.panda_stress import run
p=argparse.ArgumentParser(description=__doc__)
for name in ('manifest','tiling-directories','encoded-root','verification','protocol','output'):
    p.add_argument('--'+name,required=True)
a=p.parse_args()
print(json.dumps(run(a.manifest,a.tiling_directories,a.encoded_root,a.verification,a.protocol,a.output)))
