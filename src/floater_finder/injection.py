"""Connected embedding-level contamination, never a pixel-level slide simulation."""

from collections import deque
from copy import deepcopy
from decimal import Decimal, ROUND_CEILING
import numpy as np

from .artifacts import Slide, check_compatible


def grid_neighbors(slide):
    step = np.asarray(slide.metadata.get("tile_step", []), dtype=float)
    if step.shape != (2,) or not np.isfinite(step).all() or np.any(step <= 0):
        raise ValueError("Positive tile_step [x,y] is required for spatial adjacency")
    grid = (slide.coords - slide.coords.min(axis=0)) / step
    if not np.allclose(grid, np.rint(grid), atol=1e-5, rtol=0):
        raise ValueError("Coordinates are not aligned to the declared tile grid")
    cells = [tuple(pair) for pair in np.rint(grid).astype(np.int64)]
    lookup = {cell: index for index, cell in enumerate(cells)}
    if len(lookup) != len(cells):
        raise ValueError("Duplicate grid positions")
    return [[lookup[pos] for pos in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)) if pos in lookup]
            for x, y in cells]


def connected_fragment(slide, count, seed):
    if not 1 <= count <= len(slide.feats):
        raise ValueError("Requested fragment exceeds donor capacity")
    neighbors = grid_neighbors(slide)
    remaining = set(range(len(neighbors)))
    components = []
    while remaining:
        queue = deque([min(remaining)])
        remaining.remove(queue[0])
        component = []
        while queue:
            node = queue.popleft()
            component.append(node)
            for other in neighbors[node]:
                if other in remaining:
                    remaining.remove(other)
                    queue.append(other)
        if len(component) >= count:
            components.extend(component)
    if not components:
        raise ValueError("No connected donor component is large enough")
    rng = np.random.default_rng(seed)
    start = int(rng.choice(sorted(components)))
    chosen = [start]
    selected = {start}
    frontier = set(neighbors[start])
    while len(chosen) < count:
        node = int(rng.choice(sorted(frontier)))
        chosen.append(node)
        selected.add(node)
        frontier.remove(node)
        frontier.update(other for other in neighbors[node] if other not in selected)
    return np.asarray(chosen, dtype=int)


def inject(host, donor, percent, seed):
    check_compatible(host, donor)
    if host.metadata["patient_id"] == donor.metadata["patient_id"]:
        raise ValueError("Host and donor must be different patients")
    if host.foreign_mask.any() or donor.foreign_mask.any() or "injection" in host.metadata or "injection" in donor.metadata:
        raise ValueError("Inputs must be original, unmodified slides")
    if host.metadata["split"] != donor.metadata["split"]:
        raise ValueError("Host/donor must be from the same development/evaluation split")
    if not np.isfinite(percent) or not 0 <= percent <= 100 or not isinstance(seed, int) or seed < 0:
        raise ValueError("Percent must be in [0,100] and seed a nonnegative integer")
    count = int((Decimal(str(percent)) * len(host.feats) / 100).to_integral_value(rounding=ROUND_CEILING))
    metadata = deepcopy(host.metadata)
    metadata["injection"] = {"kind": "synthetic_embedding_contamination", "seed": seed,
        "requested_percent": float(percent), "realized_percent": 100 * count / len(host.feats),
        "foreign_count": count, "original_host_count": len(host.feats),
        "rounding": "ceil(percent * original_host_count / 100)",
        "donor_slide_id": donor.metadata["slide_id"], "donor_patient_id": donor.metadata["patient_id"],
        "host_metadata": deepcopy(host.metadata)}
    if count == 0:
        metadata["injection"].update(donor_tile_ids=[], donor_indices=[], translation=[0, 0])
        return Slide(host.feats.copy(), host.coords.copy(), host.tile_ids.copy(), metadata)
    for key in ("coordinate_units", "microns_per_unit", "tile_step"):
        if host.metadata.get(key) != donor.metadata.get(key):
            raise ValueError(f"Host/donor spatial metadata mismatch: {key}")
    grid_neighbors(host)
    indices = connected_fragment(donor, count, seed)
    coords = donor.coords[indices].copy()
    step = np.asarray(host.metadata["tile_step"])
    # Place the fragment one tile step beyond the right edge, near the median host y.
    translation = np.array([host.coords[:, 0].max() + step[0], np.median(host.coords[:, 1])]) - coords.min(axis=0)
    coords += translation
    ids = np.array([f'{donor.metadata["slide_id"]}::{tile}' for tile in donor.tile_ids[indices]])
    metadata["injection"].update(donor_tile_ids=donor.tile_ids[indices].tolist(), donor_indices=indices.tolist(),
                                 translation=translation.tolist())
    return Slide(np.concatenate([host.feats, donor.feats[indices]]), np.concatenate([host.coords, coords]),
                 np.concatenate([host.tile_ids, ids]), metadata,
                 np.concatenate([host.foreign_mask, np.ones(count, dtype=bool)]))


def oracle_remove(slide):
    injection = slide.metadata.get("injection")
    if injection and int(slide.foreign_mask.sum()) != injection["foreign_count"]:
        raise RuntimeError("Oracle foreign-mask count contradicts injection provenance")
    if not slide.foreign_mask.any():
        original = injection["host_metadata"] if injection else slide.metadata
        return slide.subset(np.ones(len(slide.feats), dtype=bool), deepcopy(original))
    original = slide.metadata.get("injection", {}).get("host_metadata")
    if original is None:
        raise ValueError("Missing original host provenance for oracle recovery")
    return slide.subset(~slide.foreign_mask, deepcopy(original))


def verify_oracle(host, contaminated, text):
    from .scoring import predictions
    restored = oracle_remove(contaminated)
    if restored.metadata != host.metadata:
        raise RuntimeError("Oracle failed to restore original host provenance")
    for name in ("feats", "coords", "tile_ids"):
        if not np.array_equal(getattr(host, name), getattr(restored, name)):
            raise RuntimeError("Oracle failed to preserve original host arrays/order")
    before, after = predictions(host, text), predictions(restored, text)
    for rule in before:
        if before[rule]["prediction"] != after[rule]["prediction"] or not np.allclose(
                list(before[rule]["scores"].values()), list(after[rule]["scores"].values()), atol=1e-7, rtol=1e-6):
            raise RuntimeError("Oracle failed to recover original scores/prediction")
    return restored
