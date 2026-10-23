"""Temporary software-contract fixtures, not scientific inputs or final evaluations."""
import json
from pathlib import Path
import numpy as np
import pytest
from floater_finder.experiments import file_sha256
from floater_finder.panda_final import preflight,require_execution,classification_summary,clustered_ratio_interval


def contract(tmp_path):
    source=tmp_path/'source';source.mkdir();(source/'code.py').write_text('# fixture')
    (tmp_path/'snapshot.json').write_text(json.dumps(dict(commit='fixture-source')))
    data=tmp_path/'data';data.mkdir();entries=[]
    for i in range(24):
        d=data/f'{i:032x}';d.mkdir();files={}
        for name in ('slide.npz','text.npz','timing.json','completion.json','tiles.csv','metadata.json','tile.png','image.tiff'):
            p=d/name;p.write_bytes(b'fixture bytes only, never decode');files[str(p)]=file_sha256(p)
        entries.append(dict(image_id=d.name,files=files,image_path=str(d/'image.tiff')))
    index=data/'blind.json';index.write_text(json.dumps(dict(entries=entries)))
    manifest=data/'manifest.csv';manifest.write_text('DO NOT DECODE TEST LABELS\n')
    verification=data/'verification.json';verification.write_text('{}')
    protocol=dict(schema_version=1,status='frozen',automatic_tissue_action='none',source=dict(commit='fixture-source',files={'code.py':file_sha256(source/'code.py')}),
        runtime_versions={},allowed_data_roots=[str(data)],data=dict(manifest=str(manifest),manifest_sha256=file_sha256(manifest),verification=str(verification),verification_sha256=file_sha256(verification),blinded_index=str(index),blinded_index_sha256=file_sha256(index)),
        test_ids=[r['image_id'] for r in entries],execution=dict(output=str(data/'final-output')),readiness=dict(operating_point_supported=False,reason='fixture unsupported'))
    path=tmp_path/'protocol.json';path.write_text(json.dumps(protocol))
    return path,source,protocol,entries


def test_preflight_hashes_only_and_never_loads_models_labels_or_feature_arrays(tmp_path,monkeypatch):
    path,source,protocol,entries=contract(tmp_path)
    monkeypatch.setattr(np,'load',lambda *a,**k:pytest.fail('Preflight decoded held-out arrays'))
    report=preflight(path,file_sha256(path),source)
    assert report['protocol_frozen'] and report['test_slides']==24
    assert not report['test_predictions_computed'] and not report['test_labels_decoded'] and not report['ready_for_final_predictions']
    assert not Path(protocol['execution']['output']).exists()
    Path(entries[0]['image_path']).write_bytes(b'changed fixture')
    with pytest.raises(ValueError,match='checksum mismatch'):preflight(path,file_sha256(path),source)


def test_preflight_and_execution_fail_closed_on_changed_protocol_source_or_reuse(tmp_path):
    path,source,protocol,entries=contract(tmp_path)
    with pytest.raises(ValueError,match='protocol checksum'):preflight(path,'0'*64,source)
    with pytest.raises(RuntimeError,match='explicit'):require_execution(protocol,False)
    with pytest.raises(RuntimeError,match='No supported'):require_execution(protocol,True)
    Path(protocol['execution']['output']).mkdir()
    with pytest.raises(FileExistsError,match='single execution'):preflight(path,file_sha256(path),source)
    Path(protocol['execution']['output']).rmdir();(source/'code.py').write_text('changed')
    with pytest.raises(ValueError,match='source file'):preflight(path,file_sha256(path),source)


def test_uncertainty_resamples_slides_and_preserves_zero_denominators():
    result=classification_summary([0,0,1,1],[0,1,1,1],repetitions=50)
    assert result['balanced_accuracy']==.75 and result['confusion_rows_truth_columns_prediction']==[[1,1],[0,2]]
    rows=[dict(host_id='A',hit=1,total=1),dict(host_id='A',hit=1,total=1),dict(host_id='B',hit=0,total=1)]
    interval=clustered_ratio_interval(rows,'hit','total',repetitions=50)
    assert interval['unique_host_slides']==2 and interval['estimate']==pytest.approx(2/3)
    assert clustered_ratio_interval([dict(host_id='A',hit=0,total=0)],'hit','total')['estimate'] is None


def test_final_runner_stops_before_labels_arrays_or_output_when_policy_is_unsupported(tmp_path,monkeypatch):
    from floater_finder.panda_final_run import evaluate_final
    from floater_finder import panda_final_run
    path,source,protocol,entries=contract(tmp_path)
    monkeypatch.setattr(panda_final_run,'load_sources',lambda *a,**k:pytest.fail('Unsealed final inputs'))
    with pytest.raises(RuntimeError,match='No supported'):evaluate_final(path,file_sha256(path),source,True)
    assert not Path(protocol['execution']['output']).exists()


def test_supported_final_workflow_with_software_fixtures_is_single_use(tmp_path,monkeypatch):
    # Everything below is artificial, temporary contract data. It is never a real held-out run.
    from PIL import Image
    from floater_finder.artifacts import Slide,TextEmbeddings
    from floater_finder import panda_final_run as runner
    from floater_finder.panda_topology import overview_components
    from conftest import MODEL
    sources={};phrases={c:[c+' fixture '+str(i) for i in range(3)] for c in ('benign','cancer','low_grade','high_grade')}
    text=TextEmbeddings(np.eye(4,512),list(phrases),phrases,MODEL,'fixture')
    for i in range(24):
        sid=f'{i:032x}';grade=0 if i<8 else 1 if i<16 else 4
        directory=tmp_path/sid;directory.mkdir();Image.new('RGB',(4,4),(150,70,130)).save(directory/'tile.png')
        f=np.zeros((20,512));f[:,0]=.9 if grade==0 else 0.;f[:,4]=np.sqrt(1-.9**2) if grade==0 else 0.
        if grade:f[:,1]=1
        coords=np.array([[100.*(j%5),100.*(j//5)] for j in range(20)])
        meta=dict(slide_id=sid,patient_id='unknown',patient_id_known=False,project='PANDA',organ='prostate',source_kind='fixture',
            coordinate_units='microns',microns_per_unit=1,tile_step=[100.,100.],tile_size=[100.,100.],split='eval',cohort_split='test',
            data_provider='radboud',isup_grade=grade,model=MODEL,panda={'mask_available':True})
        slide=Slide(f,coords,np.array([f't{j}' for j in range(20)]),meta)
        rows=[dict(tile_id=f't{j}',path='tile.png',gleason3_fraction='.5' if grade else '0',gleason4_fraction='0',gleason5_fraction='0') for j in range(20)]
        sources[sid]=dict(slide=slide,text=text,rows=rows,directory=directory,completion=dict(input_identity=dict(png_sha256={r['tile_id']:file_sha256(directory/'tile.png') for r in rows})),
            scores=np.einsum('id,cd->ic',f,text.feats)[:,:2],annotation_known=[True]*20,annotated_cancer=[bool(grade)]*20,split='test',host_truth='cancer' if grade else 'benign')
    def overview(source,config,receipts,output):
        mask=np.zeros((30,30),bool);mask[:5,:6]=True;scale=np.array([100.,100.])
        parts,q=overview_components(mask,source['slide'].coords,[100,100],scale)
        source.update(mask=mask,pixel_um=scale,components=parts,quality=q)
        return {'fixture_only':True}
    monkeypatch.setenv('SLURM_JOB_ID','fixture-only')
    monkeypatch.delenv('SLURM_JOB_GPUS',raising=False)
    monkeypatch.setattr(runner,'preflight',lambda *a:dict(ready_for_final_predictions=True))
    monkeypatch.setattr(runner,'load_sources',lambda *a:(sources,{}))
    monkeypatch.setattr(runner,'read_overview',overview)
    config=json.loads((Path(__file__).resolve().parents[1]/'configs/panda_review_development_v1.json').read_text())
    rules=dict(combined=dict(kind='combined',visual_threshold=.2,influence='flip',max_area_mm2=.05,min_isolation_mm=0),visual_only=dict(kind='visual',visual_threshold=.2),decision_only=dict(kind='decision'),spatial_only=dict(kind='spatial',max_area_mm2=.05,min_isolation_mm=0))
    protocol=dict(status='frozen',source={'commit':'fixture-only'},readiness={'operating_point_supported':True},execution={'output':str(tmp_path/'fixture-results')},
        data={k:'fixture-unused' for k in ('manifest','directories','encoded_root','verification','acquisition_receipts')},development_config=config,test_ids=list(sources),
        contamination=dict(minimum_total_cancer_fraction=.1,percentages=[0,.5,1,2,5,10],seed=20261020),review_policy={'rules':rules})
    path=tmp_path/'fixture-protocol.json';path.write_text(json.dumps(protocol))
    result=runner.evaluate_final(path,file_sha256(path),tmp_path,True)
    assert result['classification']['slides']==24 and result['positive_mixtures']==40
    assert result['oracle_exact_recoveries']==40 and result['distinct_host_slides']==8
    assert (tmp_path/'fixture-results/completion.json').exists()
    with pytest.raises(FileExistsError):runner.evaluate_final(path,file_sha256(path),tmp_path,True)
