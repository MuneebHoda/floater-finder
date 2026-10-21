"""Software fixtures only: geometry, reference fitting, ties and safety boundaries."""
import json
from types import SimpleNamespace
import numpy as np
import pytest
from floater_finder.detectors.contextual_similarity import anomaly_features, cohort_distance, unit_mean, METHODS
from floater_finder.detectors.calibration import budget_threshold, shortlisted, explain_shortlist, weighted_pr
from floater_finder.detectors.training import fold_assignment, host_interval


def test_relative_context_is_translation_rotation_invariant_and_truth_free():
    feats=np.array([[1.,0.],[1.,0.],[0.,1.]])
    xy=np.array([[0.,0.],[0.,600.],[100.,0.]])
    parts=[dict(indices=[0,1],foreign=True,grade=5),dict(indices=[2],foreign=False,grade=0)]
    a=anomaly_features(feats,xy,parts,distant_um=500)
    b=anomaly_features(feats,xy @ np.array([[0.,-1.],[1.,0.]])+10000,[dict(indices=p['indices']) for p in parts],distant_um=500)
    assert a==b and a[1]['scores']['nn1']==1
    assert a[1]['distant_context_tiles']==1
    assert a[1]['scores']['background_centroid']==1
    assert a[0]['scores']['robust_nn5'] is None  # Only one background tile.
    with pytest.raises(ValueError,match='disjoint'):
        anomaly_features(feats,xy,[dict(indices=[0,1]),dict(indices=[1,2])])


def test_empty_exclusions_and_missing_distant_context_remain_unevaluable():
    feats=np.eye(2);xy=np.zeros((2,2))
    empty=anomaly_features(feats,xy,[dict(indices=[0,1])],reference_centroids=[[1.,0.]])[0]
    assert empty['status']=='not_evaluable_empty_counterfactual'
    assert all(s is None for s in empty['scores'].values())
    assert anomaly_features(feats,xy,[dict(indices=[0]),dict(indices=[1])])[0]['scores']['distant_nn5'] is None
    with pytest.raises(ValueError,match='normalized'):
        anomaly_features(feats*2,xy,[])


def test_equal_slide_cohort_reference_and_budget_ties():
    a=unit_mean(np.repeat([[1.,0.]],1000,axis=0));b=unit_mean([[0.,1.]])
    assert cohort_distance([1.,0.],[a,b])==.5
    assert budget_threshold([[1.,1.],*[[] for _ in range(9)]])==1.
    assert shortlisted([1.,1.],1.,1.)==[]
    assert shortlisted([2.],1.,.89)==[]
    assert budget_threshold([[],[]]) is None
    with pytest.raises(ValueError,match='references'):
        budget_threshold([])


def test_two_stage_explains_without_prediction_dependence_veto_and_pr_preserves_ties():
    parts=[dict(influence=-.1,decision_change=False,counterfactual=None),dict(influence=.01,decision_change=True)]
    explanations=explain_shortlist(parts,[0,1])
    assert [r['component_index'] for r in explanations]==[0,1]
    assert explanations[0]['signed_cancer_influence']==-.1
    pr=weighted_pr([1.,1.],[True,False],[.5,.5])
    assert pr['average_precision']==.5 and len(pr['points'])==1
    assert pr['points'][0]['recall']==1
    folds=fold_assignment(['a','b','c','d'],2,1)
    assert folds==fold_assignment(['d','c','b','a'],2,1)
    assert sorted(folds.values())==[0,0,1,1]
    ci=host_interval([dict(host_id='a',hit=True,n=1),dict(host_id='a',hit=False,n=1)],'hit','n',20,1)
    assert ci==[.5,.5]  # Doses are resampled together, not independent patients.


def test_runner_passes_training_split_before_opening_arrays_and_writes_all_methods(tmp_path,monkeypatch):
    import floater_finder.detectors.training as training
    from floater_finder.panda_review import component_features
    root=__import__('pathlib').Path(__file__).resolve().parents[1]
    config=json.loads((root/'configs/panda_detector_v3_train_v1.json').read_text())
    config.update(expected_clean_slides=4,folds=2,bootstrap_draws=10)
    config_path=tmp_path/'config.json';config_path.write_text(json.dumps(config))
    sources={};cases=[]
    for i in range(4):
        sid=str(i);f=np.array([[1.,0.]]*5+[[0.,1.]])
        slide=SimpleNamespace(feats=f,coords=np.column_stack((np.arange(6)*112,np.zeros(6))),foreign_mask=np.zeros(6,bool),
            metadata={'microns_per_unit':1.,'model':{'checkpoint_sha256':'a'*64}})
        scores=f.copy();sources[sid]=dict(slide=slide,scores=scores)
        base,parts=component_features(f,scores,[dict(indices=[0,1,2,3,4]),dict(indices=[5])])
        cases.append(dict(case_id=sid,host_id=sid,split='train',kind='unmodified',requested_percent=0,
            mapping_fraction=1.,components=parts,tile_scores=scores.tolist(),foreign_mask=[False]*6,
            annotation_known=[True]*6,annotated_cancer=[False]*5+[True],baseline=base,clean_prediction=base['prediction'],host_truth='benign'))
    c=json.loads(json.dumps(cases[0]));c.update(case_id='0-p1',kind='synthetic',requested_percent=1,donor_id='1')
    f=np.concatenate([sources['0']['slide'].feats,[[0.,1.]]]);scores=f.copy()
    c['baseline'],c['components']=component_features(f,scores,[dict(indices=[0,1,2,3,4]),dict(indices=[5]),dict(indices=[6])])
    c.update(tile_scores=scores.tolist(),foreign_mask=[False]*6+[True],annotation_known=[True]*7,annotated_cancer=[False]*5+[True,True]);cases.append(c)
    def load(manifest,directories,encoded,verification,splits):
        assert splits==('train',)
        return sources,{'text_fingerprint':'b'*64}
    def inject(host,donor,indices,percent,seed):
        return SimpleNamespace(feats=np.concatenate([host.feats,donor.feats[indices]]),
            coords=np.concatenate([host.coords,[[900.,0.]]]),foreign_mask=np.array([False]*6+[True]),metadata=host.metadata)
    monkeypatch.setattr(training,'load_sources',load);monkeypatch.setattr(training,'inject_development_s1',inject)
    monkeypatch.setattr(training,'train_cases',lambda *a:cases)
    monkeypatch.setenv('SLURM_JOB_ID','software-fixture')
    for name in ('manifest','directories','verification','cases'):(tmp_path/name).write_text(name)
    stress=tmp_path/'stress';stress.mkdir();(stress/'trials.json').write_text(json.dumps([dict(host_id='0',donor_id='1',donor_indices=[5],requested_percent=1,split='train')]))
    report=training.run(tmp_path/'manifest',tmp_path/'directories',tmp_path/'encoded',tmp_path/'verification',stress,
        tmp_path/'cases',config_path,tmp_path/'out')
    assert set(report['methods'])==set(METHODS)
    assert report['counts']['oracle_checks']==1
    assert report['calibration_predictions_computed'] is False and report['final_test_predictions_computed'] is False
    assert (tmp_path/'out/completion.json').is_file()
    for fold in report['folds']:
        assert not set(fold['fit_ids'])&set(fold['held_ids'])
    with pytest.raises(FileExistsError):
        training.run(tmp_path/'manifest',tmp_path/'directories',tmp_path/'encoded',tmp_path/'verification',stress,
            tmp_path/'cases',config_path,tmp_path/'out')
