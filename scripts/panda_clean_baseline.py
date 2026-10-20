#!/usr/bin/env python3
"""Evaluate fixed PANDA zero-shot prompts on training/calibration slides only."""
import argparse
from floater_finder.panda_baseline import evaluate_development
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--manifest',required=True);p.add_argument('--encoded-root',required=True);p.add_argument('--output',required=True)
a=p.parse_args();evaluate_development(a.manifest,a.encoded_root,a.output)
