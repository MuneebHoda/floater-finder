"""Synthetic arrays stay inside temporary software checks; no validation results."""
import csv
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from conftest import MODEL
from floater_finder.artifacts import Slide,TextEmbeddings,write_json
from floater_finder.experiments import file_sha256
from floater_finder.panda_encoding import input_identity
from floater_finder.predictors.fresh import frozen_inputs,load_fresh,score_sources,run

PROJECT=Path(__file__).resolve().parents[1]
BUNDLE=PROJECT/'configs/panda_fresh_baseline_v1'


def test_real_preparation_has_exact_membership_bytes_and_no_predictions(monkeypatch):
    from floater_finder.predictors.linear_probe import FrozenPredictor
    def forbidden(*args,**kwargs):raise AssertionError('Preflight must not score')
    monkeypatch.setattr(FrozenPredictor,'__call__',forbidden)
    p,rows,models=frozen_inputs(BUNDLE/'protocol.json',file_sha256(BUNDLE/'protocol.json'),PROJECT)
    assert len(rows)==60 and len(models)==4 and len(p['excluded_slide_ids'])==129
    assert all(r['split']=='engineering' and r['candidate_split']=='fresh_development_validation' for r in rows)
    plan=json.loads((BUNDLE/'acquisition.json').read_text())
    assert plan['approval_required'] and len(plan['files'])==120
    assert sum(r['bytes'] for r in plan['files'])==1348184402
    spec=importlib.util.spec_from_file_location('fresh_acquire_fixture',PROJECT/'scripts/panda_acquire.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.validate_plan(plan)==plan


def test_protocol_and_manifest_changes_block_before_scoring(tmp_path):
    with pytest.raises(ValueError,match='protocol changed'):frozen_inputs(BUNDLE/'protocol.json','wrong',PROJECT)
    (tmp_path/'manifest.csv').write_bytes((BUNDLE/'manifest.csv').read_bytes()+b'\n')
    (tmp_path/'protocol.json').write_bytes((BUNDLE/'protocol.json').read_bytes())
    with pytest.raises(ValueError,match='manifest changed'):
        frozen_inputs(tmp_path/'protocol.json',file_sha256(tmp_path/'protocol.json'),PROJECT)


def fixture_inputs(tmp_path,**changes):
    # Fake real-contract metadata only tests guards, never records scientific evidence.
    sid='f'*32;directory=tmp_path/'tiles'/sid;directory.mkdir(parents=True)
    manifest=tmp_path/'manifest.csv';manifest.write_text('image_id,isup_grade\n'+sid+',0\n')
    model=MODEL|{'checkpoint_sha256':'0'*64}
    metadata=dict(slide_id=sid,patient_id='unknown',project='PANDA',organ='prostate',coordinate_units='microns',
        microns_per_unit=1,split='dev',source_kind='real',data_provider='radboud',isup_grade=0,
        cohort_split='engineering',selection_manifest_sha256=file_sha256(manifest),train_csv_sha256='a'*64,
        requested_field_um=112.,export_pixels=224,
        extraction=dict(max_tiles=512,sampling_mode='representative',selection_uses_mask=False,seed=20261020,
            max_candidates=20000,min_tissue_fraction=.1))
    metadata.update(changes)
    write_json(directory/'metadata.json',metadata)
    (directory/'tiles.csv').write_text('tile_id,path,x,y\nt,t.png,0,1\n')
    (directory/'t.png').write_bytes(b'fixture-only payload; no image inference')
    write_json(directory/'completion.json',dict(sha256={n:file_sha256(directory/n) for n in ('tiles.csv','metadata.json','t.png')}))
    prompt=tmp_path/'prompts';prompt.write_text('fixture-only')
    _,identity=input_identity(directory,prompt,model['checkpoint_sha256'])
    encoded=tmp_path/'encoded';out=encoded/sid;out.mkdir(parents=True)
    Slide(np.eye(1,512),np.array([[0.,1.]]),np.array(['t']),dict(metadata,model=model)).save(out/'slide.npz')
    phrases={c:[c+' fixture '+str(i) for i in range(3)] for c in ('benign','cancer')}
    text=TextEmbeddings(np.eye(2,512),list(phrases),phrases,model,'real');text.save(out/'text.npz')
    write_json(out/'timing.json',{})
    hashes={n:file_sha256(out/n) for n in ('slide.npz','text.npz','timing.json')}
    write_json(out/'completion.json',dict(input_identity=identity,artifact_sha256=hashes))
    record=dict(image_id=sid,split='engineering',tiles=1,completion_sha256=file_sha256(out/'completion.json'),artifact_sha256=hashes)
    verification=tmp_path/'verification.json'
    write_json(verification,dict(source_kind='real',manifest_sha256=file_sha256(manifest),slides=1,text_fingerprint=text.fingerprint(),records=[record]))
    directories=tmp_path/'directories.json';write_json(directories,[str(directory)])
    protocol=dict(excluded_slide_ids=['e'*32],manifest_sha256=file_sha256(manifest),prompts_sha256=file_sha256(prompt),
        train_sha256='a'*64,text_fingerprint=text.fingerprint(),embedding_model=model)
    return protocol,[dict(image_id=sid,isup_grade='0')],manifest,directories,encoded,verification


def test_fresh_loader_accepts_verified_fixture_and_rejects_corrupt_hash(tmp_path):
    args=fixture_inputs(tmp_path)
    loaded=load_fresh(*args)
    assert len(loaded)==1 and loaded[0]['grade']==0
    target=args[4]/('f'*32)/'timing.json';target.write_text('corrupt fixture')
    with pytest.raises(ValueError,match='checksum'):load_fresh(*args)


@pytest.mark.parametrize('changes',[
    dict(cohort_split='test'),dict(data_provider='karolinska'),dict(isup_grade=1),
    dict(requested_field_um=224.),dict(extraction=dict(max_tiles=512,sampling_mode='donor',selection_uses_mask=True,
        seed=20261020,max_candidates=20000,min_tissue_fraction=.1))])
def test_semantic_spoofing_rejected_even_with_consistent_file_hashes(tmp_path,changes):
    with pytest.raises(ValueError,match='provenance'):load_fresh(*fixture_inputs(tmp_path,**changes))


def test_original_test_id_rejected_before_any_input_is_read():
    with pytest.raises(ValueError,match='original test'):
        load_fresh(dict(excluded_slide_ids=['original-test']),[dict(image_id='original-test')],None,None,None,None)


def test_incomplete_receipt_blocks_before_any_arrays_are_opened(tmp_path,monkeypatch):
    args=fixture_inputs(tmp_path)
    receipt=json.loads(args[-1].read_text());receipt['records']=[];args[-1].write_text(json.dumps(receipt))
    monkeypatch.setattr(Slide,'load',lambda *a:pytest.fail('No arrays may open for incomplete membership'))
    with pytest.raises(ValueError,match='Missing/extra'):load_fresh(*args)


def test_scorer_tasks_keep_benign_out_of_grade_and_never_fit():
    def model(classes):
        return SimpleNamespace(spec=dict(classes=classes),score_slide=lambda s:dict(prediction=classes[0],
            scores=dict.fromkeys(classes,0.),positive_probability=None))
    models={(task,role):model(classes) for task,classes in (('benign_cancer',['benign','cancer']),
        ('low_high',['low_grade','high_grade'])) for role in ('primary','historical')}
    sources=[dict(image_id=f'fixture-{g}',grade=g,slide=SimpleNamespace(feats=np.ones((1,2)))) for g in (0,1,4)]
    predictions,summaries=score_sources(sources,models,20261024)
    assert len(predictions['benign_cancer/primary'])==3 and len(predictions['low_high/primary'])==2
    assert summaries['benign_cancer/primary']['class_support']==[1,2]
    assert summaries['low_high/primary']['classes']==['low_grade','high_grade']


def test_execution_opt_in_slurm_and_single_output_guards(tmp_path,monkeypatch):
    with pytest.raises(RuntimeError,match='execute-fresh'):run(*([None]*8))
    monkeypatch.delenv('SLURM_JOB_ID',raising=False)
    with pytest.raises(RuntimeError,match='CPU Slurm'):run(*([None]*8),execute=True)
    monkeypatch.setenv('SLURM_JOB_ID','fixture-only')
    with pytest.raises(FileExistsError,match='Single execution'):
        run(None,None,None,None,None,None,tmp_path,None,execute=True)
