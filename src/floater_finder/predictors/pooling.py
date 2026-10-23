"""Annotation-free, permutation-invariant summary features."""
import numpy as np


def slide_vector(feats, rule='mean', top_k=5):
    x = np.asarray(feats, dtype=np.float64)
    if x.ndim != 2 or min(x.shape) == 0 or not np.isfinite(x).all():
        raise ValueError('Finite nonempty [tiles, dimensions] features required')
    if rule == 'mean':
        return x.mean(axis=0)
    if rule != 'mean_max_topk' or type(top_k) is not int or top_k < 1:
        raise ValueError('Known feature rule and positive fixed top K required')
    k = min(top_k, len(x))
    # Coordinatewise order statistics, not annotation- or label-guided tile selection.
    top = np.partition(x, len(x)-k, axis=0)[-k:].mean(axis=0)
    return np.concatenate([x.mean(axis=0), x.max(axis=0), top])
