#!/usr/bin/env python3
"""Training-only CONCH predictor CV; known calibration remains descriptive."""
import argparse
from floater_finder.predictors.run import run

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','directories','encoded','verification','config','output'):
        p.add_argument('--'+name, required=True)
    a=p.parse_args()
    print(run(a.manifest,a.directories,a.encoded,a.verification,a.config,a.output))
