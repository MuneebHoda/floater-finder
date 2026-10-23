#!/usr/bin/env python3
"""Prepare at most 96 supplied-tile composites and controls; no model inference."""
import argparse
from floater_finder.research.pixel_controls import prepare

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--plan',required=True,help='Versioned JSON plan with exact PNG tile hashes and rectangular geometry')
parser.add_argument('--output',required=True,help='New directory; existing outputs are never overwritten')
a=parser.parse_args()
manifest=prepare(a.plan,a.output)
print(f"Prepared {manifest['variants']} image variants; no encoder inference or scientific results.")
