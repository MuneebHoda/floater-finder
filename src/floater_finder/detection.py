"""Training-free signals, clean-development calibration, and held-out evaluation."""

import numpy as np

from .artifacts import check_compatible
from .injection import oracle_remove
from .scoring import predictions, tile_scores

VARIANTS = ("organ_only", "visual_only", "combined")


def coords_mm(slide):
    scale = slide.metadata.get("microns_per_unit")
    if scale is None or not np.isfinite(scale) or scale <= 0:
        raise ValueError("Physical-distance detection needs a verified microns_per_unit scale")
    return slide.coords * scale / 1000


def organ_mismatch(slide, text):
    expected = slide.metadata["organ"]
    if expected not in text.classes:
        raise ValueError("Expected organ must have a fixed prompt ensemble")
    scores = tile_scores(slide, text)
    index = text.classes.index(expected)
    return np.delete(scores, index, axis=1).max(axis=1) - scores[:, index]


def visual_inconsistency(slide, exclusion_mm=1.0, chunk_size=256):
    if exclusion_mm < 0 or not np.isfinite(exclusion_mm) or not isinstance(chunk_size, int) or chunk_size < 1:
        raise ValueError("Invalid spatial exclusion/chunk size")
    coords = coords_mm(slide)
    n = len(slide.feats)
    best = np.full(n, -np.inf)
    # Both axes are blocked: no [all_tiles,all_tiles] allocation, even for reference tiles.
    for start in range(0, n, chunk_size):
        stop = min(n, start + chunk_size)
        for other in range(0, n, chunk_size):
            end = min(n, other + chunk_size)
            distance2 = ((coords[start:stop, None] - coords[None, other:end]) ** 2).sum(axis=2)
            allowed = distance2 > exclusion_mm ** 2
            similarity = np.einsum("ik,jk->ij", slide.feats[start:stop], slide.feats[other:end], optimize=False)
            best[start:stop] = np.maximum(best[start:stop], np.where(allowed, similarity, -np.inf).max(axis=1))
    if not np.isfinite(best).all():
        raise ValueError("Some tiles have no distant reference neighbor; signal is undefined")
    return 1 - np.clip(best, -1, 1)


def smooth(values, slide, radius_mm, chunk_size=256):
    if not np.isfinite(radius_mm) or radius_mm < 0:
        raise ValueError("Invalid smoothing radius")
    coords = coords_mm(slide)
    result = np.empty(len(values), dtype=float)
    for start in range(0, len(values), chunk_size):
        stop = min(len(values), start + chunk_size)
        totals = np.zeros(stop - start)
        counts = np.zeros(stop - start)
        for other in range(0, len(values), chunk_size):
            end = min(len(values), other + chunk_size)
            nearby = ((coords[start:stop, None] - coords[None, other:end]) ** 2).sum(axis=2) <= radius_mm ** 2
            totals += np.where(nearby, values[None, other:end], 0).sum(axis=1)
            counts += nearby.sum(axis=1)
        result[start:stop] = totals / counts
    return result


def _signals(slide, text, config):
    return np.column_stack([organ_mismatch(slide, text), visual_inconsistency(slide, config["exclusion_mm"], config["chunk_size"])])


def _combine(raw, slide, calibration):
    standardized = (raw - np.asarray(calibration["mean"])) / np.asarray(calibration["scale"])
    weight = calibration["lambda"]
    values = {"organ_only": standardized[:, 0], "visual_only": standardized[:, 1],
              "combined": weight * standardized[:, 0] + (1 - weight) * standardized[:, 1]}
    return {name: smooth(score, slide, calibration["smoothing_mm"], calibration["chunk_size"])
            for name, score in values.items()}


def calibrate(slides, text, exclusion_mm=1.0, smoothing_mm=0.1, weight=0.5, quantile=0.99, chunk_size=256):
    if not slides or not 0 <= weight <= 1 or not 0 < quantile < 1:
        raise ValueError("Clean development slides, bounded lambda and quantile are required")
    config = {"exclusion_mm": exclusion_mm, "smoothing_mm": smoothing_mm, "lambda": weight,
              "quantile": quantile, "chunk_size": chunk_size}
    raw = []
    for slide in slides:
        check_compatible(slide, text)
        if slide.metadata["split"] != "dev" or slide.foreign_mask.any() or "injection" in slide.metadata:
            raise ValueError("Calibrate only on separate, unmodified development slides")
        raw.append(_signals(slide, text, config))
    all_values = np.concatenate(raw)
    config.update(mean=all_values.mean(axis=0).tolist(), scale=np.maximum(all_values.std(axis=0), 1e-8).tolist(),
                  scale_floor=1e-8, model=text.model, text_fingerprint=text.fingerprint(), source_kind=text.source_kind,
                  development_patients=sorted({slide.metadata["patient_id"] for slide in slides}),
                  calibration_tile_count=len(all_values), thresholds={}, measured_development_false_alarm={})
    smoothed = [_combine(values, slide, config) for slide, values in zip(slides, raw)]
    for variant in VARIANTS:
        values = np.concatenate([entry[variant] for entry in smoothed])
        threshold = float(np.quantile(values, quantile, method="higher"))
        config["thresholds"][variant] = threshold
        config["measured_development_false_alarm"][variant] = float(np.mean(values > threshold))
    config["interpretation"] = "Fixed-coefficient training-free scoring with clean-development calibration; no unseen-FPR guarantee."
    return config


def _check_calibration(slide, text, calibration):
    check_compatible(slide, text)
    if calibration["model"] != text.model or calibration["text_fingerprint"] != text.fingerprint() or calibration["source_kind"] != text.source_kind:
        raise ValueError("Calibration model/prompt/source provenance mismatch")


def development_anomaly_scores(slide, text, calibration):
    """Resubstitution diagnostic only; never an independent evaluation result."""
    _check_calibration(slide, text, calibration)
    involved = {slide.metadata["patient_id"]}
    if "injection" in slide.metadata:
        involved.add(slide.metadata["injection"]["donor_patient_id"])
    if slide.metadata["split"] != "dev" or not involved <= set(calibration["development_patients"]):
        raise ValueError("Development diagnostics require calibration patients only, including donors")
    return _combine(_signals(slide, text, calibration), slide, calibration)


def anomaly_scores(slide, text, calibration):
    _check_calibration(slide, text, calibration)
    involved = {slide.metadata["patient_id"], slide.metadata.get("injection", {}).get("donor_patient_id")}
    if slide.metadata["split"] != "eval" or involved & set(calibration["development_patients"]):
        raise ValueError("Evaluation patients/donors must be independent of calibration")
    return _combine(_signals(slide, text, calibration), slide, calibration)


def auroc(truth, scores):
    truth, scores = np.asarray(truth, dtype=bool), np.asarray(scores)
    if truth.shape != scores.shape or not np.isfinite(scores).all():
        raise ValueError("AUROC inputs must be aligned and finite")
    positives, negatives = int(truth.sum()), int((~truth).sum())
    if not positives or not negatives:
        return None
    _, inverse, counts = np.unique(scores, return_inverse=True, return_counts=True)
    average_rank = np.cumsum(counts) - (counts - 1) / 2
    ranks = average_rank[inverse]
    return float((ranks[truth].sum() - positives * (positives + 1) / 2) / (positives * negatives))


def detection_metrics(truth, scores, flags):
    positives, negatives = int(truth.sum()), int((~truth).sum())
    tp, fp, removed = int((truth & flags).sum()), int((~truth & flags).sum()), int(flags.sum())
    return {"auroc": auroc(truth, scores), "detection_rate": tp / positives if positives else None,
            "measured_false_alarm_rate": fp / negatives if negatives else None,
            "precision": tp / removed if removed else None, "fragment_hit": bool(tp) if positives else None,
            "genuine_host_tiles_removed": fp, "foreign_tiles": positives, "host_tiles": negatives, "removed_tiles": removed}


def evaluate(slide, text, calibration, seed=0):
    scores = anomaly_scores(slide, text, calibration)
    original = oracle_remove(slide)
    baseline = predictions(original, text)
    no_filter = predictions(slide, text)
    result = {"source_kind": slide.metadata["source_kind"], "no_filter": no_filter, "oracle": baseline, "variants": {}}
    flags_by_variant = {}
    for variant, values in scores.items():
        flags = values > calibration["thresholds"][variant]
        flags_by_variant[variant] = flags
        metrics = detection_metrics(slide.foreign_mask, values, flags)
        retained = ~flags
        filtered = predictions(slide.subset(retained), text) if retained.any() else None
        rng = np.random.default_rng(seed)
        random_keep = np.ones(len(flags), dtype=bool)
        random_keep[rng.choice(len(flags), int(flags.sum()), replace=False)] = False
        random_prediction = predictions(slide.subset(random_keep), text) if random_keep.any() else None
        metrics.update(filtered=filtered, random_same_count=random_prediction,
            recovered={rule: filtered[rule]["prediction"] == baseline[rule]["prediction"] if filtered else None for rule in baseline},
            clean_prediction_changed={rule: filtered[rule]["prediction"] != no_filter[rule]["prediction"] if filtered else None for rule in baseline}
                if not slide.foreign_mask.any() else None)
        if not slide.foreign_mask.any() and slide.metadata.get("label") in text.classes:
            metrics["clean_correct_to_wrong"] = {
                rule: no_filter[rule]["prediction"] == slide.metadata["label"] and
                      (filtered is None or filtered[rule]["prediction"] != slide.metadata["label"])
                for rule in baseline}
        result["variants"][variant] = metrics
    return result, scores, flags_by_variant
