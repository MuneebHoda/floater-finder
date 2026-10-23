#!/usr/bin/env python3
"""Recreate only documented figure crops; never fabricate or retouch microscopy."""
from pathlib import Path
import hashlib,json
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
for r in json.loads((HERE/'media/provenance.json').read_text()):
 out=ROOT/r['path']
 if 'crop_box_pixels_xyxy' in r:
  src=ROOT/r['source_path']
  if hashlib.sha256(src.read_bytes()).hexdigest()!=r['source_sha256']:raise ValueError('Source figure changed')
  Image.open(src).crop(tuple(r['crop_box_pixels_xyxy'])).save(out)
 if hashlib.sha256(out.read_bytes()).hexdigest()!=r['sha256']:raise ValueError('Media identity mismatch')
print('All microscopy bytes and figure panel crops verified')
