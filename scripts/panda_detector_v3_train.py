#!/usr/bin/env python3
"""Execute the frozen, training-only detector-v3 comparison."""
import argparse
from floater_finder.detectors.training import run

parser=argparse.ArgumentParser(description=__doc__)
for name in ('manifest','directories','encoded','verification','stress','cases','config','output'):
    parser.add_argument('--'+name,required=True)
a=parser.parse_args()
run(a.manifest,a.directories,a.encoded,a.verification,a.stress,a.cases,a.config,a.output)
