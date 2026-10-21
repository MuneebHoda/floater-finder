"""Artificial fixtures only; coverage is not clinical detector performance."""
from copy import deepcopy
import csv
import json
from pathlib import Path
import pytest

from floater_finder.artifacts import Slide
from floater_finder.detectors.context_eligibility import assess_context
from floater_finder.experiments import file_sha256
from floater_finder.research import context_safety as safety
from floater_finder.research.contracts import ExperimentRun, canonical
from floater_finder.research.registry import Registry
from floater_finder.research.topology_context import audit_slide
from test_topology_context import source

PROJECT = Path(__file__).resolve().parents[1]
CONFIG = PROJECT/'configs/panda_context_safety_v1.json'


def checkpoint():
    slide, case, features = source()
    row = audit_slide(slide, case, features, [2], [7])
    row.update(host_id='fixture-only', source_identity='a'*64)
    for parts in row['components'].values():
        for p in parts:
            p.update(evaluation_annotation_known_tiles=p['tile_count'], evaluation_native_annotation_positive_tiles=1)
    return row


@pytest.mark.parametrize('candidate,total,score,eligible', [
    (10,10,None,False), (9,10,None,False), (5,10,10.,False),
    (4,10,10.,True), (10,16,20.,False), (8,16,20.,True)])
def test_context_boundaries_and_no_foreignness_or_tissue_action(candidate,total,score,eligible):
    r = assess_context(candidate,total,score)
    assert r['eligible_for_numeric_comparison'] is eligible
    assert r['comparison_score'] == (score if eligible else None)
    assert r['diagnostic_score'] == score
    assert r['review_alert'] is r['foreignness'] is None
    assert r['automatic_tissue_action']=='none' and not r['score_stability_validated']
    assert r['review_status']=='abstain_unvalidated_foreignness_policy'


@pytest.mark.parametrize('args', [(0,10,None),(True,10,None),(2,1,1.),(2,10,None),
    (2,10,float('nan')),(2,10,float('inf')),(2,10,True),(9,10,1.)])
def test_invalid_input_never_becomes_a_silent_negative(args):
    with pytest.raises(ValueError): assess_context(*args)


def test_annotation_truth_does_not_affect_gate_and_unknown_stays_unknown():
    row = checkpoint(); a = safety.audit_checkpoint(row)
    changed = deepcopy(row)
    for parts in changed['components'].values():
        for p in parts: p.update(evaluation_annotation_known_tiles=0,evaluation_native_annotation_positive_tiles=0)
    b = safety.audit_checkpoint(changed)
    for kind in a['components']:
        for x,y in zip(a['components'][kind],b['components'][kind]):
            assert x['eligibility']==y['eligibility']
            assert y['evaluation_annotation_unknown_tiles']==2
    assert safety.summarize([b])['topologies'][0]['strata'][0]['annotation_unknown_components']==2


def test_genuine_small_positive_can_remain_eligible_without_becoming_foreign():
    # Equal-size fixture components with six genuine comparison tiles apiece.
    row = checkpoint(); row['tiles']=12
    for parts in row['components'].values():
        for i,p in enumerate(parts):
            p.update(safety.context_support(6,12),indices=list(range(i*6,(i+1)*6)),
                evaluation_annotation_known_tiles=6, evaluation_native_annotation_positive_tiles=int(i==0))
    row['crosswalk']=safety.crosswalk(row['components']['rgb_cached'],row['components']['sampled'],12)
    result=safety.summarize([safety.audit_checkpoint(row)])
    for topo in result['topologies']:
        eligible=next(s for s in topo['strata'] if s['stratum']=='conservative_eligible')
        assert eligible['components']==2 and eligible['native_annotation_positive_components']==1
    assert result['review_alert_rate'] is result['genuine_tissue_prediction_harm'] is None


def test_no_candidate_mapping_unknown_or_single_component_is_hidden():
    row=checkpoint(); row['components']['rgb_cached']=[];row['mapping_fraction']=0.
    row['crosswalk']=safety.crosswalk([],row['components']['sampled'],row['tiles'])
    for p in row['components']['sampled']:
        p.update(unassigned_rgb_tiles_in_candidate=2,unassigned_rgb_tiles_in_remaining_context=2)
    r=safety.audit_checkpoint(row);s=safety.summarize([r])
    assert s['topologies'][0]['slides_without_eligible_comparison']==1
    assert s['topologies'][1]['strata'][0]['with_unassigned_comparison_tiles']==2


def test_checkpoint_geometry_and_annotation_corruption_fail():
    for change in ('context','annotation','crosswalk'):
        row=checkpoint();p=row['components']['sampled'][0]
        if change=='context':p['remaining_tiles']+=1
        elif change=='annotation':p['evaluation_native_annotation_positive_tiles']=3
        else:row['crosswalk']['mapped_tiles']=0
        with pytest.raises(ValueError):safety.audit_checkpoint(row)


def make_registry(root):
    run=ExperimentRun('fixture-only','software fixture','a'*40,canonical({}),'fixture-manifest',
        'train','fixture-model','fixture-embeddings',canonical({'cpus':2}))
    registry=Registry(root,run);registry.status('planned');registry.status('running')
    registry.checkpoint('slide-fixture',checkpoint());registry.status('verified',validation=True)
    return registry


def test_sealed_read_is_read_only_and_detects_hash_chain_and_tail_damage(tmp_path):
    root=tmp_path/'old';make_registry(root)
    before={str(p):p.stat().st_mtime_ns for p in root.rglob('*')}
    _,artifacts=safety.read_sealed(root)
    assert len(artifacts)==1 and before=={str(p):p.stat().st_mtime_ns for p in root.rglob('*')}
    target=root/'checkpoints/slide-fixture.json';value=target.read_text();target.write_text('{}')
    with pytest.raises(ValueError,match='checkpoint changed'):safety.read_sealed(root)
    target.write_text(value);(root/'events/000003.json').unlink()
    with pytest.raises(ValueError,match='sealed'):safety.read_sealed(root)


def test_preflight_opens_no_arrays_or_predictions_and_requires_frozen_scope(monkeypatch,tmp_path):
    def forbidden(*a,**k):raise AssertionError('No arrays permitted')
    monkeypatch.setattr(Slide,'load',forbidden)
    c=safety.preflight(CONFIG,file_sha256(CONFIG),PROJECT)
    assert c['split']=='train' and c['resources']['gpu']==0
    c['majority_veto']=False;p=tmp_path/'bad.json';p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='training-only'):safety.preflight(p,file_sha256(p),PROJECT)
    with pytest.raises(ValueError,match='protocol changed'):safety.preflight(CONFIG,'bad',PROJECT)
    with pytest.raises(RuntimeError,match='CPU Slurm'):safety.run(*([None]*5),execute=False)


def test_complete_saved_json_runner_with_72_artificial_slides(monkeypatch,tmp_path):
    c=json.loads(CONFIG.read_text());manifest=tmp_path/'fixture-manifest.csv'
    ids=[f'fixture-{i}' for i in range(72)]
    with manifest.open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['image_id','split'])
        writer.writerows((sid,'train') for sid in ids);writer.writerow(['sealed-test-do-not-open','test'])
    c['inputs']['manifest']=dict(path=str(manifest),sha256=file_sha256(manifest))
    old_config=json.loads((PROJECT/c['audit_protocol']).read_text())
    old_run=ExperimentRun('panda_topology_context_v1','fixture-only',c['audit_source_commit'],canonical(old_config),
        file_sha256(manifest),'train','fixture-model','fixture-embeddings',canonical({'cpus':2}))
    old_root=tmp_path/'old';old=Registry(old_root,old_run);old.status('planned');old.status('running')
    for sid in ids:
        r=checkpoint();r['host_id']=sid;old.checkpoint('slide-'+sid,r)
    old.checkpoint('summary',dict(slides=72));old.status('verified',validation=True)
    c['audit_root']=str(old_root);c['output']=str(tmp_path/'new')
    monkeypatch.setattr(safety,'preflight',lambda *a,**k:c)
    monkeypatch.setenv('SLURM_JOB_ID','fixture-only');monkeypatch.delenv('SLURM_JOB_GPUS',raising=False)
    before={str(p):p.read_bytes() for p in old_root.rglob('*') if p.is_file()}
    result=safety.run(CONFIG,'fixture',PROJECT,c['output'],'b'*40,execute=True)
    assert result['slides']==72 and not result['final_test_ready']
    assert before=={str(p):p.read_bytes() for p in old_root.rglob('*') if p.is_file()}
    _,artifacts=safety.read_sealed(c['output']);assert len(artifacts)==73
