
import csv,hashlib,itertools,json,os
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from floater_finder.panda import panda_readers
ROOT=Path('/work/nvme/bfqi/mhoda/panda')
OUTPUT=ROOT/'annotated_cohort.csv'
SEED=20261020
GROUPS=['benign','gg1','high_grade']
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def select(candidates):
    selected=[]
    for group in GROUPS:
        pool=[r.copy() for r in candidates if r['group']==group]
        pool.sort(key=lambda r:(not r['mask_available'],hashlib.sha256(f"{SEED}:select:{group}:{r['image_id']}".encode()).hexdigest()))
        chosen=pool[:20]
        chosen.sort(key=lambda r:hashlib.sha256(f"{SEED}:split:{group}:{r['image_id']}".encode()).hexdigest())
        for index,row in enumerate(chosen):
            row['split']='train' if index<12 else ('calibration' if index<16 else 'test')
            selected.append(row)
    return selected
# Software-only quota/determinism check; these artificial IDs are never written to the manifest.
fixture=[dict(image_id=f'fixture-{g}-{i}',group=g,mask_available=i%2==0) for g in GROUPS for i in range(25)]
check=select(fixture)
assert check==select(list(reversed(fixture))) and len(check)==60
for g in GROUPS: assert Counter(r['split'] for r in check if r['group']==g)=={'train':12,'calibration':4,'test':4}
assert not OUTPUT.exists(),'Existing annotated_cohort.csv preserved; inspect it before changing anything'
assert not Path(str(OUTPUT)+'.selection_provenance.json').exists()
pilot_before=digest(ROOT/'pilot.csv')
with (ROOT/'train.csv').open(newline='') as f:
    reader=csv.DictReader(f); columns=reader.fieldnames; metadata=list(itertools.islice(reader,20001))
assert len(metadata)<=20000
assert len({r['image_id'] for r in metadata})==len(metadata)
by_id={r['image_id']:r for r in metadata}
with os.scandir(ROOT/'train_images') as entries: files=list(itertools.islice(entries,201))
assert len(files)<=200,'Available-file scan exceeded 200 entries'
available={}
for entry in files:
    p=Path(entry.path)
    if entry.is_file(follow_symlinks=False) and p.suffix.lower() in ['.tif','.tiff']:
        available.setdefault(p.stem,[]).append(p)
candidates=[]; exclusions=[]
for image_id,paths in sorted(available.items()):
    row=by_id.get(image_id)
    if row is None or row.get('data_provider')!='radboud': continue
    grade=int(row['isup_grade'])
    group='benign' if grade==0 else ('gg1' if grade==1 else ('high_grade' if grade in [4,5] else None))
    if group is None: continue
    if len(paths)!=1:
        exclusions.append({'image_id':image_id,'reason':'ambiguous WSI filenames'});continue
    masks=[ROOT/'train_label_masks'/(stem+suffix) for stem in [image_id+'_mask',image_id] for suffix in ['.tiff','.tif'] if (ROOT/'train_label_masks'/(stem+suffix)).is_file()]
    if len(masks)>1:
        exclusions.append({'image_id':image_id,'reason':'ambiguous mask filenames'});continue
    mask=masks[0] if masks else None
    try:
        with panda_readers(paths[0],mask) as (image,mask_reader,header):
            mpp=header['measured_mpp_xy']; dims=header['pyramid_dimensions'][0]
    except Exception as error:
        exclusions.append({'image_id':image_id,'reason':type(error).__name__+': '+str(error)[:300]});continue
    patient=row.get('patient_id','').strip()
    candidates.append({'image_id':image_id,'data_provider':'radboud','isup_grade':grade,'gleason_score':row['gleason_score'],'group':group,'patient_id':patient,'patient_id_source':'train.csv patient_id' if patient else 'not supplied by PANDA train.csv','wsi_path':str(paths[0]),'mask_path':str(mask) if mask else '', 'mask_available':mask is not None,'wsi_bytes':paths[0].stat().st_size,'mask_bytes':mask.stat().st_size if mask else '', 'mpp_x_um':mpp[0],'mpp_y_um':mpp[1],'width_level0':dims[0],'height_level0':dims[1],'wsi_header_verified':True,'mask_alignment_verified':True if mask else '', 'selection_seed':SEED})
selected=select(candidates)
assert len({r['image_id'] for r in selected})==len(selected)
patients={}
for row in selected:
    if row['patient_id']:
        previous=patients.setdefault(row['patient_id'],row['split'])
        assert previous==row['split'],'Patient crosses splits; no manifest written'
counts={g:{'eligible_available':sum(r['group']==g for r in candidates),'selected':sum(r['group']==g for r in selected),'with_mask':sum(r['group']==g and r['mask_available'] for r in selected),'splits':dict(Counter(r['split'] for r in selected if r['group']==g)),'shortfall':20-sum(r['group']==g for r in selected)} for g in GROUPS}
assert selected,'No eligible real files; no empty manifest written'
for row in selected:
    assert row['image_id'] in by_id and row['isup_grade']==int(by_id[row['image_id']]['isup_grade'])
    assert Path(row['wsi_path']).is_file() and (not row['mask_available'] or Path(row['mask_path']).is_file())
assert digest(ROOT/'pilot.csv')==pilot_before
os.umask(0o077)
with OUTPUT.open('x',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(selected[0]));writer.writeheader();writer.writerows(selected)
with OUTPUT.open(newline='') as f: written=list(csv.DictReader(f))
assert len(written)==len(selected) and len({r['image_id'] for r in written})==len(written)
assert digest(ROOT/'pilot.csv')==pilot_before
complete=len(selected)==60 and all(counts[g]['splits']=={'train':12,'calibration':4,'test':4} for g in GROUPS)
record={'created_utc':datetime.now(timezone.utc).isoformat(),'status':'complete_balanced_cohort' if complete else 'insufficient_available_cases_partial_manifest','manifest':str(OUTPUT),'manifest_sha256':digest(OUTPUT),'seed':SEED,'selection':'Within each group: valid-mask-first, seeded SHA-256 tie order; retain up to 20; independent seeded SHA-256 split order with quotas 12/4/4','train_csv':str(ROOT/'train.csv'),'train_csv_sha256':digest(ROOT/'train.csv'),'metadata_columns':columns,'metadata_rows':len(metadata),'pilot_preserved_sha256':pilot_before,'all_available_tiff_file_count':sum(len(v) for v in available.values()),'groups':counts,'selected_total':len(selected),'mask_coverage':{'with_mask':sum(r['mask_available'] for r in selected),'total':len(selected)},'patient_ids_available':sum(bool(r['patient_id']) for r in selected),'patient_leakage_verification':'No patient IDs supplied; biopsy IDs are not patient identities. All currently selected rows are training-only.','ready_as_60_slide_cohort':complete,'individual_inputs_header_validated':True,'embedding_run':False,'new_downloads':False,'jobs_submitted_by_selection':False,'exclusions':exclusions,'candidate_inventory_sha256':hashlib.sha256(json.dumps(candidates,sort_keys=True).encode()).hexdigest(),'selector_self_check':'60 artificial records selected with exact 12/4/4 group quotas; determinism passed; no fixture IDs written','selection_recipe_sha256':digest(__file__)}
with Path(str(OUTPUT)+'.selection_provenance.json').open('x') as f: json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(record,indent=2),flush=True)
