"""Artificial saved-score/colored-PNG fixtures; never scientific measurements."""
from copy import deepcopy
import csv
from html.parser import HTMLParser
import json
from pathlib import Path
import pytest
from PIL import Image

from floater_finder.artifacts import Slide
from floater_finder.experiments import file_sha256
from floater_finder.research import control_audit as audit
from floater_finder.research.context_safety import read_sealed
from floater_finder.research.contracts import ExperimentRun,canonical
from floater_finder.research.registry import Registry

PROJECT=Path(__file__).resolve().parents[1]
CONFIG=PROJECT/'configs/panda_paired_control_audit_v1.json'


def prediction(cancer):
    return dict(prediction='cancer' if cancer else 'benign',scores=dict(benign=.2 if cancer else .8,cancer=.8 if cancer else .2))


def component(indices,baseline,counter):
    return dict(component_id='c'+str(indices[0]),indices=indices,bbox_um=[0,0,100,100],observed_tissue_area_mm2=len(indices)*.01,
        counterfactual=counter,status='evaluable' if counter else 'not_evaluable_empty_counterfactual',
        decision_change=baseline['prediction']!=counter['prediction'] if counter else None,
        influence=baseline['scores']['cancer']-baseline['scores']['benign']-(counter['scores']['cancer']-counter['scores']['benign']) if counter else None)


def case(sid,n,cancer=False):
    p=prediction(cancer)
    return dict(case_id=sid,host_id=sid,split='train',kind='unmodified',baseline=p,
        tile_scores=[[p['scores']['benign'],p['scores']['cancer']] for _ in range(n)],
        annotation_known=[True]*n,annotated_cancer=[cancer]*n,foreign_mask=[False]*n,
        mapping_fraction=1,components=[component(list(range(n)),p,None)])


def source(root,sid,n,cancer=False):
    root.mkdir(parents=True);rows=[];hashes={}
    for i in range(n):
        path=root/f'tile-{i}.png';Image.new('RGB',(16,16),(i*11%255,30,60)).save(path)
        rows.append(dict(tile_id=f'tile-{i}',path=path.name,image_id=sid,x=str(i*100.),y='200.0' if i else '1000.0',
            grid_x=i,grid_y=0,area_mm2=.01,gleason3_fraction=0.,gleason4_fraction=.5 if cancer else 0.,gleason5_fraction=0.))
        hashes[f'tile-{i}']=file_sha256(path)
    metadata=dict(slide_id=sid,source_kind='real',cohort_split='train',coordinate_units='microns',coordinate_reference='tile_top_left',
        microns_per_unit=1,tile_size=[100.,100.],tile_step=[100.,100.],export_pixels=16,project='PANDA',data_provider='radboud',
        isup_grade=4 if cancer else 0,extraction=dict(sampling_mode='representative',selection_uses_mask=False))
    # The simulated real-input marker exercises the production guard; these images are artificial.
    (root/'metadata.json').write_text(json.dumps(metadata))
    with (root/'tiles.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    return dict(rows=rows,metadata=metadata,hashes=hashes,directory=root)


def controls(h,d):
    hid=h['metadata']['slide_id'];did=d['metadata']['slide_id'];n=len(h['rows']);host=case(hid,n);donor=case(did,len(d['rows']),True)
    donor['components']=[component([0],donor['baseline'],prediction(False)),component(list(range(1,len(d['rows']))),donor['baseline'],prediction(True))]
    mixed=deepcopy(host);mixed.update(case_id=hid+'-5',kind='synthetic',donor_id=did,requested_percent=5,baseline=prediction(True))
    for name in ('tile_scores','annotation_known','annotated_cancer'):mixed[name]=host[name]+[donor[name][0]]
    mixed['foreign_mask']=[False]*n+[True]
    mixed['components']=[component(list(range(n)),mixed['baseline'],prediction(True)),component([n],mixed['baseline'],prediction(False))]
    trial=dict(host_id=hid,donor_id=did,split='train',requested_percent=5,realized_percent=100/n,host_tiles=n,foreign_tiles=1,
        donor_indices=[0],donor_tile_ids=['tile-0'],foreign_footprint_area_mm2=.01,annotated_cancer_area_mm2=.005,
        baseline=dict(top5pct=deepcopy(host['baseline'])),contaminated=dict(top5pct=deepcopy(mixed['baseline'])),
        oracle=dict(top5pct=deepcopy(host['baseline'])),oracle_exact_recovery=True,
        synthetic_injection=dict(kind='synthetic_PANDA_S1_embedding_contamination',donor_indices=[0],donor_tile_ids=['tile-0'],
            donor_slide_id=did,foreign_count=1,original_host_count=n,patient_independence_verified=False,
            translation_um=[max(float(r['x']) for r in h['rows'])+300, -800.]))
    features={c['case_id']:[dict(scores=dict(robust_nn5=2. if len(c['tile_scores'])-len(p['indices'])>=2 else None)) for p in c['components']] for c in (host,donor,mixed)}
    return mixed,host,donor,trial,features,h,d


@pytest.fixture
def pair_inputs(tmp_path):
    return controls(source(tmp_path/'host','a'*32,20),source(tmp_path/'donor','b'*32,4,True))


def test_same_native_tile_has_different_context_without_foreignness_inference(pair_inputs):
    p=audit.assemble_pair(*pair_inputs)
    assert p['gallery_indices']['native_fragment']==p['gallery_indices']['synthetic_fragment']==[0]
    assert p['native_donor_overlap_components'][0]['decision_change'] is True
    assert p['synthetic_components'][1]['decision_change'] is True
    assert p['native_donor_overlap_components'][0]['evaluation_native_cancer_tiles']==1
    assert p['synthetic_components'][1]['evaluation_appended_donor_tiles']==1
    assert p['newly_induced_host_label_error'] and p['saved_oracle_verified'] and not p['new_oracle_executed']
    assert p['saved_translation_um']==[2200.,-800.]  # Numeric minimum of CSV strings, never lexicographic.
    assert p['review_alert'] is p['foreignness'] is None and p['automatic_tissue_action']=='none'


@pytest.mark.parametrize('damage',['oracle','score_tail','donor_ids','annotation','fraction','area','translation','mapping','counterfactual','split','patient_claim'])
def test_wrong_saved_provenance_stops_instead_of_repairing_it(pair_inputs,damage):
    mixed,host,donor,t,f,h,d=pair_inputs
    if damage=='oracle':t['oracle_exact_recovery']=False
    elif damage=='score_tail':mixed['tile_scores'][-1]=[99,0]
    elif damage=='donor_ids':t['donor_tile_ids']=['other']
    elif damage=='annotation':donor['annotation_known'][0]=False
    elif damage=='fraction':d['rows'][0]['gleason4_fraction']=.09
    elif damage=='area':t['annotated_cancer_area_mm2']=1
    elif damage=='translation':t['synthetic_injection']['translation_um'][0]+=1
    elif damage=='mapping':mixed['mapping_fraction']=.8
    elif damage=='counterfactual':mixed['components'][1]['decision_change']=False
    elif damage=='patient_claim':t['synthetic_injection']['patient_independence_verified']=True
    else:host['split']='test'
    with pytest.raises((ValueError,RuntimeError)):audit.assemble_pair(*pair_inputs)


def test_unmapped_donor_is_visible_and_initial_errors_are_not_new_errors(pair_inputs):
    mixed,host,donor,t,f,h,d=pair_inputs
    mixed['components']=mixed['components'][:1];mixed['mapping_fraction']=20/21;f[mixed['case_id']]=f[mixed['case_id']][:1]
    host['baseline']=prediction(True);t['baseline']['top5pct']=t['oracle']['top5pct']=deepcopy(host['baseline'])
    p=audit.assemble_pair(*pair_inputs);s=audit.summarize([p,p])
    assert p['evaluation_unmapped_donor_tiles']==1
    assert s['originally_correct_hosts']==0 and s['initially_incorrect_hosts']==2 and s['newly_induced_host_label_errors']==0
    assert s['unique_overlapping_native_components']==1 and s['unique_decisive_overlapping_native_components']==1
    assert s['detector_recall'] is s['review_alert_rate'] is None


def test_original_empty_native_exclusion_stays_unevaluable(pair_inputs):
    mixed,host,donor,t,f,h,d=pair_inputs;donor['components']=[component(list(range(4)),donor['baseline'],None)]
    f[donor['case_id']]=[dict(scores=dict(robust_nn5=None))]
    p=audit.assemble_pair(*pair_inputs);r=p['native_donor_overlap_components'][0]
    assert r['decision_change'] is None and r['cached_counterfactual'] is None
    assert r['context']['status']!='eligible'


def test_local_png_identity_dedup_and_rendered_pair_are_bound(pair_inputs,tmp_path):
    p=audit.assemble_pair(*pair_inputs);out=tmp_path/'out';(out/'tiles').mkdir(parents=True);assets={}
    p['galleries']={role:[audit.copy_tile(pair_inputs[5] if role=='host_context' else pair_inputs[6],i,out,assets,1000000) for i in ix] for role,ix in p['gallery_indices'].items()}
    assert len(assets)==8 and p['galleries']['native_fragment']==p['galleries']['synthetic_fragment']
    assert all((out/n).read_bytes()==Path(a['source_path']).read_bytes() for n,a in assets.items())
    class Images(HTMLParser):
        def __init__(self):super().__init__();self.paths=[]
        def handle_starttag(self,tag,attrs):
            if tag=='img':self.paths.extend(v for k,v in attrs if k=='src')
    page=audit.render_pair(p);parser=Images();parser.feed(page)
    assert len(parser.paths)==9 and all(path[3:] in assets for path in parser.paths)
    assert 'Known provenance' in page and 'not an observed contaminated WSI' in page
    p['galleries']['native_fragment'][0]['asset_path']='https://example.com/track.png'
    with pytest.raises(ValueError,match='Safe local'):audit.render_pair(p)


@pytest.mark.parametrize('damage',['hash','path','symlink','shape','budget','slide_id'])
def test_invalid_png_source_stops_before_copying(pair_inputs,tmp_path,damage):
    s=pair_inputs[5];out=tmp_path/'out';(out/'tiles').mkdir(parents=True);budget=1000000
    if damage=='hash':s['hashes']['tile-0']='0'*64
    elif damage=='path':s['rows'][0]['path']='../escape.png'
    elif damage=='symlink':
        escaped=tmp_path/'escape.png';escaped.write_bytes((s['directory']/'tile-0.png').read_bytes());(s['directory']/'tile-0.png').unlink();(s['directory']/'tile-0.png').symlink_to(escaped)
    elif damage=='shape':s['metadata']['export_pixels']=32
    elif damage=='slide_id':s['metadata']['slide_id']='../escape'
    else:budget=0
    with pytest.raises(ValueError):audit.copy_tile(s,0,out,{},budget)
    assert not list((out/'tiles').iterdir())


def test_preflight_and_execution_gate_never_read_slide_arrays(monkeypatch,tmp_path):
    monkeypatch.setattr(Slide,'load',lambda *a,**k:pytest.fail('No saved arrays allowed'))
    c=audit.preflight(CONFIG,file_sha256(CONFIG),PROJECT);assert c['pairs']==24 and c['resources']['gpu']==0
    c['split']='test';p=tmp_path/'bad.json';p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='training'):audit.preflight(p,file_sha256(p),PROJECT)
    with pytest.raises(RuntimeError,match='CPU Slurm'):audit.run(*([None]*5),execute=False)


def test_all_24_artificial_pairs_seal_outputs_and_preserve_native_inputs(tmp_path,monkeypatch):
    c=json.loads(CONFIG.read_text());ids=[f'{i:032x}' for i in range(72)];native=tmp_path/'native';encoded=tmp_path/'encoded';manifest=tmp_path/'manifest.csv'
    with manifest.open('w',newline='') as f:w=csv.writer(f);w.writerow(['image_id','split']);w.writerows((sid,'train') for sid in ids);w.writerow(['sealed-test','test'])
    old=Registry(native,ExperimentRun('panda_preview_export_v1','Artificial fixture',c['native_source_commit'],canonical({}),file_sha256(manifest),
        'train','fixture-checkpoint','fixture-text',canonical({'cpus':2})))
    old.status('planned');old.status('running');sources={};clean={};verified=[]
    for i,sid in enumerate(ids):
        s=source(tmp_path/'sources'/sid,sid,20 if i<24 else 4,i>=24);sources[sid]=s;clean[sid]=case(sid,len(s['rows']),i>=24)
        completion=dict(cohort_split='train',input_identity=dict(manifest_sha256=file_sha256(s['directory']/'tiles.csv'),metadata_sha256=file_sha256(s['directory']/'metadata.json'),png_sha256=s['hashes'],checkpoint_sha256='fixture-checkpoint'))
        dest=encoded/sid;dest.mkdir(parents=True);(dest/'completion.json').write_text(json.dumps(completion));verified.append(dict(image_id=sid,completion_sha256=file_sha256(dest/'completion.json')))
        old.checkpoint('slide-'+sid,dict(report=dict(baseline=clean[sid]['baseline'],tile_count=len(s['rows']),provenance=dict(checkpoint_sha256='fixture-checkpoint'))))
    old.checkpoint('summary',dict(artificial=True));old.status('verified',validation=True)
    old_before={str(p):p.read_bytes() for p in native.rglob('*') if p.is_file()}
    trials=[];mixed=[];features={}
    for i in range(24):
        m,h,d,t,fs,_,_=controls(sources[ids[i]],sources[ids[24+i%16]])
        clean[d['host_id']]=d;mixed.append(m);trials.append(t);features.update(fs)
    paths=dict(manifest=manifest)
    payloads=dict(cases=list(clean.values())+mixed,trials=trials,features=dict(source_kind='real',config_sha256=c['old_feature_config_sha256'],features=features),
        directories=[str(s['directory']) for s in sources.values()],verification=dict(manifest_sha256=file_sha256(manifest),records=verified))
    for name,payload in payloads.items():paths[name]=tmp_path/(name+'.json');paths[name].write_text(json.dumps(payload))
    paths['feature_completion']=tmp_path/'feature_completion.json';paths['feature_completion'].write_text(json.dumps(dict(status='verified',artifacts={'feature_checkpoint.json':file_sha256(paths['features'])})))
    c.update(native_root=str(native),encoded_root=str(encoded),output=str(tmp_path/'result'),inputs={k:dict(path=str(p),sha256=file_sha256(p)) for k,p in paths.items()})
    monkeypatch.setattr(audit,'preflight',lambda *a,**k:c);monkeypatch.setenv('SLURM_JOB_ID','fixture');monkeypatch.delenv('SLURM_JOB_GPUS',raising=False)
    monkeypatch.setattr(Slide,'load',lambda *a,**k:pytest.fail('No arrays/prediction calls allowed'))
    result=audit.run(CONFIG,'fixture',PROJECT,c['output'],'b'*40,execute=True)
    assert result['pairs']==24 and result['unique_host_slides']==24 and result['unique_donor_slides']==16
    assert result['newly_induced_host_label_errors']==24 and result['saved_oracle_receipts_verified']==24 and result['new_oracle_executions']==0
    assert result['unique_decisive_overlapping_native_components']==16 and result['decisive_components_with_appended_donor']==24
    assert result['image_references']==216 and result['unique_png_assets']==160 and len(read_sealed(c['output'])[1])==25
    assert all(file_sha256(Path(c['output'])/name)==digest for name,digest in result['rendered_file_sha256'].items())
    assert old_before=={str(p):p.read_bytes() for p in native.rglob('*') if p.is_file()}
