#!/usr/bin/env python3
"""Create new versioned candidate manifests; no downloads or job submissions."""
import argparse,json
from floater_finder.panda_cohort import plan
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--root',required=True)
p.add_argument('--catalog',required=True)
p.add_argument('--output',required=True)
p.add_argument('--mask-profile')
a=p.parse_args()
print(json.dumps(plan(a.root,a.catalog,a.output,mask_profile=a.mask_profile),indent=2))
