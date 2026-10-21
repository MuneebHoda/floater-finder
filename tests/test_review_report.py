"""Artificial saved-prediction fixtures; not scientific or clinical evidence."""
from copy import deepcopy
import csv
import json
from pathlib import Path
import pytest

from floater_finder.artifacts import Slide
from floater_finder.experiments import file_sha256
from floater_finder.review_report import evidence_from_case, build_report, render_html, render_index, saved_prediction
from floater_finder.research import review_export as export
from floater_finder.research.context_safety import audit_checkpoint, read_sealed
from floater_finder.research.contracts import ExperimentRun, canonical
from floater_finder.research.registry import Registry
from test_context_safety import checkpoint

PROJECT=Path(__file__).resolve().parents[1]
CONFIG=PROJECT/'configs/panda_dependence_export_v1.json'


def fixture():
    t=checkpoint();s=audit_checkpoint(t);base=dict(prediction='cancer',scores=dict(benign=.2,cancer=.8))
    counter=dict(prediction='benign',scores=dict(benign=.8,cancer=.2));parts=[]
    for index,p in enumerate(t['components']['rgb_cached']):
        parts.append(dict(component_id=index+1,indices=p['indices'],bbox_um=[index*400,0,index*400+200,100],
            observed_tissue_area_mm2=p['observed_rgb_tissue_area_mm2'],isolation_bbox_lower_bound_mm=.2,
            status='evaluable',counterfactual=counter if index==0 else base,
            decision_change=index==0,cancer_decision_change=index==0,influence=1.2 if index==0 else 0.))
    case=dict(host_id=t['host_id'],case_id='fixture-case',baseline=base,components=parts,host_truth='hidden',
        annotation_known=[True]*4,annotated_cancer=[True]*4,foreign_mask=[False]*4,split='train',kind='unmodified')
    p=dict(source_kind='fixture',source_commit='fixture',scorer=dict(name='artificial fixture scorer'))
    return case,t,s,p


def test_dependence_remains_visible_when_numeric_context_abstains_and_inputs_are_preserved():
    c,t,s,p=fixture();before=deepcopy((c,t,s,p));r=build_report(evidence_from_case(c),t,s,p)
    assert r['components'][0]['decision_change'] is True
    assert r['components'][0]['context']['status']=='abstain'
    assert r['components'][0]['context']['comparison_score'] is None
    assert r['components'][0]['counterfactual']['result']['prediction']=='benign'
    assert r['review_alert'] is r['foreignness'] is None and r['automatic_tissue_action']=='none'
    assert (c,t,s,p)==before
    r['baseline']['scores']['cancer']=0;assert c['baseline']['scores']['cancer']==.8


def test_truth_fields_never_enter_reviewer_json_html_or_component_order():
    c,t,s,p=fixture();a=build_report(evidence_from_case(c),t,s,p)
    c.update(host_truth='changed',foreign_mask=[True]*4,annotated_cancer=[False]*4,annotation_known=[False]*4)
    assert a==build_report(evidence_from_case(c),t,s,p)
    encoded=canonical(a)
    assert all(k not in encoded for k in ('host_truth','annotated_cancer','annotation_known','foreign_mask','evaluation_only'))
    assert [r['component_id'] for r in a['components']]==[1,2]
    page=render_html(a);assert 'Artificial software fixture' in page and 'Decision changes' in page
    assert 'Foreignness is not established' in page and 'Preserve all tissue' in page


@pytest.mark.parametrize('damage', ['membership','gate','baseline','counterfactual','influence','bbox','area','unknown'])
def test_corrupt_cached_alignment_or_prediction_fails(damage):
    c,t,s,p=fixture()
    if damage=='membership':c['components'][0]['indices']=[0]
    elif damage=='gate':s['components']['rgb_cached'][0]['eligibility']['comparison_score']=20
    elif damage=='baseline':c['baseline']['prediction']='benign'
    elif damage=='counterfactual':c['components'][0]['decision_change']=False
    elif damage=='influence':c['components'][0]['influence']=float('nan')
    elif damage=='bbox':c['components'][0]['bbox_um'][2]=-1
    elif damage=='area':s['components']['rgb_cached'][0]['occupied_area_mm2']+=1
    else:s['components']['rgb_cached'][0]['unassigned_rgb_tiles_in_comparison']=1
    with pytest.raises(ValueError):build_report(evidence_from_case(c),t,s,p)


def test_empty_exclusion_has_no_benign_default_and_no_mapped_components_is_unknown():
    c,t,s,p=fixture();part=c['components'][0];g=t['components']['rgb_cached'][0]
    c['components']=[part];t['components']['rgb_cached']=[g]
    part.update(indices=[0,1,2,3],counterfactual=None,decision_change=None,cancer_decision_change=None,
        influence=None,status='not_evaluable_empty_counterfactual')
    g.update(export_fixture_support(4,4),indices=[0,1,2,3],score=None)
    s['components']['rgb_cached']=[dict(s['components']['rgb_cached'][0],eligibility=export_fixture_gate(4,4,None))]
    r=build_report(evidence_from_case(c),t,s,p)
    assert r['components'][0]['counterfactual']['result'] is None and r['components'][0]['decision_change'] is None
    c['components']=[];t['components']['rgb_cached']=[];s['components']['rgb_cached']=[]
    assert 'not a negative finding' in render_html(build_report(evidence_from_case(c),t,s,p))


def export_fixture_support(tiles,total):
    from floater_finder.research.topology_context import context_support
    return context_support(tiles,total)


def export_fixture_gate(tiles,total,score):
    from floater_finder.detectors.context_eligibility import assess_context
    return assess_context(tiles,total,score)


def test_html_escapes_source_text_has_no_active_controls_and_safe_index_links():
    c,t,s,p=fixture();p['scorer']['name']='<script>alert(1)</script>'
    r=build_report(evidence_from_case(c),t,s,p);page=render_html(r)
    assert '<script' not in page and '&lt;script&gt;' in page
    assert '<button' not in page and '<form' not in page and 'src=' not in page
    assert 'reports/fixture-only.html' in render_index([r])
    r['host_id']='../../elsewhere'
    with pytest.raises(ValueError,match='Safe report'):render_index([r])
    with pytest.raises(ValueError):saved_prediction(dict(prediction='cancer',scores=dict(benign=1.,cancer=1.)))


def test_preflight_and_cpu_gate_read_no_arrays(monkeypatch,tmp_path):
    monkeypatch.setattr(Slide,'load',lambda *a,**k:pytest.fail('No arrays in export'))
    c=export.preflight(CONFIG,file_sha256(CONFIG),PROJECT)
    assert not c['new_predictions'] and c['slides']==72
    c['split']='test';p=tmp_path/'bad.json';p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='training-only'):export.preflight(p,file_sha256(p),PROJECT)
    with pytest.raises(RuntimeError,match='CPU Slurm'):export.run(*([None]*5),execute=False)


def test_complete_72_slide_fixture_export_seals_rendered_hashes_and_native_controls(monkeypatch,tmp_path):
    c=json.loads(CONFIG.read_text());manifest=tmp_path/'manifest.csv';ids=[f'{n:032x}' for n in range(72)]
    with manifest.open('w',newline='') as handle:
        w=csv.writer(handle);w.writerow(['image_id','split']);w.writerows((sid,'train') for sid in ids)
        w.writerow(['do-not-open-test','test'])
    case,t,s,_=fixture();cases=[];before={}
    for name,exp in [('topology',c['topology_experiment_id']),('safety',c['safety_experiment_id'])]:
        root=tmp_path/name;c[name+'_root']=str(root)
        run=ExperimentRun(exp,'fixture only',c[name+'_source_commit'],canonical({}),file_sha256(manifest),
            'train','fixture-checkpoint','fixture-text',canonical({'cpus':2}))
        registry=Registry(root,run);registry.status('planned');registry.status('running')
        for sid in ids:
            row=deepcopy(t if name=='topology' else s);row['host_id']=sid;registry.checkpoint('slide-'+sid,row)
        registry.checkpoint('summary',dict(slides=72));registry.status('verified',validation=True)
        before[name]={str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    for sid in ids:
        row=deepcopy(case);row['host_id']=sid;row['case_id']=sid;cases.append(row)
    cases_file=tmp_path/'cases.json';cases_file.write_text(json.dumps(cases))
    c['inputs']={name:dict(path=str(path),sha256=file_sha256(path)) for name,path in [('manifest',manifest),('cases',cases_file)]}
    c['output']=str(tmp_path/'new');c['components']=144
    monkeypatch.setattr(export,'preflight',lambda *a,**k:c)
    monkeypatch.setenv('SLURM_JOB_ID','fixture');monkeypatch.delenv('SLURM_JOB_GPUS',raising=False)
    result=export.run(CONFIG,'fixture',PROJECT,c['output'],'b'*40,execute=True)
    assert result['slides']==72 and result['decision_changing_abstained']==72 and result['annotation_positive_decisive_components']==72
    assert result['review_alert_rate'] is result['foreign_fragment_recall'] is None
    assert len(result['rendered_file_sha256'])==145
    for name,digest in result['rendered_file_sha256'].items():assert file_sha256(Path(c['output'])/name)==digest
    assert read_sealed(c['output'])[0]['split']=='train'
    for name in before:assert before[name]=={str(p):p.read_bytes() for p in Path(c[name+'_root']).rglob('*') if p.is_file()}
