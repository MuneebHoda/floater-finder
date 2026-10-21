"""Morphology scores from image vectors and relative geometry, without truth inputs."""
import numpy as np

METHODS = ('nn1', 'nn5', 'robust_nn5', 'background_centroid',
           'component_neighbor', 'distant_nn5', 'cohort_centroid5')


def unit_mean(values):
    mean = np.asarray(values, dtype=np.float64).mean(axis=0)
    norm = np.linalg.norm(mean)
    if norm <= 1e-12:
        return None
    return mean / norm


def cohort_distance(centroid, reference_centroids):
    """One normalized centroid per reference slide gives equal slide weight."""
    refs = np.asarray(reference_centroids, dtype=np.float64)
    if centroid is None or refs.size == 0:
        return None
    distances = 1 - np.clip(refs @ centroid, -1, 1)
    k = min(5, len(distances))
    return float(np.partition(distances, k-1)[:k].mean())


def _nearest(similarities, k=5):
    k = min(k, similarities.shape[1])
    if not k:
        return None
    top = np.partition(similarities, similarities.shape[1]-k, axis=1)[:, -k:]
    return 1 - np.clip(top, -1, 1).mean(axis=1)


def anomaly_features(feats, coords_um, components, reference_centroids=(), distant_um=500.):
    """Return scores in component order; unavailable context is an explicit None.

    Components provide only disjoint tile indices. IDs, labels, annotations,
    synthetic truth, absolute coordinates and prediction scores are not inputs.
    Empty exclusion is unevaluable even if cohort context is available.
    """
    feats = np.asarray(feats, dtype=np.float64)
    coords = np.asarray(coords_um, dtype=np.float64)
    if (feats.ndim != 2 or not len(feats) or coords.shape != (len(feats), 2)
            or not np.isfinite(feats).all() or not np.isfinite(coords).all()
            or not np.allclose(np.linalg.norm(feats, axis=1), 1, atol=1e-4)):
        raise ValueError('Finite aligned normalized image vectors and physical coordinates required')
    if not np.isfinite(distant_um) or distant_um < 0:
        raise ValueError('Invalid physical context distance')
    occupied = set(); indices = []
    for part in components:
        raw = np.asarray(part['indices'])
        if raw.ndim != 1 or raw.dtype.kind not in 'iu' or not len(raw):
            raise ValueError('Nonempty integer component indices required')
        ix = raw.astype(int)
        if len(set(ix)) != len(ix) or ix.min() < 0 or ix.max() >= len(feats) or occupied.intersection(ix):
            raise ValueError('Components must be disjoint valid indices')
        occupied.update(ix); indices.append(ix)
    similarity = np.clip(feats @ feats.T, -1, 1)
    distances_um = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=2)
    centroids = [unit_mean(feats[ix]) for ix in indices]
    result = []
    for number, ix in enumerate(indices):
        keep = np.ones(len(feats), dtype=bool); keep[ix] = False
        record = dict(status='evaluable', centroid=None if centroids[number] is None else centroids[number].tolist(),
                      scores={name: None for name in METHODS}, distant_context_tiles=0)
        if not keep.any():
            record['status'] = 'not_evaluable_empty_counterfactual'; result.append(record); continue
        cross = similarity[np.ix_(ix, np.flatnonzero(keep))]
        nearest1 = _nearest(cross, 1); nearest5 = _nearest(cross)
        record['scores'].update(nn1=float(np.median(nearest1)), nn5=float(np.median(nearest5)))
        background = similarity[np.ix_(np.flatnonzero(keep), np.flatnonzero(keep))].copy()
        if len(background) > 1:
            np.fill_diagonal(background, -np.inf)
            k = min(5, len(background)-1)
            reference_distances = _nearest(background, k)
            median = np.median(reference_distances)
            # A fixed floor prevents arbitrary division by tiny within-background MAD.
            scale = max(1.4826 * float(np.median(np.abs(reference_distances-median))), .01)
            record['scores']['robust_nn5'] = float((np.median(nearest5)-median)/scale)
        center = centroids[number]; background_center = unit_mean(feats[keep])
        if center is not None and background_center is not None:
            record['scores']['background_centroid'] = float(1-np.clip(center @ background_center, -1, 1))
        others = [c for i, c in enumerate(centroids) if i != number and c is not None]
        if center is not None and others:
            record['scores']['component_neighbor'] = float(1-max(np.clip(np.asarray(others) @ center, -1, 1)))
        # Relative distance only; no right-edge, bounding-box or source-ID features.
        far = np.flatnonzero(keep & (distances_um[ix].min(axis=0) >= distant_um))
        record['distant_context_tiles'] = len(far)
        if len(far):
            record['scores']['distant_nn5'] = float(np.median(_nearest(similarity[np.ix_(ix, far)])))
        record['scores']['cohort_centroid5'] = cohort_distance(center, reference_centroids)
        result.append(record)
    return result
