#!/usr/bin/env python3
"""Checkpointable CPU tiling for an explicit slice of a versioned PANDA manifest."""
import argparse,csv,json,os
from pathlib import Path
from floater_finder.artifacts import write_json
from floater_finder.experiments import file_sha256
from floater_finder.panda import extract_panda_tiles,panda_input,panda_readers
from floater_finder.panda_masks import audit_mask
import floater_finder.panda as adapter


def run(root,manifest,output,start=0,count=10,max_tiles=512,selection='representative',mask_exclusions_path=None):
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('Cohort tiling requires an authorized Slurm CPU job')
    if not 0<=start<120 or not 1<=count<=10 or max_tiles not in (256,512):
        raise ValueError('Explicit bounded slice of at most ten slides required')
    if selection not in ('representative','donor'):
        raise ValueError('Separate representative and donor output roots required')
    with Path(manifest).open(newline='') as handle:
        rows=list(csv.DictReader(handle))
    if not 1<=len(rows)<=120 or len({r['image_id'] for r in rows})!=len(rows):
        raise ValueError('Invalid bounded unique cohort manifest')
    chosen=rows[start:start+count]
    if not chosen:raise ValueError('Empty cohort slice')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    exclusions=json.loads(Path(mask_exclusions_path).read_text()) if mask_exclusions_path else {}
    records=[]
    for row in chosen:
        sid=row['image_id']
        exclusion=exclusions.get(sid)
        item=panda_input(root,sid,manifest,exclusion)
        if row.get('mask_file') and item['mask_path'] is None and not exclusion:
            raise ValueError('Planned mask acquisition is incomplete')
        if selection=='donor' and item['isup_grade']<4:
            continue
        identity=dict(manifest_sha256=file_sha256(manifest),adapter_sha256=file_sha256(adapter.__file__),
            runner_sha256=file_sha256(__file__),
            image_sha256=file_sha256(item['image_path']),mask_sha256=file_sha256(item['original_mask_path']) if item['original_mask_path'] else None,
            max_tiles=max_tiles,selection=selection,field_um=112.,pixels=224,max_candidates=20000,
            min_tissue_fraction=.1,seed=20261020,min_gp45_fraction=.01)
        if exclusion:identity['mask_exclusion']=exclusion
        directory=output/sid
        if directory.exists():
            receipt=json.loads((directory/'completion.json').read_text())
            if receipt['input_identity']!=identity or any(file_sha256(directory/n)!=h for n,h in receipt['sha256'].items()):
                raise ValueError('Completed tiling differs from its inputs or hashes; preserved for inspection')
            records.append(dict(image_id=sid,status='reused_validated',tiles=receipt['tiles']))
            continue
        with panda_readers(item['image_path'],item['mask_path']) as (_,mask,provenance):
            native_audit=audit_mask(mask,provenance['measured_mpp_xy']) if mask is not None else None
        if exclusion:native_audit=dict(status='unusable_mask_excluded',excluded_mask=item['excluded_mask'])
        result=extract_panda_tiles(root,sid,directory,manifest_path=manifest,selection=selection,
                                  max_tiles=max_tiles,max_candidates=20000,mask_exclusion=exclusion)
        write_json(directory/'mask_audit.json',native_audit)
        receipt=dict(input_identity=identity,tiles=result['tiles'],slurm_job_id=os.environ['SLURM_JOB_ID'],
            sha256={p.name:file_sha256(p) for p in sorted(directory.iterdir()) if p.is_file()})
        write_json(directory/'completion.json',receipt)
        records.append(dict(image_id=sid,status='tiled_validated',tiles=result['tiles']))
        print(json.dumps(records[-1]),flush=True)
    return records


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('root','manifest','output'):p.add_argument('--'+key,required=True)
    p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int,default=10)
    p.add_argument('--max-tiles',type=int,choices=(256,512),default=512)
    p.add_argument('--selection',choices=('representative','donor'),default='representative')
    p.add_argument('--mask-exclusions',help='Explicit versioned SHA256-bound exclusion reasons; no automatic fallback')
    a=p.parse_args();run(a.root,a.manifest,a.output,a.start,a.count,a.max_tiles,a.selection,a.mask_exclusions)
