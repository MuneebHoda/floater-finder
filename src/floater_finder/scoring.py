"""Cosine scoring and per-class pooling with explicit deterministic ties."""

import math
import numpy as np

from .artifacts import check_compatible, normalize

POOLING = ("mean", "top1pct", "top5pct")


def ensemble_prompts(encoded, prompts):
    """Normalize each prompt, average within class, then normalize the class mean."""
    vectors = []
    offset = 0
    for phrases in prompts.values():
        if not 3 <= len(phrases) <= 5:
            raise ValueError("Use 3-5 fixed phrases per class")
        vectors.append(normalize(np.asarray(encoded[offset:offset + len(phrases)])).mean(axis=0))
        offset += len(phrases)
    if offset != len(encoded):
        raise ValueError("Prompt embeddings do not align with phrases")
    return normalize(np.asarray(vectors))


def tile_scores(slide, text):
    check_compatible(slide, text)
    return np.einsum("id,cd->ic", slide.feats, text.feats, optimize=False)


def pool(scores, rule):
    scores = np.asarray(scores)
    if scores.ndim != 2 or min(scores.shape) == 0 or not np.isfinite(scores).all():
        raise ValueError("Expected finite nonempty [tiles,classes] scores")
    if rule == "mean":
        return scores.mean(axis=0)
    if rule not in POOLING:
        raise ValueError("Unknown pooling rule")
    fraction = 0.01 if rule == "top1pct" else 0.05
    k = max(1, math.ceil(fraction * len(scores)))
    # Equal tile scores retain artifact order, independently for each class.
    order = np.argsort(-scores, axis=0, kind="stable")[:k]
    return np.take_along_axis(scores, order, axis=0).mean(axis=0)


def predictions(slide, text):
    scores = tile_scores(slide, text)
    result = {}
    for rule in POOLING:
        values = pool(scores, rule)
        result[rule] = {"prediction": text.classes[int(np.argmax(values))],
                        "scores": dict(zip(text.classes, values.tolist()))}
    return result
