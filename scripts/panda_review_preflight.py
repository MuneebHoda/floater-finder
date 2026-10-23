#!/usr/bin/env python3
"""Read-only byte/source verification. Does not decode held-out feature arrays, images or labels."""
import argparse,json
from floater_finder.panda_final import preflight
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--protocol',required=True);p.add_argument('--expected-sha256',required=True);p.add_argument('--source-root',required=True)
a=p.parse_args();print(json.dumps(preflight(a.protocol,a.expected_sha256,a.source_root),indent=2))
