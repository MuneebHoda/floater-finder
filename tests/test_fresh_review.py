"""Artificial fixture safety/transfer checks; no real arrays or scientific results."""
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
import pytest

from floater_finder.artifacts import Slide
from floater_finder.experiments import file_sha256
from floater_finder.predictors.linear_probe import FrozenPredictor
from floater_finder.research.fresh_stress import counterfactual
from floater_finder.detectors import fresh_review as review
from test_fresh_stress import fixtures,FixtureScorer

PROJECT=Path(__file__).resolve().parents[1]
CONFIG=PROJECT/'configs/panda_fresh_review_transfer_v1.json'


def bag():
    sources,models,_=fixtures();slide=sources['fixture-donor']['slide'].subset([0,1,2,3])
    slide.coords[:]=[[0,0],[100,0],[500,0],[600,0]]
    slide.feats[:]=0;slide.feats[:2,0]=1;slide.feats[2:,1]=1
    reports={role:counterfactual(slide,model,np.array([0.,0.,.01,.01]),
        dict(case_id='fixture-clean',host_id='fixture-donor',kind='unmodified',mode='clean',role=role)) for role,model in models.items()}
    return slide,models,reports


def folds():
    ids=[f'fictional-train-{n}' for n in range(72)]
    return dict(primary_prototype='robust_nn5',folds=[dict(method='robust_nn5',fold=n,
        held_ids=ids[n::5],fit_ids=[sid for sid in ids if sid not in ids[n::5]],threshold=float(n+1)) for n in range(5)])


def test_fold_unanimity_is_conservative_and_requires_training_separation():
    v=folds();assert review.transfer_threshold(v,['fixture-study'])==5.
    with pytest.raises(ValueError,match='separation'):review.transfer_threshold(v,['fictional-train-0'])
    v['folds'][0]['fit_ids'].append(v['folds'][0]['held_ids'][0])
    with pytest.raises(ValueError,match='provenance'):review.transfer_threshold(v,[])
    v=folds();v['folds'][0]['threshold']=None
    assert review.transfer_threshold(v,[]) is None


def test_preflight_is_metadata_only_and_keeps_new_scope_bounded(monkeypatch,tmp_path):
    def forbidden(*a,**k):raise AssertionError('no arrays or scoring in preflight')
    monkeypatch.setattr(Slide,'load',forbidden);monkeypatch.setattr(FrozenPredictor,'__call__',forbidden)
    c,*_=review.preflight(CONFIG,file_sha256(CONFIG),PROJECT)
    assert c['maximum_bags']==140 and c['maximum_filtered_predictions']==9800 and c['approval_required']
    assert c['visual_threshold']==9.32818765238456
    with pytest.raises(ValueError,match='protocol changed'):review.preflight(CONFIG,'wrong',PROJECT)
    c['random_draws']=33;p=tmp_path/'unsafe.json';p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='bounded'):review.preflight(p,file_sha256(p),PROJECT)


def test_membership_geometry_validation_and_truth_blind_anomaly_features():
    slide,_,reports=bag();r=reports['primary'];parts=review.review_parts(slide,r)
    changed=deepcopy(r)
    for p in changed['pieces']:
        p['evaluation_only_foreign_tiles']=999;p['evaluation_only_genuine_cancer_area_mm2']=999
    assert review.review_parts(slide,changed)==parts
    changed=deepcopy(r);changed['pieces'][0]['area_mm2']*=2
    with pytest.raises(ValueError,match='physical'):review.review_parts(slide,changed)
    changed=deepcopy(r);changed['pieces'][0]['tile_ids'][0]='wrong-source'
    with pytest.raises(ValueError,match='identity'):review.review_parts(slide,changed)
    changed=deepcopy(r);changed['pieces'].append(deepcopy(changed['pieces'][0]));changed['piece_count']+=1
    with pytest.raises(ValueError,match='partition'):review.review_parts(slide,changed)


def test_strict_ties_visual_dependence_and_random_count_are_distinct():
    parts=[dict(visual_score=3.,decision_change=True),dict(visual_score=4.,decision_change=False),
        dict(visual_score=None,decision_change=True),dict(visual_score=100.,decision_change=None)]
    r=review.flags(parts,3.,7)
    assert r['visual']==[1] and r['dependence']==[0,2] and r['combined']==[] and r['random_matched']==[]
    r=review.flags(parts,2.,7)
    assert r['combined']==[0] and len(r['random_matched'])==1 and r==review.flags(parts,2.,7)
    assert all(i!=3 for i in r['random_matched'])


def test_genuine_cancer_can_be_flagged_and_hypothetical_harm_is_not_hidden():
    slide,models,reports=bag();parts=review.review_parts(slide,reports['primary']);before=slide.feats.copy()
    selected=review.flags(parts,0.,7)['combined']
    assert selected==[1]
    def forbidden(*a):raise AssertionError('reuse saved one-piece counterfactual')
    baseline=reports['primary']['baseline']
    result=review.assess(slide,parts,selected,np.array([0.,0.,.01,.01]),forbidden,baseline,baseline,'cancer')
    assert result['genuine_cancer_components_flagged']==1 and result['hypothetical_clean_damage']
    assert result['foreign_tiles']==0 and result['fragment_hit'] is None
    assert result['automatic_tissue_action']=='none' and np.array_equal(slide.feats,before)
    empty=review.assess(slide,parts,[0,1],np.array([0.,0.,.01,.01]),forbidden,baseline,baseline,'cancer')
    assert empty['empty_after_hypothetical_filter'] and empty['hypothetical_clean_damage']


def test_empty_exclusions_abstain_instead_of_becoming_benign():
    slide,models,_=bag();slide.coords[:]=[[0,0],[100,0],[200,0],[300,0]]
    report=counterfactual(slide,models['primary'],np.zeros(4),dict(mode='clean'))
    parts=review.review_parts(slide,report)
    assert len(parts)==1 and parts[0]['visual_score'] is None
    assert all(not f for f in review.flags(parts,0.,7).values())
    result=review.assess(slide,parts,[],np.zeros(4),models['primary'],report['baseline'],report['baseline'],'cancer')
    assert result['topology_abstained'] and result['filtered_prediction']=='cancer' and not result['empty_after_hypothetical_filter']


def test_known_foreign_recovery_excludes_initial_errors_from_new_error_denominator():
    slide,models,reports=bag();slide.foreign_mask[2:]=True
    parts=review.review_parts(slide,reports['primary']);baseline=reports['primary']['baseline']
    clean=models['primary'](slide.feats[:2]);areas=np.array([0.,0.,.01,.01])
    result=review.assess(slide,parts,[1],areas,models['primary'],clean,baseline,'benign')
    assert result['fragment_hit'] and result['complete_fragment'] and result['foreign_flagged']==2
    assert result['newly_induced_error'] and result['recovered_new_error']
    assert result['genuine_cancer_components_flagged']==0 and not result['hypothetical_clean_damage']
    wrong=review.assess(slide,parts,[1],areas,models['primary'],baseline,baseline,'benign')
    assert wrong['initially_incorrect'] and not wrong['newly_induced_error'] and not wrong['recovered_new_error']


def test_fixture_bag_covers_both_models_all_policies_and_keeps_random_draw_units():
    slide,models,reports=bag();c=json.loads(CONFIG.read_text());c['visual_threshold']=0.
    clean={role:r['baseline'] for role,r in reports.items()}
    result=review.measure_bag(slide,reports,models,np.array([0.,0.,.01,.01]),clean,'cancer',c,'fixture-clean')
    assert len(result['metrics'])==70 and set(result['explanations'])=={'primary','historical'}
    assert all(p['foreignness']=='not_established' for v in result['explanations'].values() for p in v)
    groups=review.summarize(result['metrics'])
    random=next(r for r in groups if r['role']=='primary' and r['policy']=='random_matched')
    assert random['observations']==32 and random['unique_bags']==1 and random['unique_host_slides']==1
    assert random['random_draws_are_not_independent_slides'] and random['alert_rate']==1
    bad=deepcopy(reports);bad['historical']['pieces'][0]['tile_indices'].reverse()
    with pytest.raises(ValueError,match='topology'):review.measure_bag(slide,bad,models,np.zeros(4),clean,'cancer',c,'fixture-clean')


def test_real_execution_cannot_run_without_explicit_cpu_slurm(monkeypatch):
    monkeypatch.delenv('SLURM_JOB_ID',raising=False)
    with pytest.raises(RuntimeError,match='CPU Slurm'):review.run(*([None]*5),execute=True)
