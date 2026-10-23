from copy import deepcopy
import json
from pathlib import Path
import numpy as np
import pytest
from floater_finder.panda_review import component_features
from floater_finder.panda_review_v2 import (
    observed_signals, fit_reference, rank_scores, ranked_flags, investigate, failure_decomposition,
)


def fixture_case(sid='a', split='train', synthetic=False):
    features = np.array([[1., 0.]] * 5 + [[0., 1.]])
    scores = np.array([[.8, .1]] * 5 + [[.1, 1.]])
    parts = [dict(indices=list(range(5)), observed_tissue_area_mm2=.5, isolation_bbox_lower_bound_mm=.2, bbox_um=[0, 0, 100, 500]),
             dict(indices=[5], observed_tissue_area_mm2=.01, isolation_bbox_lower_bound_mm=.2, bbox_um=[200, 0, 300, 100])]
    base, components = component_features(features, scores, parts)
    if not synthetic:
        components[0]['visual'] = .1
        components[1]['visual'] = .2
    return dict(case_id=sid + ('-p1' if synthetic else ''), host_id=sid, split=split,
        components=components, mapping_fraction=1., tile_scores=scores.tolist(), baseline=base,
        foreign_mask=[False] * 5 + [synthetic], annotation_known=[True] * 6,
        annotated_cancer=[False] * 5 + [True], clean_prediction='cancer', host_truth='cancer',
        kind='synthetic' if synthetic else 'unmodified', requested_percent=1 if synthetic else 0,
        **({'donor_id': 'donor'} if synthetic else {}))


def config():
    path = Path(__file__).resolve().parents[1] / 'configs/panda_review_v2_development.json'
    result = json.loads(path.read_text()); result['bootstrap_repetitions'] = 20; result['matched_random_draws'] = 2
    return result


def cases():
    return [fixture_case(split + str(i), split, synthetic) for split in ('train', 'calibration')
            for i in range(3) for synthetic in (False, True)]


def test_detector_is_blind_to_annotation_injection_ids_and_absolute_placement():
    c = cases(); reference = fit_reference(c); example = c[-1]
    weights = config()['strategies']['combined_rank']
    before = rank_scores(example, weights, reference)
    altered = deepcopy(example)
    altered.update(foreign_mask=[False] * 6, annotation_known=[False] * 6, annotated_cancer=[False] * 6,
                   host_truth='benign', donor_id='anything', host_id='different', kind='unmodified', requested_percent=99)
    for part in altered['components']:
        part['bbox_um'] = [-1e12, 0, -1e12, 1]
        part['indices'] = [0]
    assert rank_scores(altered, weights, reference) == before
    assert ranked_flags(altered, before, 0, 1) == ranked_flags(example, before, 0, 1)
    assert set(observed_signals(altered['components'][0])) == {'visual', 'absolute_influence', 'smallness', 'isolation'}


def test_reference_excludes_calibration_and_foreign_training_cases():
    c = cases(); before = fit_reference(c)
    changed = deepcopy(c)
    for example in changed:
        if example['split'] == 'calibration' or example['kind'] == 'synthetic':
            for p in example['components']:
                p.update(visual=1000, influence=-200, observed_tissue_area_mm2=500)
    assert fit_reference(changed) == before
    with pytest.raises(ValueError, match='Held-out'):
        fit_reference([{'split': 'test'}])
    with pytest.raises(ValueError, match='before feature processing'):
        investigate([{'split': 'test'}], {}, {})


def test_caps_do_not_split_tied_groups_and_abstention_preserves_budget():
    c = fixture_case()
    assert ranked_flags(c, [.8, .9], .7, 1) == [1]
    assert ranked_flags(c, [.9, .9], .7, 1) == []
    assert ranked_flags(c, [.9, .9], .7, 3) == [0, 1]
    assert ranked_flags(c, [.8, .9], .9, 1) == []  # Strict threshold.
    c['mapping_fraction'] = .89
    assert ranked_flags(c, [.8, .9], .7, 1) == []


def test_unsigned_relevance_does_not_equate_to_foreignness():
    p = fixture_case()['components'][0]
    p['influence'] = -.125
    assert observed_signals(p)['absolute_influence'] == .125
    p['status'] = 'not_evaluable_empty_counterfactual'
    assert observed_signals(p) is None


def test_failure_audit_counts_mixed_components_and_keeps_truth_out_of_detector():
    clean = fixture_case(); positive = fixture_case(synthetic=True)
    positive['components'][1]['indices'] = [4, 5]
    positive['components'][0]['indices'] = [0, 1, 2, 3]
    report, raw = failure_decomposition([clean, positive], dict(visual_threshold=.1, influence=.01, max_area_mm2=.25, min_isolation_mm=0))
    assert report['splits']['train']['mixed_component_cases'] == 1
    assert report['splits']['train']['unassigned_foreign_tiles'] == 0
    assert any(r['category'] == 'synthetic_mixed' and r['foreign_tiles'] == 1 and r['native_tiles'] == 1 for r in raw)


def test_selection_and_normalization_do_not_consume_calibration_outcomes():
    c = cases(); cfg = config(); v1 = dict(visual_threshold=.25, influence=.01, max_area_mm2=.25, min_isolation_mm=0)
    result, raw, decomposition = investigate(c, cfg, v1)
    altered = deepcopy(c)
    for example in altered:
        if example['split'] == 'calibration':
            example['host_truth'] = 'benign'
            for part in example['components']:
                part['visual'] = .999
                part['influence'] = -.9
    second, _, _ = investigate(altered, cfg, v1)
    assert result['reference'] == second['reference']
    assert result['primary_strategy'] == second['primary_strategy']
    for name in result['methods']:
        assert result['methods'][name]['selected_point'] == second['methods'][name]['selected_point']
        assert not result['methods'][name]['top_one_unbudgeted']['calibration']['deployment_eligible']
    assert not result['final_test_slides_scored']
    assert not result['final_test_predictions_authorized']
    json.dumps([result, raw, decomposition], allow_nan=False)
