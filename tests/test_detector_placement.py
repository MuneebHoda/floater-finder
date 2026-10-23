"""Artificial geometry and vectors verify software, never scientific performance."""
import inspect
import numpy as np
import pytest
from floater_finder.detectors.placement import (memberships,map_components,review_features,
    annotation_arrays,evaluate,paired_groups)
from floater_finder.detectors.calibration import shortlisted


def scorer(x):
    value = float(x[:,0].mean())
    return dict(prediction='cancer' if value > .5 else 'benign',scores=dict(benign=0.,cancer=value))


def test_rgb_gap_contact_and_native_carrier():
    mask=np.zeros((4,8),bool);mask[:,0:2]=True
    rgb=np.full((4,4,3),[150,20,100],np.uint8)
    coords=np.array([[0,0],[4,0]],float)
    parts,q=map_components(mask,coords,[2,4],[1,1],'append_legacy',[1],[rgb])
    assert memberships(parts)==[(0,),(1,)] and q['mapping_fraction']==1
    contact=np.array([[0,0],[2,0]],float)
    parts,_=map_components(mask,contact,[2,4],[1,1],'near_tissue',[1],[rgb])
    assert memberships(parts)==[(0,1)]
    parts,q=map_components(mask,coords,[2,4],[1,1],'replacement')
    assert memberships(parts)==[(0,)] and q['mapping_fraction']==.5
    white=np.full_like(rgb,255)
    parts,q=map_components(mask,coords,[2,4],[1,1],'append_legacy',[1],[white])
    assert memberships(parts)==[(0,)] and q['mapping_fraction']==.5


def test_no_background_filling_or_label_based_membership():
    mask=np.zeros((2,6),bool);mask[:,0:2]=True
    rgb=np.full((4,4,3),255,np.uint8)
    rgb[:,:2]=[150,20,100]
    parts,q=map_components(mask,np.array([[0,0],[4,0]]),[2,2],[1,1],'append_legacy',[1],[rgb])
    assert parts[1]['observed_tissue_area_mm2']==2e-6
    assert memberships([dict(component_id=77,indices=[1,0])])==[(0,1)]
    with pytest.raises(ValueError):map_components(mask,np.array([[0,0]]),[2,2],[1,1],'replacement',rgbs=[rgb])


def test_truth_blind_features_and_coordinate_only_invariance():
    assert set(inspect.signature(review_features).parameters)=={'feats','coords_um','parts','references','scorer','labels'}
    feats=np.array([[1.,0.],[0.,1.],[0.,1.]])
    coords=np.array([[0.,0.],[20.,0.],[30.,0.]])
    parts=[dict(indices=[0]),dict(indices=[1,2])]
    before,a=review_features(feats,coords,parts,[],scorer,('benign','cancer'))
    after,b=review_features(feats,coords+[123,456],parts,[],scorer,('benign','cancer'))
    assert before==after and a==b
    _,far=review_features(feats,coords*np.array([100,1]),parts,[],scorer,('benign','cancer'))
    for x,y in zip(a,far):
        assert x['counterfactual']==y['counterfactual']
        for key in x['scores']:
            if key!='distant_nn5':assert x['scores'][key]==y['scores'][key]
    assert a[0]['scores']['distant_nn5'] is None and far[0]['scores']['distant_nn5'] is not None


def test_empty_exclusion_is_unevaluable_and_ties_abstain():
    _,parts=review_features(np.array([[1.,0.]]),np.array([[0.,0.]]),[dict(indices=[0])],[],scorer,('benign','cancer'))
    assert parts[0]['counterfactual'] is None and parts[0]['influence'] is None
    assert all(v is None for v in parts[0]['scores'].values())
    assert shortlisted([1.,None,1.0001],1.,1.)==[2]
    assert shortlisted([100.],1.,.899)==[]


def row(known,cancer):
    return dict(mask_available=str(known),gleason3_fraction=str(cancer),gleason4_fraction='0',gleason5_fraction='0')


def test_annotation_provenance_after_append_replacement_and_sham():
    host=[row(True,0),row(False,0)];donor=[row(True,1)]
    k,c=annotation_arrays(host,donor,[2],[0],3)
    assert k.tolist()==[True,False,True] and c.tolist()==[False,False,True]
    k,c=annotation_arrays(host,donor,[0],[0],2)
    assert c.tolist()==[True,False]
    k,c=annotation_arrays([row(True,1),row(True,0)],[row(True,1),row(True,0)],[1],[0],2)
    assert c.tolist()==[True,True]


@pytest.mark.parametrize('clean_correct',[True,False])
def test_induced_error_denominator_and_recovery(clean_correct):
    feats=np.array([[0.,1.],[1.,0.],[1.,0.]])
    clean=dict(prediction='benign' if clean_correct else 'cancer')
    before=scorer(feats)
    r=evaluate(feats,[dict(indices=[1,2])],[0],[False,True,True],[True]*3,[False,True,True],scorer,clean,before,'benign',1.)
    assert r['newly_induced_error']==clean_correct and r['recovered_new_error']==clean_correct
    assert r['fragment_hit'] and r['foreign_flagged']==2 and r['host_tiles_flagged']==0
    assert r['genuine_cancer_components']==0


def test_genuine_small_positive_is_not_foreign():
    feats=np.array([[0.,1.],[1.,0.],[1.,0.]])
    before=scorer(feats)
    r=evaluate(feats,[dict(indices=[1,2])],[0],[False]*3,[True]*3,[False,True,True],scorer,before,before,'cancer',1.)
    assert r['foreign_tiles']==0 and r['fragment_hit'] is None
    assert r['genuine_cancer_components_flagged']==1 and r['hypothetical_clean_damage']


def test_paired_eligibility_preserves_abstentions_and_excludes_replacement():
    base=dict(task='s1',condition='cancer',control='annotated_donor',host_id='h',donor_id='d',seed=1,requested_percent=1)
    rows=[dict(base,case_id=str(i),mode=m,mapping_fraction=0 if i==1 else 1) for i,m in enumerate(
        ('append_legacy','near_tissue','within_region_context','replacement'))]
    groups=paired_groups(rows)
    assert len(groups)==1 and groups[0]['complete_triplet'] and groups[0]['cases']['near_tissue']=='1'
    with pytest.raises(ValueError):paired_groups(rows+[rows[0]])


def test_real_runner_requires_slurm(monkeypatch):
    from floater_finder.detectors.placement_run import run
    monkeypatch.delenv('SLURM_JOB_ID',raising=False)
    with pytest.raises(RuntimeError,match='CPU Slurm'):run(*([None]*10))


def test_frozen_input_hashes():
    import json
    from pathlib import Path
    from floater_finder.research.registry import file_hash
    root=Path(__file__).resolve().parents[1]
    config=json.loads((root/'configs/panda_detector_placement_v1.json').read_text())
    assert file_hash(root/config['trials'])==config['trials_sha256']
    assert file_hash(root/config['threshold_report'])==config['threshold_sha256']
    for digest in [config['old_components_sha256'],config['engine_identity'],*config['predictor_files'].values()]:
        assert len(digest)==64


def test_paired_tile_denominators_dose_strata_and_sham_burden():
    from floater_finder.detectors.placement_run import _paired_summary,_case_summary
    feats=np.array([[0.,1.],[1.,0.],[1.,0.]])
    before=scorer(feats); clean=dict(prediction='benign')
    rows=[]
    for dose in (1,10):
        for mode in ('append_legacy','near_tissue','within_region_context'):
            flags=[0] if mode=='append_legacy' else []
            metric=evaluate(feats,[dict(indices=[1,2])],flags,[False,True,True],[True]*3,[False,True,True],scorer,clean,before,'benign',1.)
            rows.append(dict(metric,task='s1',condition='cancer',control='annotated_donor',kind='synthetic',
                host_id='h',donor_id='d',seed=1,mode=mode,requested_percent=dose,case_id=f'{dose}-{mode}'))
    paired=_paired_summary(paired_groups(rows),rows)
    assert len(paired)==4 and {r['requested_percent'] for r in paired}=={1,10}
    assert all(r['append']['metrics']['foreign_tiles']==2 and r['append']['metrics']['foreign_tiles_flagged']==2 for r in paired)
    assert all(r['placed']['metrics']['foreign_tiles_flagged']==0 for r in paired)
    native=evaluate(feats,[dict(indices=[1,2])],[0],[False]*3,[True]*3,[False,True,True],scorer,before,before,'cancer',1.)
    summary=_case_summary([dict(native,host_id='h',donor_id='h',kind='sham')])
    assert summary['alert_rate']==1 and summary['mean_components_per_case']==1
    assert summary['native_originally_correct']==1 and summary['hypothetical_native_damage_rate']==1
