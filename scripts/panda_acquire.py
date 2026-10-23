#!/usr/bin/env python3
"""Execute an explicitly approved selective PANDA file plan inside Slurm."""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile

def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write('\n')


def validate_plan(plan):
    if plan.get('slides') not in (60,120) or not plan.get('files'):
        raise ValueError('Expected a 60/120-slide catalog-derived acquisition plan')
    names=set()
    for row in plan['files']:
        name=row['name'];path=Path(name)
        if (name in names or len(path.parts)!=2 or row['role'] not in ('image','mask') or
                path.parts[0] != ('train_images' if row['role']=='image' else 'train_label_masks') or
                path.suffix!='.tiff' or len(row['image_id'])!=32 or
                any(c not in '0123456789abcdef' for c in row['image_id']) or
                path.name != row['image_id']+('_mask' if row['role']=='mask' else '')+'.tiff' or
                type(row['bytes']) is not int or not 0<row['bytes']<=5_000_000_000):
            raise ValueError('Invalid/unbounded selective acquisition entry')
        names.add(name)
    image_ids={r['image_id'] for r in plan['files'] if r['role']=='image'}
    if len(image_ids)!=plan['slides'] or any(r['image_id'] not in image_ids for r in plan['files']):
        raise ValueError('Plan slide count or image/mask membership mismatch')
    return plan


def acquire(plan_path, root, receipts, approved_sha256):
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('Dataset acquisition requires an approved Slurm job')
    if file_sha256(plan_path)!=approved_sha256:
        raise ValueError('Approval hash differs from the exact acquisition plan')
    plan=validate_plan(json.loads(Path(plan_path).read_text()))
    root,receipts=Path(root).resolve(),Path(receipts)
    receipts.mkdir(parents=True,exist_ok=True)
    from kaggle.api.kaggle_api_extended import KaggleApi
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
        api=KaggleApi();api.authenticate()
    for item in plan['files']:
        destination=root/item['name']
        destination.parent.mkdir(parents=True,exist_ok=True)
        if destination.is_symlink() or destination.parent.resolve()!=root/Path(item['name']).parent:
            raise ValueError('Symlinks are forbidden in dataset destinations')
        receipt=receipts/(destination.name+'.json')
        if destination.exists():
            if destination.stat().st_size!=item['bytes']:
                raise ValueError('Existing file differs from catalog size; preserved for inspection')
            if receipt.exists() and json.loads(receipt.read_text())['sha256']!=file_sha256(destination):
                raise ValueError('Existing file differs from its receipt; preserved for inspection')
            if not receipt.exists():
                write_json(receipt,dict(name=item['name'],bytes=item['bytes'],sha256=file_sha256(destination),
                    integrity='catalog size plus locally computed SHA256; external checksum unavailable',
                    source='pre-existing local file',reader_verified=False))
            continue
        with tempfile.TemporaryDirectory(prefix='.panda-selective-',dir=root) as tmp:
            tmp=Path(tmp)
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                api.competition_download_file('prostate-cancer-grade-assessment',item['name'],path=str(tmp),quiet=True)
            downloaded=list(tmp.iterdir())
            if len(downloaded)!=1:
                raise ValueError('Unexpected selective download output')
            fetched=downloaded[0]
            if zipfile.is_zipfile(fetched):
                with zipfile.ZipFile(fetched) as archive:
                    members=archive.infolist()
                    if len(members)!=1 or members[0].filename not in (destination.name,item['name']) or members[0].file_size!=item['bytes']:
                        raise ValueError('ZIP member/name/size differs from catalog plan')
                    unpacked=tmp/'unpacked.tiff'
                    with archive.open(members[0]) as src,unpacked.open('xb') as dst:
                        shutil.copyfileobj(src,dst,1024*1024)  # Fully reading verifies ZIP CRC.
                    fetched=unpacked
            if fetched.stat().st_size!=item['bytes']:
                raise ValueError('Downloaded TIFF/catalog size mismatch')
            digest=file_sha256(fetched)
            os.link(fetched,destination)  # Atomic exclusive publish; never overwrite another run.
            write_json(receipt,dict(name=item['name'],bytes=item['bytes'],sha256=digest,
                source='official Kaggle competition selective file download',plan_sha256=approved_sha256,
                integrity='catalog size, ZIP CRC when packaged, local SHA256; external checksum unavailable',
                slurm_job_id=os.environ['SLURM_JOB_ID'],reader_verified=False))
        print(json.dumps(dict(acquired=item['name'],bytes=item['bytes'])),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',required=True);parser.add_argument('--root',required=True)
    parser.add_argument('--receipts',required=True);parser.add_argument('--approved-plan-sha256',required=True)
    a=parser.parse_args()
    try:
        acquire(a.plan,a.root,a.receipts,a.approved_plan_sha256)
    except Exception as error:
        # HTTP exception messages can include signed URLs; never log the raw exception.
        print(json.dumps(dict(status='blocked',error_type=type(error).__name__,
            http_status=getattr(getattr(error,'response',None),'status_code',None))),flush=True)
        raise SystemExit(1)
