from copy import deepcopy
import numpy as np
from floater_finder.panda_review import component_features,flagged_components,evaluate_flags,matched_draws,summarize,wilson


def case():
    f=np.zeros((6,2));f[:5,0]=1;f[5,1]=1
    scores=np.array([[.8,.1]]*5+[[.1,1.]])
    components=[dict(indices=list(range(5)),observed_tissue_area_mm2=.5,isolation_bbox_lower_bound_mm=.2),
                dict(indices=[5],observed_tissue_area_mm2=.01,isolation_bbox_lower_bound_mm=.2)]
    baseline,parts=component_features(f,scores,components)
    return dict(case_id='fixture',components=parts,mapping_fraction=1.,tile_scores=scores.tolist(),baseline=baseline,
        foreign_mask=[False]*5+[True],annotation_known=[True]*6,annotated_cancer=[False]*5+[True],
        clean_prediction='benign',host_truth='benign')


def test_review_uses_visual_influence_geometry_without_using_annotation_or_foreign_truth():
    c=case();rule=dict(kind='combined',visual_threshold=.5,influence='flip',max_area_mm2=.05,min_isolation_mm=.1)
    assert flagged_components(c,rule)==[1]
    assert flagged_components(c,dict(kind='decision'))==[1]
    original=deepcopy(c);c['foreign_mask']=[False]*6
    assert flagged_components(c,rule)==flagged_components(original,rule)
    evaluated=evaluate_flags(c,[1])
    assert evaluated['genuine_cancer_components_flagged']==1  # Genuine cancer can satisfy the same signals.
    assert not evaluated['newly_induced_error']
    assert evaluate_flags(original,[1])['recovered_new_error']


def test_new_errors_require_original_correctness_and_empty_filtering_is_unevaluable():
    c=case();c['clean_prediction']='cancer'
    r=evaluate_flags(c,[1]);assert r['initially_incorrect'] and not r['newly_induced_error'] and not r['recovered_new_error']
    c['foreign_mask']=[False]*6;c['clean_prediction']='benign'
    r=evaluate_flags(c,[0,1]);assert r['empty_after_hypothetical_filter'] and r['filtered_prediction'] is None
    assert r['hypothetical_clean_damage']
    f=np.eye(2);base,parts=component_features(f,[[1.,0.],[0.,1.]],
        [dict(indices=[0,1],observed_tissue_area_mm2=.02,isolation_bbox_lower_bound_mm=None)])
    assert parts[0]['counterfactual'] is None and parts[0]['decision_change'] is None
    c['components']=parts
    assert flagged_components(c,dict(kind='decision'))==[]


def test_matched_random_keeps_burden_and_exposes_single_eligible_size_match():
    c=case();draws=matched_draws(c,[1],20)
    assert len(draws)==20 and all(d==[1] for d in draws)  # Size matching can make random control deterministic.
    c['mapping_fraction']=.8
    assert flagged_components(c,dict(kind='visual',visual_threshold=0))==[]
    assert wilson(0,0) is None and wilson(0,24)[1]>.1
