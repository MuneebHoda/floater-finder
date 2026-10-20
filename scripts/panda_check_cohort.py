#!/usr/bin/env python3
"""Bounded metadata-only verification of completed PANDA tiling and native-mask audits."""
import argparse,csv,json,math
from pathlib import Path
from collections import Counter
from floater_finder.artifacts import write_json
from floater_finder.experiments import file_sha256


def check(manifest,tiles,receipts,output):
    with Path(manifest).open(newline='') as f:cohort=list(csv.DictReader(f))
    if len(cohort) not in (60,120) or len({r['image_id'] for r in cohort})!=len(cohort):raise ValueError('Complete fixed cohort required')
    records=[]
    for row in cohort:
        d=Path(tiles)/row['image_id'];completion=json.loads((d/'completion.json').read_text())
        meta=json.loads((d/'metadata.json').read_text());audit=json.loads((d/'mask_audit.json').read_text())
        for name in ('metadata.json','tiles.csv','mask_audit.json'):
            assert file_sha256(d/name)==completion['sha256'][name],f'Changed prepared metadata: {row["image_id"]}'
        for role in ('image','mask'):
            source=json.loads((Path(receipts)/(Path(row[role+'_file']).name+'.json')).read_text())
            assert completion['input_identity'][role+'_sha256']==source['sha256'],'Acquisition/tiling input hash mismatch'
        with (d/'tiles.csv').open(newline='') as f:data=list(csv.DictReader(f))
        assert 1<=len(data)<=512 and len(data)==completion['tiles']
        assert len({r['tile_id'] for r in data})==len(data)==len({r['path'] for r in data})
        assert all(r['path'] in completion['sha256'] for r in data)
        assert meta['image_id']==row['image_id'] and meta['isup_grade']==int(row['isup_grade']) and meta['cohort_split']==row['split']
        assert meta['extraction']['sampling_mode']=='representative' and not meta['extraction']['selection_uses_mask']
        assert meta['extraction']['candidates_examined']==meta['extraction']['total_grid_cells']
        known=meta['panda']['mask_available'];gp45=0 if known else None;cancer=0 if known else None;captured=0.
        for tile in data:
            x,y=float(tile['x']),float(tile['y']);area=float(tile['area_mm2'])
            assert all(math.isfinite(v) for v in (x,y,area)) and area>0
            assert math.isclose(x,int(tile['x_level0'])*meta['measured_mpp_xy'][0],abs_tol=1e-9)
            assert math.isclose(y,int(tile['y_level0'])*meta['measured_mpp_xy'][1],abs_tol=1e-9)
            assert math.isclose(area,meta['tile_size'][0]*meta['tile_size'][1]/1e6,abs_tol=1e-12)
            values=[tile[k+'_fraction'] for k in ('background','stroma','benign','gleason3','gleason4','gleason5')]
            if known:
                values=list(map(float,values));assert all(0<=v<=1 for v in values) and math.isclose(sum(values),1,abs_tol=1e-10)
                gp45+=values[4]+values[5]>0;cancer+=sum(values[3:])>0;captured+=(values[4]+values[5])*area
            else:assert all(v=='' for v in values),'Unknown annotation cannot become zeros'
        if known:
            assert sum(audit['native_pixel_counts'].values())==math.prod(audit['dimensions'])
            native_area=audit['area_mm2']['gleason4']+audit['area_mm2']['gleason5']
            assert captured<=native_area+1e-10
        else:
            assert audit['status']=='unusable_mask_excluded' and meta['panda']['excluded_mask'];native_area=None
        records.append(dict(image_id=row['image_id'],group=row['group'],split=row['split'],isup_grade=int(row['isup_grade']),
            tiles=len(data),mask_usable=known,gp45_positive_native_mask=audit.get('gp45_positive') if known else None,
            gp45_positive_tiles=gp45,cancer_positive_tiles=cancer,native_gp45_area_mm2=native_area,
            captured_gp45_area_mm2=captured if known else None,
            gp45_annotation_capture_fraction=captured/native_area if native_area else None,
            tiling_completion_sha256=file_sha256(d/'completion.json'),slurm_job_id=completion['slurm_job_id']))
    report=dict(source_kind='real',category='PANDA data/CPU verification; cancer model not evaluated',
        manifest_sha256=file_sha256(manifest),slides=len(records),groups=dict(Counter(r['group'] for r in records)),
        mask_usable=sum(r['mask_usable'] for r in records),mask_excluded=sum(not r['mask_usable'] for r in records),
        representative_tiles=sum(r['tiles'] for r in records),
        high_grade_gp45_positive_masks=sum(r['group']=='high_grade' and r['gp45_positive_native_mask'] is True for r in records),
        positive_labelled_slides_with_no_cancer_in_sample=[r['image_id'] for r in records if r['isup_grade']>0 and r['cancer_positive_tiles']==0],
        patient_independence_verified=False,png_bytes_recheck='All creation hashes recorded; encoder rechecks prepared hashes before use',
        records=records)
    write_json(output,report);print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','tiles','receipts','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();check(a.manifest,a.tiles,a.receipts,a.output)
