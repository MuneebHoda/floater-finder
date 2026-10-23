#!/usr/bin/env python3
"""Prepare a bounded cohort GPU input list and reuse exactly matching saved artifacts."""
import argparse,csv,json,shutil
from pathlib import Path
from floater_finder.artifacts import write_json
from floater_finder.experiments import file_sha256
from floater_finder.panda_encoding import encoding_contract,validate_saved


def prepare(manifest,cohort_tiles,profile_tiles,profile_embeddings,prompts,output_root,directories_output,checkpoint_sha256):
    with Path(manifest).open(newline='') as f:cohort=list(csv.DictReader(f))
    if len(cohort) not in (60,120) or len({r['image_id'] for r in cohort})!=len(cohort):raise ValueError('Fixed unique cohort required')
    output_root=Path(output_root);output_root.mkdir(parents=True,exist_ok=False)
    contract=encoding_contract();directories=[];records=[]
    for row in cohort:
        sid=row['image_id'];target=Path(cohort_tiles)/sid
        prepared=json.loads((target/'completion.json').read_text());meta=json.loads((target/'metadata.json').read_text())
        assert meta['cohort_split']==row['split'] and meta['isup_grade']==int(row['isup_grade'])
        source=Path(profile_embeddings)/sid;old_tiles=Path(profile_tiles)/sid/'representative'
        reused=False
        if (source/'completion.json').is_file():
            receipt=json.loads((source/'completion.json').read_text());identity=receipt['input_identity']
            old_meta=json.loads((old_tiles/'metadata.json').read_text())
            with (old_tiles/'tiles.csv').open(newline='') as f:old_rows=list(csv.DictReader(f))
            assert identity['checkpoint_sha256']==checkpoint_sha256
            assert identity['encoding_contract']==contract and identity['prompts_sha256']==file_sha256(prompts)
            assert file_sha256(old_tiles/'metadata.json')==identity['metadata_sha256']
            assert file_sha256(old_tiles/'tiles.csv')==identity['manifest_sha256']==prepared['sha256']['tiles.csv']
            assert old_meta['cohort_split']==row['split'] and old_meta['isup_grade']==int(row['isup_grade'])
            for tile in old_rows:
                assert identity['png_sha256'][tile['tile_id']]==prepared['sha256'][tile['path']]
            validate_saved(source,old_rows,identity)
            destination=output_root/sid;destination.mkdir()
            for name in ('slide.npz','text.npz','timing.json','completion.json'):shutil.copy2(source/name,destination/name)
            validate_saved(destination,old_rows,identity)
            target=old_tiles;reused=True
        directories.append(str(target))
        records.append(dict(image_id=sid,input_directory=str(target),reused_profile=reused,tiles=prepared['tiles'],
            cohort_tiling_completion_sha256=file_sha256(Path(cohort_tiles)/sid/'completion.json')))
    write_json(directories_output,directories)
    report=dict(category='Prepared inputs; no new GPU inference',cohort_manifest_sha256=file_sha256(manifest),
        source_cohort_tiles=str(cohort_tiles),profile_source=str(profile_embeddings),output_root=str(output_root),
        total_slides=len(records),total_tiles=sum(r['tiles'] for r in records),
        reused_slides=sum(r['reused_profile'] for r in records),reused_tiles=sum(r['tiles'] for r in records if r['reused_profile']),
        new_slides=sum(not r['reused_profile'] for r in records),new_tiles=sum(r['tiles'] for r in records if not r['reused_profile']),
        directories_sha256=file_sha256(directories_output),
        reuse_scope='Matching recorded PNG hashes, CSV, IDs/coordinates, labels/splits and model/runtime/prompts; encoder rechecks current PNG bytes before reuse',
        records=records)
    write_json(str(directories_output)+'.provenance.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','cohort-tiles','profile-tiles','profile-embeddings','prompts','output-root','directories-output','checkpoint-sha256'):p.add_argument('--'+name,required=True)
    a=p.parse_args();prepare(a.manifest,a.cohort_tiles,a.profile_tiles,a.profile_embeddings,a.prompts,a.output_root,a.directories_output,a.checkpoint_sha256)
