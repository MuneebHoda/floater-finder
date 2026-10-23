#!/usr/bin/env python3
"""Verify the fixed cohort against current tile bytes and saved CONCH receipts, without scoring."""
import argparse,json
from pathlib import Path
from floater_finder.panda_encoding import validate_batch
p=argparse.ArgumentParser(description=__doc__)
for name in ('tiling-directories','prompts','checkpoint-sha256','encoded-root','manifest','output'):
    p.add_argument('--'+name,required=True)
a=p.parse_args()
r=validate_batch(json.loads(Path(a.tiling_directories).read_text()),a.prompts,a.checkpoint_sha256,
                 a.encoded_root,a.manifest,a.output)
print(json.dumps({k:v for k,v in r.items() if k!='records'},indent=2))
