#!/usr/bin/env python3
"""New development-only review-policy/topology analysis; reuse committed baseline and S1 draws."""
import argparse
from floater_finder.panda_review_run import develop
p=argparse.ArgumentParser(description=__doc__)
for name in ('manifest','tiling-directories','encoded-root','verification','stress','acquisition-receipts','config','baseline','output'):p.add_argument('--'+name,required=True)
a=p.parse_args()
develop(a.manifest,a.tiling_directories,a.encoded_root,a.verification,a.stress,a.acquisition_receipts,a.config,a.baseline,a.output)
