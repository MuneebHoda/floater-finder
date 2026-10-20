import importlib.util
import json
from pathlib import Path
import numpy as np
import pytest
from floater_finder.artifacts import Slide,TextEmbeddings,write_json
from floater_finder.experiments import file_sha256
from floater_finder.panda_encoding import input_identity,validate_saved
from conftest import MODEL


def test_embedding_resume_rejects_changed_inputs_and_corrupt_artifacts(tmp_path):
    d=tmp_path/'tiles';d.mkdir()
    (d/'tile.png').write_bytes(b'software fixture only')
    (d/'tiles.csv').write_text('tile_id,path,x,y\nt,tile.png,0,1\n')
    (d/'metadata.json').write_text('{}')
    prompts=tmp_path/'prompts.yaml';prompts.write_text('fixture')
    # Synthetic arrays simulate the real artifact contract only inside this unit test.
    model=MODEL|{'checkpoint_sha256':'0'*64}
    rows,identity=input_identity(d,prompts,model['checkpoint_sha256'],{'version':'fixture'})
    out=tmp_path/'encoded';out.mkdir()
    metadata=dict(slide_id='fixture',patient_id='unknown',project='PANDA',organ='prostate',
                  coordinate_units='microns',split='dev',source_kind='real',model=model)
    Slide(np.eye(1,512),np.array([[0.,1.]]),np.array(['t']),metadata).save(out/'slide.npz')
    phrases={c:[c+' fixture '+str(i) for i in range(3)] for c in ('benign','cancer')}
    TextEmbeddings(np.eye(2,512),list(phrases),phrases,model,'real').save(out/'text.npz')
    write_json(out/'timing.json',{})
    write_json(out/'completion.json',dict(input_identity=identity,artifact_sha256={n:file_sha256(out/n) for n in ('slide.npz','text.npz','timing.json')}))
    assert validate_saved(out,rows,identity)['input_identity']==identity
    (d/'tile.png').write_bytes(b'changed')
    _,changed=input_identity(d,prompts,model['checkpoint_sha256'],{'version':'fixture'})
    with pytest.raises(ValueError,match='inputs/model'):validate_saved(out,rows,changed)
    (out/'timing.json').write_text('changed')
    with pytest.raises(ValueError,match='checksum'):validate_saved(out,rows,identity)


def test_acquisition_plan_requires_consistent_exact_file_membership():
    path=Path(__file__).resolve().parents[1]/'scripts/panda_acquire.py'
    spec=importlib.util.spec_from_file_location('panda_acquire',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    rows=[dict(name=f'train_images/{i:032x}.tiff',image_id=f'{i:032x}',role='image',bytes=100) for i in range(60)]
    assert module.validate_plan(dict(slides=60,files=rows))['slides']==60
    with pytest.raises(ValueError):module.validate_plan(dict(slides=60,files=rows[:-1]))
    rows[0]['name']='../escape.tiff'
    with pytest.raises(ValueError):module.validate_plan(dict(slides=60,files=rows))


def test_selective_acquisition_resumes_and_preserves_existing_bytes(tmp_path,monkeypatch):
    import sys,types,zipfile
    path=Path(__file__).resolve().parents[1]/'scripts/panda_acquire.py'
    spec=importlib.util.spec_from_file_location('panda_acquire_resume',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    root=tmp_path/'data';(root/'train_images').mkdir(parents=True)
    payload=b'bounded software-fixture payload only'
    files=[dict(name=f'train_images/{i:032x}.tiff',image_id=f'{i:032x}',role='image',bytes=len(payload)) for i in range(60)]
    for row in files[1:]:(root/row['name']).write_bytes(payload)
    plan=tmp_path/'plan.json';plan.write_text(json.dumps(dict(slides=60,files=files)))
    calls=[]
    class Fake:
        def authenticate(self):pass
        def competition_download_file(self,competition,name,path,quiet):
            calls.append(name)
            with zipfile.ZipFile(Path(path)/(Path(name).name+'.zip'),'w') as archive:
                archive.writestr(Path(name).name,payload)
    monkeypatch.setitem(sys.modules,'kaggle.api.kaggle_api_extended',types.SimpleNamespace(KaggleApi=Fake))
    monkeypatch.setenv('SLURM_JOB_ID','fixture-only')
    with pytest.raises(ValueError,match='Approval hash'):
        module.acquire(plan,root,tmp_path/'receipts','wrong')
    assert not calls
    module.acquire(plan,root,tmp_path/'receipts',file_sha256(plan))
    module.acquire(plan,root,tmp_path/'receipts',file_sha256(plan))
    assert calls==[files[0]['name']]
    target=root/files[0]['name'];target.write_bytes(b'preserve my changed existing file')
    with pytest.raises(ValueError,match='preserved for inspection'):
        module.acquire(plan,root,tmp_path/'receipts',file_sha256(plan))
    assert target.read_bytes()==b'preserve my changed existing file'


def test_encoder_provenance_accepts_namespace_package_and_hashes_source(tmp_path,monkeypatch):
    import types
    from floater_finder import panda_encoding
    source=tmp_path/'model.py';source.write_text('# fixture code\n')
    monkeypatch.setattr(panda_encoding.importlib.util,'find_spec',lambda _:types.SimpleNamespace(origin=None,submodule_search_locations=[str(tmp_path)]))
    monkeypatch.setattr(panda_encoding.importlib.metadata,'version',lambda _:'fixture-version')
    before=panda_encoding.encoding_contract()
    assert before['upstream_source_sha256']=={'0/model.py':file_sha256(source)}
    source.write_text('# changed fixture code\n')
    assert panda_encoding.encoding_contract()!=before


def test_embedding_inputs_reject_changes_after_tiling_completion(tmp_path):
    (tmp_path/'tiles.csv').write_text('tile_id,path,x,y\nt,t.png,0,0\n')
    (tmp_path/'metadata.json').write_text('{}')
    (tmp_path/'t.png').write_bytes(b'fixture PNG payload')
    prompts=tmp_path/'prompts';prompts.write_text('fixture')
    expected={n:file_sha256(tmp_path/n) for n in ('tiles.csv','metadata.json','t.png')}
    write_json(tmp_path/'completion.json',dict(sha256=expected))
    _,identity=input_identity(tmp_path,prompts,'0'*64)
    assert identity['prepared_tiling_receipt_sha256']==file_sha256(tmp_path/'completion.json')
    (tmp_path/'t.png').write_bytes(b'changed fixture image')
    with pytest.raises(ValueError,match='changed before encoding'):
        input_identity(tmp_path,prompts,'0'*64)


def test_cohort_verification_checks_provenance_without_scoring_test_slides(tmp_path,monkeypatch):
    import csv
    from floater_finder import panda_encoding as encoding
    rows=[dict(image_id=f'{i:032x}',isup_grade=(0,1,4)[i//20],
               split='train' if i%20<12 else 'calibration' if i%20<16 else 'test') for i in range(60)]
    manifest=tmp_path/'fixture.csv'
    with manifest.open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    model=MODEL|{'checkpoint_sha256':'0'*64}
    phrases={c:[f'{c} fixture {i}' for i in range(3)] for c in ('benign','cancer','low_grade','high_grade')}
    text=TextEmbeddings(np.eye(4,512),list(phrases),phrases,model,'real')
    metadata={};directories=[];changed=False
    for r in rows:
        d=tmp_path/r['image_id'];d.mkdir();directories.append(d)
        m=dict(slide_id=r['image_id'],patient_id='unknown',organ='prostate',coordinate_units='microns',split='dev',
               project='PANDA',source_kind='real',data_provider='radboud',isup_grade=r['isup_grade'],
               cohort_split=r['split'],extraction=dict(sampling_mode='representative',selection_uses_mask=False))
        metadata[r['image_id']]=m
        write_json(d/'metadata.json',m)
    loaded=[]
    def load(path):
        sid=Path(path).parent.name;loaded.append(sid)
        m=metadata[sid]|{'model':model,'tile_selection':{'method':'canonical adapter adds this field'}}
        if changed:m=m|{'isup_grade':5}
        return Slide(np.eye(1,512),np.array([[0.,1.]]),np.array(['t']),m)
    monkeypatch.setenv('SLURM_JOB_ID','fixture-only')
    monkeypatch.setattr(encoding,'encoding_contract',lambda:{'fixture':True})
    monkeypatch.setattr(encoding,'input_identity',lambda *a:([{'tile_id':'t','x':'0','y':'1'}],{}))
    monkeypatch.setattr(encoding,'validate_saved',lambda *a:dict(slurm_job_id='fixture-encoder',artifact_sha256={}))
    monkeypatch.setattr(encoding.Slide,'load',load)
    monkeypatch.setattr(encoding.TextEmbeddings,'load',lambda _:text)
    monkeypatch.setattr(encoding,'file_sha256',lambda _:'0'*64)
    output=tmp_path/'fixture-verification.json'
    result=encoding.validate_batch(directories,'fixture-prompts','0'*64,tmp_path,manifest,output)
    assert result['slides']==60 and result['tiles']==60 and len(loaded)==60
    assert result['test_slides_scored'] is False and result['clinical_validity_verified'] is False
    changed=True
    with pytest.raises(ValueError,match='provenance mismatch'):
        encoding.validate_batch(directories,'fixture-prompts','0'*64,tmp_path,manifest,tmp_path/'rejected.json')
    assert not (tmp_path/'rejected.json').exists()
    with pytest.raises(ValueError,match='duplicated'):
        changed=False
        encoding.validate_batch([directories[0]]*60,'fixture-prompts','0'*64,tmp_path,manifest,tmp_path/'duplicate.json')
