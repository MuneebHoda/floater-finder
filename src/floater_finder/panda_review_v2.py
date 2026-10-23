"""Rank saved CONCH review signals; experimental truth is restricted to evaluation."""
from collections import defaultdict
import json
import numpy as np
from .panda_review import evaluate_flags, matched_draws, summarize, acceptable, wilson
from .panda_final import clustered_ratio_interval

SIGNALS = ('visual', 'absolute_influence', 'smallness', 'isolation')


def observed_signals(component):
    """The detector boundary intentionally excludes coordinates, identities and annotations."""
    if component['status'] != 'evaluable':
        return None
    raw = dict(visual=component['visual'], absolute_influence=abs(component['influence']),
               smallness=-component['observed_tissue_area_mm2'], isolation=component['isolation_bbox_lower_bound_mm'])
    return {k: float(v) if v is not None and np.isfinite(v) else None for k, v in raw.items()}


def fit_reference(cases):
    if any(c['split'] not in ('train', 'calibration') for c in cases):
        raise ValueError('Held-out test cases are forbidden')
    reference = {name: [] for name in SIGNALS}
    for case in cases:
        if case['split'] != 'train' or case['kind'] != 'unmodified' or case['mapping_fraction'] < .9:
            continue
        for component in case['components']:
            values = observed_signals(component)
            if values:
                for name, value in values.items():
                    if value is not None:
                        reference[name].append(value)
    if not all(reference.values()):
        raise ValueError('Missing training-only clean feature reference')
    return {name: sorted(values) for name, values in reference.items()}


def rank_scores(case, weights, reference):
    if not weights or any(k not in SIGNALS or v < 0 for k, v in weights.items()) or not np.isclose(sum(weights.values()), 1):
        raise ValueError('Fixed nonnegative unit-sum signal weights required')
    scores = []
    for component in case['components']:
        raw = observed_signals(component)
        if raw is None or any(raw[k] is None for k in weights):
            scores.append(None)
            continue
        total = 0.
        for name, weight in weights.items():
            a = reference[name]; value = raw[name]
            percentile = (np.searchsorted(a, value, side='left') + np.searchsorted(a, value, side='right')) / (2 * len(a))
            total += weight * percentile
        scores.append(float(total))
    return scores


def ranked_flags(case, scores, threshold, cap):
    if case['mapping_fraction'] < .9:
        return []
    if len(scores) != len(case['components']) or cap not in (1, 3):
        raise ValueError('Aligned scores and preregistered review cap required')
    groups = defaultdict(list)
    for i, score in enumerate(scores):
        if score is not None and score > threshold:
            groups[score].append(i)
    result = []
    for score in sorted(groups, reverse=True):
        group = groups[score]
        if len(result) + len(group) > cap:
            break  # Do not use injection order or absolute position to split a tied group.
        result.extend(group)
        if len(result) == cap:
            break
    return result


def evaluate(cases, scores, threshold, cap):
    rows = []
    for case, values in zip(cases, scores):
        flags = ranked_flags(case, values, threshold, cap)
        row = evaluate_flags(case, flags)
        row.update({k: case[k] for k in ('case_id', 'host_id', 'split', 'kind', 'requested_percent')})
        if 'donor_id' in case:
            row['donor_id'] = case['donor_id']
        rows.append(row)
    return rows, summarize(rows)


def _selection_key(candidate):
    m = candidate['train']
    return (m['fragment_recall'] or 0, m['new_error_recovery_rate'] or 0,
            -(m['genuine_cancer_slide_flag_rate'] or 0), -m['unmodified_alert_rate'],
            -m['mean_components_per_unmodified_slide'], -candidate['cap'], candidate['threshold'])


def _uncertainty(rows, config):
    clean = [r for r in rows if r['kind'] == 'unmodified']
    positive = [dict(r, positive_trial=1) for r in rows if r['foreign_tiles'] > 0]
    induced = [dict(r, induced_trial=1) for r in positive if r['newly_induced_error']]
    kwargs = dict(seed=config['seed'], repetitions=config['bootstrap_repetitions'])
    return dict(unmodified_alert_rate_wilson95=wilson(sum(r['alerted'] for r in clean), len(clean)),
        fragment_recall_host_bootstrap95=clustered_ratio_interval(positive, 'fragment_hit', 'positive_trial', **kwargs),
        induced_error_recovery_host_bootstrap95=clustered_ratio_interval(induced, 'recovered_new_error', 'induced_trial', **kwargs),
        unit='unique host slide; donor reuse and unknown patient identity limit independence')


def _gate(metrics, config):
    return dict(burden_and_harm_pass=acceptable(metrics, config['budgets']),
        fragment_recall_pass=(metrics['fragment_recall'] or 0) >= config['minimum_useful_fragment_recall'],
        error_recovery_pass=(metrics['new_error_recovery_rate'] or 0) >= config['minimum_useful_induced_error_recovery'])


def investigate(cases, config, v1_rule):
    if any(c['split'] not in ('train', 'calibration') for c in cases):
        raise ValueError('Held-out test cases are forbidden before feature processing')
    reference = fit_reference(cases)
    train_indices = [i for i, c in enumerate(cases) if c['split'] == 'train']
    train = [cases[i] for i in train_indices]
    results = {}; raw = {}; candidates = []; selected = {}
    for name, weights in config['strategies'].items():
        all_scores = [rank_scores(c, weights, reference) for c in cases]
        training_scores = [all_scores[i] for i in train_indices]
        maxima = [max((v for v in s if v is not None), default=-1.) if c['mapping_fraction'] >= .9 else -1.
                  for c, s in zip(train, training_scores) if c['kind'] == 'unmodified']
        options = []
        for q in config['training_clean_slide_maximum_quantiles']:
            threshold = float(np.quantile(maxima, q, method='higher'))
            for cap in config['maximum_components']:
                _, metrics = evaluate(train, training_scores, threshold, cap)
                options.append(dict(strategy=name, weights=weights, training_clean_maximum_quantile=q,
                    threshold=threshold, cap=cap, train=metrics, burden_and_harm_pass=acceptable(metrics, config['budgets'])))
        _, reject_metrics = evaluate(train, training_scores, 1., 1)
        options.append(dict(strategy=name, weights=weights, training_clean_maximum_quantile=None,
            threshold=1., cap=1, train=reject_metrics, burden_and_harm_pass=acceptable(reject_metrics, config['budgets'])))
        eligible = [r for r in options if r['burden_and_harm_pass']]
        if not eligible:
            raise RuntimeError('Reject-all must preserve baseline and pass development burden/harm')
        point = max(eligible, key=_selection_key)
        selected[name] = point
        candidates.extend(options)
        rows, _ = evaluate(cases, all_scores, point['threshold'], point['cap'])
        raw[name] = rows
        result = dict(selected_point=point, selection_uses='training only', splits={}, top_one_unbudgeted={})
        for split in ('train', 'calibration'):
            split_rows = [r for r in rows if r['split'] == split]
            metrics = summarize(split_rows)
            result['splits'][split] = dict(metrics=metrics, gates=_gate(metrics, config), uncertainty=_uncertainty(split_rows, config))
            ids = [i for i, c in enumerate(cases) if c['split'] == split]
            top_rows, top_metrics = evaluate([cases[i] for i in ids], [all_scores[i] for i in ids], -1., 1)
            result['top_one_unbudgeted'][split] = dict(metrics=top_metrics, deployment_eligible=False,
                interpretation='Every evaluable non-tied slide is offered review; this is a ranking diagnostic, not a low-burden alert policy')
            # Every method gets its own matched burden and area control, including zero-budget methods.
            draws = [[] for _ in range(config['matched_random_draws'])]; forced = components = 0
            for i in ids:
                case = cases[i]; flags = ranked_flags(case, all_scores[i], point['threshold'], point['cap'])
                for index in flags:
                    b = np.searchsorted(config['matched_area_bins_mm2'], case['components'][index]['observed_tissue_area_mm2'])
                    pool_size = sum(p['status'] == 'evaluable' and np.searchsorted(config['matched_area_bins_mm2'], p['observed_tissue_area_mm2']) == b for p in case['components'])
                    forced += pool_size == 1; components += 1
                for draw, picked in enumerate(matched_draws(case, flags, config['matched_random_draws'], config['seed'])):
                    row = evaluate_flags(case, picked)
                    row.update({k: case[k] for k in ('case_id', 'host_id', 'split', 'kind', 'requested_percent')})
                    draws[draw].append(row)
            metrics_by_draw = [summarize(r) for r in draws]
            mean = {k: float(np.mean([m[k] for m in metrics_by_draw if m[k] is not None])) if any(m[k] is not None for m in metrics_by_draw) else None for k in metrics_by_draw[0]}
            result['splits'][split]['matched_random'] = dict(mean=mean, draws=metrics_by_draw,
                forced_singleton_size_matches=int(forced), requested_matches=components,
                interpretation='Fixed burden and area bins; singleton pools force the detector component, and zero flags give an uninformative control')
        result['operating_point_supported'] = all(all(s['gates'].values()) for s in result['splits'].values())
        results[name] = result
    primary_name = max(selected, key=lambda k: _selection_key(selected[k]))
    decomposition, component_rows = failure_decomposition(cases, v1_rule)
    return dict(schema_version=2, methods=results, primary_strategy=primary_name,
        operating_point_supported=results[primary_name]['operating_point_supported'], candidates=candidates,
        reference=reference, failure_decomposition=decomposition,
        final_test_predictions_authorized=False, final_test_slides_scored=False,
        calibration_role=config['calibration_role'], automatic_tissue_action='none',
        scientific_scope='Development on existing engineered right-edge S1 mixtures; no naturally occurring floaters or clinical validity established'), raw, component_rows


def _distribution(values):
    a = [v for v in values if v is not None]
    return dict(count=len(a), quantiles_0_10_25_50_75_90_100=np.quantile(a, [0, .1, .25, .5, .75, .9, 1]).tolist() if a else None)


def failure_decomposition(cases, v1_rule):
    rows = []; case_rows = []; clean_by_host = {c['host_id']: c for c in cases if c['kind'] == 'unmodified'}
    for case in cases:
        truth = np.asarray(case['foreign_mask'], bool)
        known = np.asarray(case['annotation_known'], bool); cancer = np.asarray(case['annotated_cancer'], bool)
        clean = clean_by_host[case['host_id']]
        native_xmax = max((p['bbox_um'][2] for p in clean['components']), default=None)
        assigned_foreign = set(); foreign_parts = []
        for i, part in enumerate(case['components']):
            ids = np.asarray(part['indices'], int); foreign = int(truth[ids].sum()); native = int((~truth[ids]).sum())
            genuine = bool((known[ids] & cancer[ids] & ~truth[ids]).any())
            category = ('synthetic_mixed' if native else 'synthetic_foreign_pure') if foreign else ('native_annotated_cancer' if genuine else 'native_without_positive_annotation')
            evaluable = part['status'] == 'evaluable'
            visual = bool(evaluable and part['visual'] > v1_rule['visual_threshold'])
            influence = bool(evaluable and part['influence'] >= v1_rule['influence'])
            spatial = bool(part['observed_tissue_area_mm2'] <= v1_rule['max_area_mm2'] and part['isolation_bbox_lower_bound_mm'] is not None and part['isolation_bbox_lower_bound_mm'] >= v1_rule['min_isolation_mm'])
            record = dict(case_id=case['case_id'], host_id=case['host_id'], split=case['split'], kind=case['kind'],
                requested_percent=case['requested_percent'], component_index=i, category=category, foreign_tiles=foreign,
                native_tiles=native, genuine_annotated_cancer=genuine, evaluable=evaluable,
                visual=part['visual'], influence=part['influence'], decision_change=part['decision_change'],
                cancer_decision_change=part['cancer_decision_change'], area_mm2=part['observed_tissue_area_mm2'],
                isolation_mm=part['isolation_bbox_lower_bound_mm'], v1_visual_pass=visual, v1_influence_pass=influence,
                v1_spatial_pass=spatial, v1_visual_and_influence=visual and influence,
                v1_all_pass=visual and influence and spatial and case['mapping_fraction'] >= .9,
                at_or_beyond_native_observed_right_edge=bool(foreign and native_xmax is not None and part['bbox_um'][0] >= native_xmax),
                evaluation_only_truth_and_position=True)
            rows.append(record)
            if foreign:
                assigned_foreign.update(ids[truth[ids]].tolist()); foreign_parts.append(record)
        if truth.any():
            case_rows.append(dict(case_id=case['case_id'], host_id=case['host_id'], donor_id=case['donor_id'], split=case['split'],
                requested_percent=case['requested_percent'], foreign_tiles=int(truth.sum()), assigned_foreign_tiles=len(assigned_foreign),
                unassigned_foreign_tiles=int(truth.sum())-len(assigned_foreign),
                foreign_bearing_components=len(foreign_parts), mixed_components=sum(p['native_tiles'] > 0 for p in foreign_parts),
                pure_foreign_components=sum(p['native_tiles'] == 0 for p in foreign_parts),
                foreign_component_at_or_beyond_right_edge=any(p['at_or_beyond_native_observed_right_edge'] for p in foreign_parts),
                v1_foreign_visual_pass=any(p['v1_visual_pass'] for p in foreign_parts),
                v1_foreign_influence_pass=any(p['v1_influence_pass'] for p in foreign_parts),
                v1_foreign_spatial_pass=any(p['v1_spatial_pass'] for p in foreign_parts),
                v1_foreign_visual_and_influence=any(p['v1_visual_and_influence'] for p in foreign_parts),
                v1_foreign_all_pass=any(p['v1_all_pass'] for p in foreign_parts)))
    report = dict(splits={}, categories={}, synthetic_case_diagnostics=case_rows,
        position_warning='Right-edge location is an experimental construction artifact, never detector input; no naturally occurring foreignness is established')
    for split in ('train', 'calibration'):
        positive = [r for r in case_rows if r['split'] == split]
        counts = {k: sum(bool(r[k]) for r in positive) for k in ('v1_foreign_visual_pass', 'v1_foreign_influence_pass', 'v1_foreign_spatial_pass', 'v1_foreign_visual_and_influence', 'v1_foreign_all_pass', 'foreign_component_at_or_beyond_right_edge')}
        report['splits'][split] = dict(positive_trials=len(positive), unique_hosts=len({r['host_id'] for r in positive}),
            unique_donors=len({r['donor_id'] for r in positive}), mixed_component_cases=sum(r['mixed_components'] > 0 for r in positive),
            foreign_tiles=sum(r['foreign_tiles'] for r in positive), unassigned_foreign_tiles=sum(r['unassigned_foreign_tiles'] for r in positive),
            foreign_bearing_components=sum(r['foreign_bearing_components'] for r in positive), **counts)
        report['categories'][split] = {}
        for category in sorted({r['category'] for r in rows}):
            group = [r for r in rows if r['split'] == split and r['category'] == category and (r['kind'] == 'unmodified' or r['foreign_tiles'] > 0)]
            influence = [r['influence'] for r in group if r['influence'] is not None]
            report['categories'][split][category] = dict(components=len(group),
                visual=_distribution([r['visual'] for r in group]), influence=_distribution(influence),
                decision_changes=sum(bool(r['decision_change']) for r in group), cancer_decision_changes=sum(bool(r['cancer_decision_change']) for r in group),
                influence_positive=sum(v > 0 for v in influence), influence_zero=sum(v == 0 for v in influence), influence_negative=sum(v < 0 for v in influence),
                area_mm2=_distribution([r['area_mm2'] for r in group]), isolation_mm=_distribution([r['isolation_mm'] for r in group]))
    return report, rows
