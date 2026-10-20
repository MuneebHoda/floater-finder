"""Embedding-only piece counterfactuals; no model loading or tissue deletion."""

from collections import deque
import json

import numpy as np

from .artifacts import Slide


def analyze_saved_slide(path, scorer, *, scorer_id, max_gap_tiles=1, alert_policy=None):
    """Analyze a validated saved Slide without guessing physical tile geometry.

    ``tile_step``, ``tile_size`` and ``microns_per_unit`` must be recorded in the
    artifact metadata. Image resize dimensions and slide-level grades are never
    substituted for physical footprints or per-tile truth. Scorers receive only
    embeddings and coordinates; label fractions and foreign masks are not inputs.
    The array API below remains available for other saved embedding formats.
    """
    slide = Slide.load(path)
    metadata = slide.metadata
    for key in ("tile_step", "tile_size", "microns_per_unit"):
        if metadata.get(key) is None:
            raise ValueError(f"Saved slide requires explicit physical geometry: {key}")
    report = analyze_fragment_dependence(
        slide.feats, slide.coords, scorer, tile_step=metadata["tile_step"],
        tile_size=metadata["tile_size"], coordinate_units=metadata["coordinate_units"],
        microns_per_unit=metadata["microns_per_unit"], source_kind=metadata["source_kind"],
        scorer_id=scorer_id, tile_ids=slide.tile_ids, max_gap_tiles=max_gap_tiles,
        alert_policy=alert_policy)
    keys = ("slide_id", "patient_id", "patient_id_known", "project", "organ", "split",
            "split_provenance", "source_kind", "data_provider", "coordinate_reference", "model")
    # A JSON copy keeps returned provenance independent of the loaded metadata.
    report["slide_provenance"] = json.loads(json.dumps(
        {key: metadata[key] for key in keys if key in metadata}, allow_nan=False))
    return report


def _positive_pair(value, name):
    pair = np.asarray(value, dtype=float)
    if pair.ndim == 0:
        pair = np.repeat(pair, 2)
    if pair.shape != (2,) or not np.isfinite(pair).all() or np.any(pair <= 0):
        raise ValueError(f"{name} must contain one or two finite positive values")
    return pair


def connected_pieces(coords, tile_step, max_gap_tiles=1):
    """8-connected occupied grid cells, bridging at most one missing tile per edge.

    A gap of one means Chebyshev grid distance <= 2. Connectivity is transitive;
    nearby tissue can merge. Input coordinates must share a regular grid origin.
    """
    coords = np.asarray(coords, dtype=float)
    step = _positive_pair(tile_step, "tile_step")
    if coords.ndim != 2 or coords.shape[1] != 2 or not len(coords) or not np.isfinite(coords).all():
        raise ValueError("Coordinates must be nonempty finite [N,2]")
    if type(max_gap_tiles) is not int or max_gap_tiles not in (0, 1):
        raise ValueError("max_gap_tiles must be 0 or 1")
    relative = (coords - coords.min(axis=0)) / step
    rounded = np.rint(relative)
    if np.any(np.abs(rounded) > 2**52) or not np.allclose(relative, rounded, rtol=0, atol=1e-6):
        raise ValueError("Coordinates must lie on the declared tile grid")
    cells = rounded.astype(np.int64)
    lookup = {tuple(cell): index for index, cell in enumerate(cells)}
    if len(lookup) != len(coords):
        raise ValueError("Duplicate tile coordinates")
    radius = max_gap_tiles + 1
    offsets = [(x, y) for x in range(-radius, radius + 1) for y in range(-radius, radius + 1)
               if x or y]
    unseen = set(range(len(cells)))
    pieces = []
    # Geometric ordering makes piece IDs independent of the input row order.
    for start in sorted(unseen, key=lambda i: tuple(cells[i])):
        if start not in unseen:
            continue
        queue, members = deque([start]), []
        unseen.remove(start)
        while queue:
            index = queue.popleft()
            members.append(index)
            x, y = cells[index]
            for dx, dy in offsets:
                neighbor = lookup.get((x + dx, y + dy))
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        pieces.append(np.asarray(sorted(members), dtype=int))
    return pieces


def _isolation_mm(piece_coords_um, other_coords_um, size_um):
    if not len(other_coords_um):
        return None
    minimum = np.inf
    # Exact nearest rectangular-footprint separation, with bounded pairwise memory.
    for start in range(0, len(piece_coords_um), 128):
        block = piece_coords_um[start:start + 128]
        for other_start in range(0, len(other_coords_um), 1024):
            other = other_coords_um[other_start:other_start + 1024]
            gaps = np.maximum(np.abs(block[:, None] - other[None]) - size_um, 0)
            minimum = min(minimum, float(np.sqrt(np.sum(gaps**2, axis=2)).min()))
    return minimum / 1000


def _score(scorer, embeddings, coords):
    # A scorer may mutate its arguments; counterfactuals must preserve saved inputs.
    result = scorer(embeddings.copy(), coords.copy())
    if not isinstance(result, dict) or not isinstance(result.get("prediction"), str) or not result["prediction"]:
        raise ValueError("Scorer must return a JSON mapping with a nonempty prediction string")
    try:
        return json.loads(json.dumps(result, allow_nan=False))
    except (TypeError, ValueError) as error:
        raise ValueError("Scorer output must be finite JSON") from error


def analyze_fragment_dependence(embeddings, coords, scorer, *, tile_step, tile_size,
                                coordinate_units, microns_per_unit, source_kind,
                                scorer_id, tile_ids=None, max_gap_tiles=1,
                                alert_policy=None):
    """Rerun a deterministic supplied scorer on the full bag and each piece omission.

    ``scorer(embeddings, coords)`` returns {"prediction": str, ...finite JSON...}.
    It must recompute pooling/attention on each remaining bag, with the same frozen
    model/settings, and must not depend on row order. Embeddings need not be unit
    normalized. Coordinates are tile top-left origins; step and footprint use the
    same units. Physical scale is measured microns per coordinate unit (scalar/XY).
    Nonoverlapping rectangular footprints are required; area is occupied tile
    footprint area, not tissue-mask area or bounding-box area.

    Optional ``alert_policy`` has max_area_mm2 and min_isolation_mm. These exploratory
    thresholds are uncalibrated. A small, isolated, decision-changing piece triggers
    review, including a genuine small positive region. Foreignness is never inferred.
    """
    features = np.asarray(embeddings)
    coords = np.asarray(coords, dtype=float)
    if features.ndim != 2 or min(features.shape) == 0 or features.dtype.kind != "f" or not np.isfinite(features).all():
        raise ValueError("Embeddings must be nonempty finite floating-point [N,D]")
    if coords.shape != (len(features), 2):
        raise ValueError("Coordinates must align with embeddings")
    if source_kind not in {"fixture", "real"}:
        raise ValueError("source_kind must be fixture or real")
    if coordinate_units not in {"microns", "level0_pixels", "grid"}:
        raise ValueError("Explicit coordinate_units must be microns, level0_pixels or grid")
    if not isinstance(scorer_id, str) or not scorer_id.strip():
        raise ValueError("A scorer_id describing the frozen scoring configuration is required")
    step = _positive_pair(tile_step, "tile_step")
    size = _positive_pair(tile_size, "tile_size")
    scale = _positive_pair(microns_per_unit, "microns_per_unit")
    if coordinate_units == "microns" and not np.array_equal(scale, [1, 1]):
        raise ValueError("Micron coordinates require microns_per_unit=1")
    if np.any(size > step):
        raise ValueError("Overlapping tile footprints are unsupported for area calculations")
    if tile_ids is None:
        tile_ids = [str(i) for i in range(len(features))]
    ids = np.asarray(tile_ids)
    if (ids.shape != (len(features),) or ids.dtype.kind not in "US" or
            len(set(ids.tolist())) != len(ids) or np.any(ids == "")):
        raise ValueError("tile_ids must be aligned, unique nonempty strings")
    policy = None
    if alert_policy is not None:
        if not isinstance(alert_policy, dict) or set(alert_policy) != {"max_area_mm2", "min_isolation_mm"}:
            raise ValueError("alert_policy needs max_area_mm2 and min_isolation_mm")
        policy = {}
        for key, value in alert_policy.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value) or value < 0:
                raise ValueError("Alert thresholds must be finite nonnegative numbers")
            policy[key] = float(value)
        policy["validation"] = "uncalibrated_exploratory_only"
    components = connected_pieces(coords, step, max_gap_tiles)
    physical_coords, physical_size = coords * scale, size * scale
    tile_area_mm2 = float(np.prod(physical_size) / 1e6)
    if not np.isfinite(physical_coords).all() or not np.isfinite(tile_area_mm2) or tile_area_mm2 <= 0:
        raise ValueError("Physical geometry must be finite and have positive area")
    baseline = _score(scorer, features, coords)
    pieces, alerts = [], []
    for number, indices in enumerate(components):
        keep = np.ones(len(features), dtype=bool)
        keep[indices] = False
        remaining = int(keep.sum())
        counterfactual = _score(scorer, features[keep], coords[keep]) if remaining else None
        changes = counterfactual["prediction"] != baseline["prediction"] if remaining else None
        area = len(indices) * tile_area_mm2
        isolation = _isolation_mm(physical_coords[indices], physical_coords[keep], physical_size)
        alert = None
        if policy is not None and changes is not None:
            alert = bool(changes and area < policy["max_area_mm2"] and
                         isolation is not None and isolation > policy["min_isolation_mm"])
        piece_id = f"piece-{number:03d}"
        piece = {"piece_id": piece_id, "tile_indices": indices.tolist(),
                 "tile_ids": ids[indices].tolist(), "tile_count": len(indices),
                 "bbox_coordinate_units": [*coords[indices].min(axis=0).tolist(),
                                           *(coords[indices].max(axis=0) + size).tolist()],
                 "area_mm2": area, "area_fraction": len(indices) / len(features),
                 "isolation_mm": isolation, "decision_changing": changes,
                 "counterfactual": {"status": "scored" if remaining else "not_evaluable_empty_slide",
                                    "remaining_tile_count": remaining, "result": counterfactual},
                 "review_alert": alert}
        pieces.append(piece)
        if alert:
            alerts.append({"type": "fragment_dependence_review", "piece_id": piece_id,
                           "baseline_prediction": baseline["prediction"],
                           "counterfactual_prediction": counterfactual["prediction"],
                           "message": "The decision depends on this piece. Review its context; foreign tissue is not established."})
    return {"schema_version": 1, "source_kind": source_kind,
            "category": "fixture_software_check" if source_kind == "fixture" else "fragment_dependence_analysis",
            "scorer_id": scorer_id, "decision_rule": "prediction_label_changes",
            "baseline": baseline, "tile_count": len(features), "piece_count": len(pieces),
            "geometry": {"coordinate_units": coordinate_units, "coordinate_reference": "tile_top_left",
                         "tile_step": step.tolist(), "tile_size": size.tolist(),
                         "microns_per_unit_xy": scale.tolist(), "connectivity": 8,
                         "max_gap_tiles": max_gap_tiles,
                         "area_definition": "sum_of_nonoverlapping_occupied_tile_footprints"},
            "pieces": pieces, "alerts_evaluated": policy is not None,
            "alert_policy": policy, "alerts": alerts, "tissue_action": "preserve_all_tissue",
            "limitations": ["Decision dependence does not establish foreign tissue; genuine small positive regions can be decisive.",
                            "Adjacent pieces can merge; no scorer-driven tile-cluster fallback is implemented.",
                            "Sampled windows or missing tissue tiles cannot establish complete biopsy-piece boundaries.",
                            "No calibrated lookalike percentiles or clinically validated alert thresholds are available."]}
