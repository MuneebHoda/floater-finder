"""Artificial topology/context fixtures only; no scientific outcome claims."""
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
import pytest

from floater_finder.artifacts import Slide
from floater_finder.experiments import file_sha256
from floater_finder.research import topology_context as audit
from test_fresh_review import bag

PROJECT=Path(__file__).resolve().parents[1]
CONFIG=PROJECT/'configs/panda_topology_context_v1.json'


def source():
    slide,_,_=bag()
    parts=[dict(indices=[0,1],observed_tissue_area_mm2=.03),dict(indices=[2,3],observed_tissue_area_mm2=.04)]
    features=audit.anomaly_features(slide.feats,slide.coords,parts)
    case=dict(components=parts,tile_scores=[0]*4,foreign_mask=[False]*4,mapping_fraction=1.)
    return slide,case,features


def test_crosswalk_records_sampling_splits_merges_and_unknown_assignments():
    r=audit.crosswalk([dict(indices=[0,1,2]),dict(indices=[3,4])],
        [dict(indices=[0]),dict(indices=[1,2,3]),dict(indices=[4,5])],6)
    assert r['unassigned_tiles']==1 and r['mapped_tiles']==5
    assert r['rgb_components_split_across_sampled']==2 and r['sampled_components_merging_rgb']==1
    assert r['complete_physical_piece_boundaries_verified'] is False
    assert r['overlap_tile_counts']==[[1,2,0],[0,1,1]]
    assert audit.crosswalk([], [dict(indices=[0,1])],2)['unassigned_tiles']==2
    with pytest.raises(ValueError,match='cover every'):audit.crosswalk([], [dict(indices=[0])],2)
    with pytest.raises(ValueError,match='Disjoint'):audit.crosswalk([dict(indices=[0]),dict(indices=[0])],[dict(indices=[0,1])],2)


def test_six_outside_tiles_are_required_for_both_nn5_operations():
    assert audit.context_support(10,10)['context_status']=='empty'
    assert audit.context_support(9,10)['context_status']=='singleton'
    assert audit.context_support(5,10)['context_status']=='partial_nn5'
    r=audit.context_support(4,10)
    assert r['context_status']=='full_nn5' and r['candidate_neighbors']==r['background_reference_neighbors']==5
    assert audit.context_support(9,10)['majority_of_sampled_bag']
    with pytest.raises(ValueError):audit.context_support(0,10)


def test_description_keeps_occupied_and_observed_rgb_area_distinct():
    slide,case,features=source()
    r=audit.describe(slide,case['components'],[p['scores']['robust_nn5'] for p in features],'rgb_cached')
    assert r[0]['occupied_area_mm2']==.02 and r[0]['observed_rgb_tissue_area_mm2']==.03
    assert r[0]['remaining_tiles']==2 and r[0]['context_status']=='partial_nn5'
    with pytest.raises(ValueError,match='availability'):audit.describe(slide,case['components'],[None,None],'rgb_cached')


def test_subsampling_is_nested_preserves_sources_and_retains_capacity_exclusions():
    slide,case,features=source();before=slide.feats.copy()
    # Geometry tie-break fixes the first component; every original outside tile is reused.
    scores=[p['scores']['robust_nn5'] for p in features]
    rows=audit.ablations(slide,case['components'],scores,[2,5],[7,8,9])
    assert len(rows)==6 and all(r['status']=='full_context_reused' and r['delta']==0 for r in rows[:3])
    assert [r['duplicate_reference_subset'] for r in rows[:3]]==[False,True,True]
    assert all(r['status']=='insufficient_context' and r['realized_context_tiles'] is None for r in rows[3:])
    assert np.array_equal(before,slide.feats)
    # A larger fixture has true nested subsets and at least one new feature computation.
    from test_fresh_stress import fixtures
    sources,_,_=fixtures();s=sources['fixture-host']['slide']
    p=[dict(indices=[0,1])];f=audit.anomaly_features(s.feats,s.coords,p)[0]['scores']['robust_nn5']
    r=audit.ablations(s,p,[f],[2,5,6],[7])
    assert all(a['status']=='reference_subsampled' for a in r)
    assert set(r[0]['reference_indices'])<=set(r[1]['reference_indices'])<=set(r[2]['reference_indices'])
    assert all(a['component_index']==0 for a in r)


def test_cached_rgb_features_are_reused_and_truth_fields_do_not_change_features(monkeypatch):
    slide,case,features=source();original=audit.anomaly_features;calls=[]
    def tracked(f,xy,parts,*args,**kwargs):calls.append(len(parts));return original(f,xy,parts,*args,**kwargs)
    monkeypatch.setattr(audit,'anomaly_features',tracked)
    r=audit.audit_slide(slide,case,features,[2],[7])
    assert calls==[2]  # Only the new sampled topology; full-size references use cached scores.
    changed=deepcopy(case);changed['annotation_known']=[False]*4;changed['annotated_cancer']=[True]*4;changed['host_truth']='unused'
    assert audit.audit_slide(slide,changed,features,[2],[7])==r
    assert r['crosswalk']['exact_membership_pairs']==2 and not r['classification_predictions_computed']


def test_empty_and_unmapped_candidates_remain_explicit():
    slide,case,features=source();case['components']=[];case['mapping_fraction']=0.
    r=audit.audit_slide(slide,case,[],[2],[7])
    assert r['crosswalk']['unassigned_tiles']==4
    assert r['context_ablations']['rgb_cached'][0]['status']=='no_mapped_candidate'
    case['components']=[dict(indices=list(range(4)),observed_tissue_area_mm2=.1)];case['mapping_fraction']=1.
    r=audit.audit_slide(slide,case,[dict(scores=dict(robust_nn5=None))],[2],[7])
    assert r['components']['rgb_cached'][0]['context_status']=='empty'
    assert r['context_ablations']['rgb_cached'][0]['status']=='insufficient_context'


def test_summary_distinguishes_seed_records_unique_slides_and_duplicate_references():
    slide,case,features=source();r=audit.audit_slide(slide,case,features,[2,5],[7,8,9])
    for parts in r['components'].values():
        for p in parts:p.update(evaluation_native_annotation_positive_tiles=1,evaluation_annotation_known_tiles=p['tile_count'])
    r['host_id']='fixture-only'
    s=audit.summarize([r]);assert s['slides']==1 and s['topologies'][0]['components']==2
    row=next(v for v in s['context_sensitivity'] if v['topology']=='rgb_cached' and v['target_context_tiles']==2)
    assert row['planned']==row['eligible']==3 and row['unique_slides']==1 and row['unique_reference_subsets']==1
    assert row['mean_delta_equal_slide']==0 and row['full_context_reused']==3
    row=next(v for v in s['context_sensitivity'] if v['topology']=='rgb_cached' and v['target_context_tiles']==5)
    assert row['excluded']==3 and row['mean_delta_equal_slide'] is None
    assert not s['classification_predictions_computed'] and not s['thresholds_fitted']


def test_no_predictions_or_arrays_in_preflight_and_scope_guard(monkeypatch,tmp_path):
    def forbidden(*a,**k):raise AssertionError('No slide loading in preflight')
    monkeypatch.setattr(Slide,'load',forbidden)
    c=audit.preflight(CONFIG,file_sha256(CONFIG),PROJECT)
    assert c['split']=='train' and c['slides']==72 and c['maximum_ablation_records']==2160
    c['split']='test';p=tmp_path/'bad.json';p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='training-only'):audit.preflight(p,file_sha256(p),PROJECT)
    with pytest.raises(ValueError,match='protocol changed'):audit.preflight(CONFIG,'bad',PROJECT)
    with pytest.raises(RuntimeError,match='CPU Slurm'):audit.run(*([None]*5),execute=False)


def test_mutated_mapping_provenance_fails():
    slide,case,features=source();case['mapping_fraction']=.5
    with pytest.raises(ValueError,match='alignment'):audit.audit_slide(slide,case,features,[2],[7])
    slide,case,features=source();slide.metadata['tile_step']=[50.,100.]
    with pytest.raises(ValueError,match='nonoverlapping'):audit.audit_slide(slide,case,features,[2],[7])
