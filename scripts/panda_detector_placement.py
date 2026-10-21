#!/usr/bin/env python3
"""Run the preregistered CPU placement audit on saved training artifacts."""
import argparse
from floater_finder.detectors.placement_run import run

parser = argparse.ArgumentParser(description=__doc__)
for name in ('manifest','directories','encoded','verification','engine-run','cases','protocol','predictor','output','source-commit'):
    parser.add_argument('--'+name,required=True)
run(**vars(parser.parse_args()))
