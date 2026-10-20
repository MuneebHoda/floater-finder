#!/usr/bin/env python3
"""Resume a bounded, explicitly approved PANDA GPU batch; one artifact per slide."""
import argparse,json
from pathlib import Path
from floater_finder.panda_encoding import encode_batch
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--tiling-directories',required=True,help='JSON list of completed, hash-audited tile directories')
p.add_argument('--prompts',required=True);p.add_argument('--checkpoint',required=True)
p.add_argument('--checkpoint-sha256',required=True);p.add_argument('--output',required=True)
a=p.parse_args()
encode_batch(json.loads(Path(a.tiling_directories).read_text()),a.prompts,a.checkpoint,a.output,checkpoint_sha256=a.checkpoint_sha256)
