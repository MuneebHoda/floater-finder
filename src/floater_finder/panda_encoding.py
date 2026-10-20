"""Checkpointable per-slide CONCH encoding using the existing canonical adapter."""
import csv
import importlib.metadata
import importlib.util
import json
import os
import re
from pathlib import Path
import time

import numpy as np

from .artifacts import Slide, TextEmbeddings, check_compatible, write_json
from .conch import encode_tiles
from .experiments import file_sha256


def encoding_contract():
    spec=importlib.util.find_spec('conch')
    if spec is None or not spec.submodule_search_locations:
        raise ValueError('Installed CONCH package locations are unavailable')
    # CONCH can be a namespace package with origin=None in the verified Delta runtime.
    roots=[Path(p) for p in spec.submodule_search_locations]
    return dict(adapter_sha256=file_sha256(Path(__file__).with_name('conch.py')),
        seed=0,cuda_matmul_tf32=False,cudnn_tf32=False,
        runtime_versions={n:importlib.metadata.version(n) for n in ('Pillow','torch','torchvision','conch')},
        upstream_source_sha256={f'{i}/{p.relative_to(root)}':file_sha256(p)
            for i,root in enumerate(roots) for p in sorted(root.rglob('*.py'))})


def input_identity(directory, prompts_path, checkpoint_sha256, encoding_contract=None):
    directory=Path(directory).resolve()
    with (directory/'tiles.csv').open(newline='') as handle:
        rows=list(csv.DictReader(handle))
    if not 1<=len(rows)<=1024 or len({r['tile_id'] for r in rows})!=len(rows):
        raise ValueError('Invalid bounded tile manifest')
    hashes={};files={}
    for row in rows:
        path=(directory/row['path']).resolve()
        if path.parent!=directory or not path.is_file():
            raise ValueError('Tile path must name a file inside its slide directory')
        hashes[row['tile_id']]=file_sha256(path)
        files[path.name]=hashes[row['tile_id']]
    identity=dict(manifest_sha256=file_sha256(directory/'tiles.csv'),
        metadata_sha256=file_sha256(directory/'metadata.json'),png_sha256=hashes,
        prompts_sha256=file_sha256(prompts_path),checkpoint_sha256=checkpoint_sha256,
        encoding_contract=encoding_contract)
    prepared=directory/'completion.json'
    if prepared.exists():
        expected=json.loads(prepared.read_text())['sha256']
        files.update({'tiles.csv':identity['manifest_sha256'],'metadata.json':identity['metadata_sha256']})
        if not set(files).issubset(expected):
            raise ValueError('Prepared tiling receipt is incomplete')
        for name,digest in expected.items():
            if Path(name).name!=name or (files.get(name) or file_sha256(directory/name))!=digest:
                raise ValueError('Prepared tiling artifact changed before encoding')
        identity['prepared_tiling_receipt_sha256']=file_sha256(prepared)
    return rows,identity


def validate_saved(output, rows, identity):
    output=Path(output)
    receipt=json.loads((output/'completion.json').read_text())
    if receipt['input_identity']!=identity:
        raise ValueError('Existing embedding inputs/model/prompts differ; choose a separate output')
    for name,digest in receipt['artifact_sha256'].items():
        if name not in ('slide.npz','text.npz','timing.json') or file_sha256(output/name)!=digest:
            raise ValueError('Completed embedding artifact checksum mismatch')
    if set(receipt['artifact_sha256'])!={'slide.npz','text.npz','timing.json'}:
        raise ValueError('Incomplete embedding receipt')
    slide,text=Slide.load(output/'slide.npz'),TextEmbeddings.load(output/'text.npz')
    if (slide.feats.shape!=(len(rows),512) or
            slide.tile_ids.tolist()!=[r['tile_id'] for r in rows] or
            not np.array_equal(slide.coords,np.array([[float(r['x']),float(r['y'])] for r in rows])) or
            slide.metadata['model']!=text.model or
            slide.metadata['model']['checkpoint_sha256']!=identity['checkpoint_sha256'] or
            slide.metadata['source_kind']!='real' or text.source_kind!='real'):
        raise ValueError('Saved embedding shape/coordinates/IDs/model provenance mismatch')
    check_compatible(slide,text)
    return receipt


def validate_batch(directories, prompts_path, checkpoint_sha256, encoded_root, manifest, output):
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('Real cohort artifact verification requires a bounded Slurm CPU job')
    with Path(manifest).open(newline='') as handle:
        cohort=list(csv.DictReader(handle))
    by_id={r['image_id']:r for r in cohort}
    if len(cohort) not in (60,120) or len(by_id)!=len(cohort) or len(directories)!=len(cohort):
        raise ValueError('Exact fixed 60/120-slide cohort required')
    contract=encoding_contract();records=[];seen=set();fingerprint=None
    for directory in map(Path,directories):
        rows,identity=input_identity(directory,prompts_path,checkpoint_sha256,contract)
        meta=json.loads((directory/'metadata.json').read_text());sid=meta['slide_id']
        if sid not in by_id or sid in seen:
            raise ValueError('Embedding input is missing, duplicated or outside the cohort')
        seen.add(sid);row=by_id[sid];destination=Path(encoded_root)/sid
        receipt=validate_saved(destination,rows,identity)
        slide,text=Slide.load(destination/'slide.npz'),TextEmbeddings.load(destination/'text.npz')
        if (any(slide.metadata.get(k)!=v for k,v in meta.items() if k!='model') or meta['data_provider']!='radboud' or meta['project']!='PANDA' or
                meta['isup_grade']!=int(row['isup_grade']) or meta['cohort_split']!=row['split'] or
                meta['extraction']['sampling_mode']!='representative' or meta['extraction']['selection_uses_mask']):
            raise ValueError('Saved metadata/labels/splits or unbiased sampling provenance mismatch')
        if fingerprint is not None and text.fingerprint()!=fingerprint:
            raise ValueError('Cohort text/model fingerprints differ')
        fingerprint=text.fingerprint()
        records.append(dict(image_id=sid,split=row['split'],tiles=len(rows),dimensions=slide.feats.shape[1],
            slurm_job_id=receipt['slurm_job_id'],completion_sha256=file_sha256(destination/'completion.json'),
            artifact_sha256=receipt['artifact_sha256']))
    report=dict(source_kind='real',category='PANDA embedding artifact verification; no predictions',
        slides=len(records),tiles=sum(r['tiles'] for r in records),dimensions=512,
        manifest_sha256=file_sha256(manifest),text_fingerprint=fingerprint,
        test_slides_scored=False,clinical_validity_verified=False,
        verification_slurm_job_id=os.environ['SLURM_JOB_ID'],records=records)
    write_json(output,report)
    return report


def encode_batch(directories, prompts_path, checkpoint, output, *, checkpoint_sha256, batch_size=16):
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('CONCH batch encoding requires an approved Slurm GPU job')
    import torch
    if torch.cuda.device_count()!=1 or not torch.cuda.is_available():
        raise ValueError('Exactly one scheduled CUDA GPU required')
    torch.set_num_threads(4)
    torch.manual_seed(0)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    if not 1<=len(directories)<=120 or file_sha256(checkpoint)!=checkpoint_sha256:
        raise ValueError('Bounded slide list and pinned checkpoint required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    contract=encoding_contract()
    records=[]
    seen=set()
    for directory in map(Path,directories):
        rows,identity=input_identity(directory,prompts_path,checkpoint_sha256,contract)
        meta=json.loads((directory/'metadata.json').read_text())
        if meta['source_kind']!='real' or meta['project']!='PANDA':
            raise ValueError('Only verified real PANDA tiling inputs are accepted')
        if not re.fullmatch(r'[0-9a-f]{32}',meta['slide_id']) or meta['slide_id'] in seen:
            raise ValueError('Distinct official PANDA slide IDs required')
        seen.add(meta['slide_id'])
        # Each sampling mode has its own output root; never mix donor enrichment into clean evaluation.
        destination=output/meta['slide_id']
        if destination.exists():
            receipt=validate_saved(destination,rows,identity)
            records.append(dict(image_id=meta['slide_id'],status='reused_validated',tiles=len(rows)))
            continue
        started=time.perf_counter()
        encode_tiles(directory/'tiles.csv',directory/'metadata.json',prompts_path,checkpoint,destination,
                     max_tiles=1024,batch_size=batch_size)
        receipt=dict(input_identity=identity,slurm_job_id=os.environ['SLURM_JOB_ID'],
            elapsed_seconds=time.perf_counter()-started,
            sampling_mode=meta['extraction']['sampling_mode'],cohort_split=meta.get('cohort_split','engineering'),
            artifact_sha256={n:file_sha256(destination/n) for n in ('slide.npz','text.npz','timing.json')})
        write_json(destination/'completion.json',receipt)
        validate_saved(destination,rows,identity)
        records.append(dict(image_id=meta['slide_id'],status='encoded_validated',tiles=len(rows)))
        print(json.dumps(records[-1]),flush=True)
    return records
