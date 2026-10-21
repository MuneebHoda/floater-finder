#!/usr/bin/env python3
"""Prepared single held-out evaluation. Requires a supported frozen protocol and explicit final execution."""
import argparse,json
from floater_finder.panda_final_run import evaluate_final
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--protocol',required=True);p.add_argument('--expected-sha256',required=True);p.add_argument('--source-root',required=True)
p.add_argument('--execute-final',action='store_true')
a=p.parse_args();r=evaluate_final(a.protocol,a.expected_sha256,a.source_root,a.execute_final)
print(json.dumps({k:v for k,v in r.items() if k not in ('comparisons',)},indent=2))
