"""Fold-only review-budget calibration, with strict ties and no truth inputs."""
import numpy as np


def budget_threshold(clean_score_lists, max_slide_rate=.1, max_components=.5):
    if not clean_score_lists:
        raise ValueError('Clean training references required')
    values = sorted(set(float(x) for row in clean_score_lists for x in row if x is not None))
    if not all(np.isfinite(values)):
        raise ValueError('Nonfinite reference scores')
    # Strict score > threshold excludes all ties together. The smallest passing
    # threshold is the most permissive point allowed by clean-fold burden alone.
    for threshold in values:
        counts = [sum(x is not None and x > threshold for x in row) for row in clean_score_lists]
        if np.mean(np.asarray(counts) > 0) <= max_slide_rate and np.mean(counts) <= max_components:
            return threshold
    return None  # no evaluable components; an explicit abstention


def shortlisted(scores, threshold, mapping_fraction, minimum_mapping=.9):
    if threshold is None or mapping_fraction < minimum_mapping:
        return []
    return [i for i, score in enumerate(scores) if score is not None and score > threshold]


def explain_shortlist(parts, indices):
    """Stage 2 explains influence without vetoing stage-1 visual review flags."""
    rows = [dict(component_index=i, signed_cancer_influence=parts[i].get('influence'),
                 decision_change=parts[i].get('decision_change'),
                 cancer_decision_change=parts[i].get('cancer_decision_change'),
                 counterfactual=parts[i].get('counterfactual')) for i in indices]
    return sorted(rows, key=lambda r: (-(abs(r['signed_cancer_influence']) if r['signed_cancer_influence'] is not None else -1), r['component_index']))


def weighted_pr(scores, truth, weights):
    """All tied scores enter together. Weights give each host equal total mass."""
    if not scores:
        return dict(average_precision=None, points=[], weighted_positive=0., weighted_total=0.)
    scores=np.asarray(scores); truth=np.asarray(truth, bool); weights=np.asarray(weights, float)
    if not (scores.shape == truth.shape == weights.shape) or not np.isfinite(scores).all() or np.any(weights <= 0):
        raise ValueError('Finite aligned weighted observations required')
    order=np.argsort(-scores,kind='stable');scores=scores[order];truth=truth[order];weights=weights[order]
    tp=np.cumsum(weights*truth);fp=np.cumsum(weights*~truth);positive=float(tp[-1]);points=[];last=0.;ap=0.
    for i in np.flatnonzero(np.r_[scores[1:] != scores[:-1], True]):
        recall=float(tp[i]/positive) if positive else None;precision=float(tp[i]/(tp[i]+fp[i]))
        points.append(dict(threshold=float(scores[i]),precision=precision,recall=recall))
        if recall is not None:ap += (recall-last)*precision;last=recall
    return dict(average_precision=ap if positive else None,points=points,weighted_positive=positive,weighted_total=float(weights.sum()))
