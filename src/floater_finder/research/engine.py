"""One embedding intervention engine, with exact historical PANDA adapters.

Coordinates never alter the feature bag for addition. Spatial realism here concerns
observed overview geometry only; it is not pixel composition or histology proof.
"""
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import numpy as np
from ..artifacts import Slide, check_compatible
from ..injection import grid_neighbors, connected_fragment
from ..panda_stress import foreign_count
from .contracts import DonorSelection, InterventionSpec, SlideArtifact, slide_identity


def donor_components(slide, rows, selection):
    if len(rows) != len(slide.feats) or [r['tile_id'] for r in rows] != slide.tile_ids.tolist():
        raise ValueError('Native annotation rows must align exactly with saved tile IDs')
    if not slide.metadata['panda']['mask_available'] and selection.condition != 'same_source_sham':
        return []
    a = np.array([[float(r[f'gleason{g}_fraction']) for g in (3, 4, 5)] for r in rows])
    if not np.isfinite(a).all() or (a < 0).any() or (a.sum(axis=1) > 1+1e-10).any():
        raise ValueError('Invalid native Gleason fractions')
    c, cutoff, grade = selection.condition, selection.minimum_fraction, slide.metadata['isup_grade']
    allowed = {'cancer': a.sum(axis=1) >= cutoff,
               'high_gp45': a[:, 1:].sum(axis=1) >= cutoff,
               'same_grade_gp3_only': (a[:, 0] >= cutoff) & (a[:, 1] == 0) & (a[:, 2] == 0),
               'high_gp4_only': (a[:, 1] >= cutoff) & (a[:, 2] == 0),
               'high_gp5_positive': a[:, 2] >= cutoff,
               'same_source_sham': np.ones(len(a), bool)}[c]
    if ((c == 'cancer' and grade not in (1, 4, 5)) or
            (c == 'same_grade_gp3_only' and grade != 1) or
            (c in ('high_gp45', 'high_gp4_only', 'high_gp5_positive') and grade not in (4, 5))):
        return []
    return tile_components(slide, np.flatnonzero(allowed))


def tile_components(slide, eligible_indices=None):
    neighbors = grid_neighbors(slide)
    remaining = set(range(len(slide.feats))) if eligible_indices is None else set(np.asarray(eligible_indices).tolist())
    if any(type(i) is not int or not 0 <= i < len(slide.feats) for i in remaining):
        raise ValueError('Valid native tile indices required')
    parts = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue, members = deque([start]), []
        while queue:
            i = queue.popleft()
            members.append(i)
            for j in neighbors[i]:
                if j in remaining:
                    remaining.remove(j)
                    queue.append(j)
        parts.append(np.array(sorted(members), dtype=int))
    return sorted(parts, key=lambda p: (-len(p), int(p[0])))


def validate_pair(host, donor, task, condition):
    check_compatible(host, donor)
    h, d = host.metadata, donor.metadata
    sham = condition == 'same_source_sham'
    expected = (h['isup_grade'] == 0 and d['isup_grade'] in (1, 4, 5) and condition == 'cancer') if task == 's1' else (
        h['isup_grade'] == 1 and
        ((condition == 'same_grade_gp3_only' and d['isup_grade'] == 1) or
         (condition in ('high_gp45', 'high_gp4_only', 'high_gp5_positive') and d['isup_grade'] in (4, 5))))
    if (any(m['project'] != 'PANDA' or m['data_provider'] != 'radboud' or
            m['cohort_split'] not in ('train', 'calibration') for m in (h, d)) or
            h['cohort_split'] != d['cohort_split'] or
            (h['slide_id'] == d['slide_id']) != sham or (not sham and not expected)):
        raise ValueError('Eligible PANDA Radboud task/condition pair in same development split required')
    if not sham and h.get('patient_id_known') and d.get('patient_id_known') and h['patient_id'] == d['patient_id']:
        raise ValueError('Known same-patient source pair is ineligible')
    if sham and slide_identity(host) != slide_identity(donor):
        raise ValueError('Same-source sham requires the identical original artifact')
    if any(s.foreign_mask.any() or 'injection' in s.metadata for s in (host, donor)):
        raise ValueError('Original unmodified inputs required')
    for key in ('coordinate_units', 'microns_per_unit', 'tile_step', 'tile_size'):
        if h.get(key) is None or h.get(key) != d.get(key):
            raise ValueError('Host/donor physical geometry differs')
    if h['coordinate_units'] != 'microns' or h['microns_per_unit'] != 1:
        raise ValueError('PANDA intervention coordinates must be recorded microns')
    size, step = np.asarray(h['tile_size']), np.asarray(h['tile_step'])
    if size.shape != (2,) or not np.isfinite(size).all() or (size <= 0).any() or np.any(size > step):
        raise ValueError('Positive nonoverlapping tile geometry required')
    grid_neighbors(host)
    grid_neighbors(donor)


def validate_indices(host, donor, indices, percent):
    count = foreign_count(percent, len(host.feats))
    a = np.asarray(indices)
    if (a.ndim != 1 or a.dtype.kind not in 'iu' or len(a) != count or
            len(set(a.tolist())) != count or (a < 0).any() or (a >= len(donor.feats)).any()):
        raise ValueError('Unique donor indices must match the requested count')
    if count:
        selected, seen = set(a.tolist()), {int(a[0])}
        queue, neighbors = deque(seen), grid_neighbors(donor)
        while queue:
            for other in neighbors[queue.popleft()]:
                if other in selected and other not in seen:
                    seen.add(other)
                    queue.append(other)
        if seen != selected:
            raise ValueError('Donor fragment must be four-connected')
    return a.astype(int), count


def select_donors(host, sources, selection, task, percent, seed):
    """Capacity-first deterministic selection; a fixed prefix keeps nested doses unique."""
    candidates = []
    needed = foreign_count(percent, len(host.feats))
    for sid, source in sources.items():
        donor = source['slide']
        try:
            validate_pair(host, donor, task, selection.condition)
        except ValueError:
            continue
        parts = donor_components(donor, source['rows'], selection)
        if not parts:
            continue
        part = parts[0]
        order = hashlib.sha256(f'{seed}/{host.metadata["slide_id"]}/{selection.condition}/{sid}'.encode()).hexdigest()
        candidates.append((len(part) < needed, 0 if len(part) >= needed else -len(part), order, sid, part))
    result = []
    for _, _, _, sid, part in sorted(candidates, key=lambda row: row[:4])[:selection.donors_per_host]:
        count = min(needed, len(part))
        order = part[connected_fragment(sources[sid]['slide'].subset(part), count, seed)] if count else np.array([], int)
        result.append(dict(donor_id=sid, indices=order.tolist(), component_capacity=len(part),
                           requested_capacity=needed, full_capacity=len(part) >= needed))
    return result


@dataclass(frozen=True)
class VerifiedOccupancy:
    """All pixels in a bounded overview, including unsampled tissue; not sampled-cell emptiness."""
    mask_bytes: bytes
    shape: tuple[int, int]
    pixel_um: tuple[float, float]
    origin_um: tuple[float, float]
    source_sha256: str
    segmentation_rule: str

    @classmethod
    def from_mask(cls, mask, pixel_um, source_sha256, segmentation_rule, origin_um=(0., 0.)):
        mask = np.asarray(mask)
        if (mask.ndim != 2 or mask.dtype.kind != 'b' or not 0 < mask.size <= 4_000_000 or
                len(source_sha256) != 64 or any(c not in '0123456789abcdef' for c in source_sha256) or
                not segmentation_rule or np.shape(pixel_um) != (2,) or np.shape(origin_um) != (2,) or
                not np.isfinite(pixel_um).all() or np.any(np.asarray(pixel_um) <= 0) or not np.isfinite(origin_um).all()):
            raise ValueError('Bounded complete boolean overview, physical scale and SHA provenance required')
        return cls(mask.tobytes(), mask.shape, tuple(pixel_um), tuple(origin_um), source_sha256, segmentation_rule)

    def mask(self):
        return np.frombuffer(self.mask_bytes, dtype=bool).reshape(self.shape)

    def bounds(self):
        return np.asarray(self.origin_um) + np.asarray(self.shape[::-1])*self.pixel_um


def _raster_rect(coords, size, occupancy):
    origin, scale = np.array(occupancy.origin_um), np.array(occupancy.pixel_um)
    start = np.floor((coords-origin)/scale).astype(int)
    stop = np.ceil((coords+size-origin)/scale).astype(int)
    if (start < 0).any() or np.any(stop > np.array(occupancy.shape[::-1])):
        raise ValueError('Fragment exceeds verified image bounds')
    return start, stop


def _valid_position(coords, host, occupancy, max_distance_um=224.):
    mask, size = occupancy.mask(), np.asarray(host.metadata['tile_size'])
    for point in coords:
        start, stop = _raster_rect(point, size, occupancy)
        if mask[start[1]:stop[1], start[0]:stop[0]].any():
            return False
        overlap = np.all((host.coords < point+size) & (host.coords+size > point), axis=1)
        if overlap.any():
            return False
    # Expand actual footprints, not the fragment bbox: empty holes are not tissue boundaries.
    for point in coords:
        lo = np.maximum(np.floor((point-max_distance_um-np.array(occupancy.origin_um))/occupancy.pixel_um).astype(int), 0)
        hi = np.minimum(np.ceil((point+size+max_distance_um-np.array(occupancy.origin_um))/occupancy.pixel_um).astype(int), occupancy.shape[::-1])
        if mask[lo[1]:hi[1], lo[0]:hi[0]].any():
            return True
    return False


def placement_anchor(host, donor, indices, occupancy, seed, anchor=None):
    if not isinstance(occupancy, VerifiedOccupancy):
        raise ValueError('Near/context placement requires verified complete overview occupancy')
    if not len(indices):
        return np.zeros(2)
    fragment = donor.coords[indices]-donor.coords[indices].min(axis=0)
    step = np.asarray(host.metadata['tile_step'])
    origin = host.coords.min(axis=0)
    if anchor is not None:
        anchor = np.asarray(anchor, dtype=float)
        if anchor.shape != (2,) or not np.isfinite(anchor).all() or not np.allclose((anchor-origin)/step, np.rint((anchor-origin)/step), atol=1e-5, rtol=0):
            raise ValueError('Placement anchor must align with the host physical grid')
        if not _valid_position(fragment+anchor, host, occupancy):
            raise ValueError('Placement overlaps observed tissue/host or is not near observed tissue')
        return anchor
    lower = np.ceil((np.asarray(occupancy.origin_um)-origin)/step).astype(int)
    upper = np.floor((occupancy.bounds()-fragment.max(axis=0)-np.asarray(host.metadata['tile_size'])-origin)/step).astype(int)
    shape = np.maximum(upper-lower+1, 0)
    if np.prod(shape) > 100_000:
        raise ValueError('Placement search exceeds bounded 100,000 grid anchors; provide verified anchor')
    cells = [(x, y) for y in range(lower[1], upper[1]+1) for x in range(lower[0], upper[0]+1)]
    rng = np.random.default_rng(seed)
    for i in rng.permutation(len(cells)):
        candidate = origin + np.asarray(cells[i])*step
        if _valid_position(fragment+candidate, host, occupancy):
            return candidate
    raise ValueError('No bounded unoccupied near-tissue placement exists')


@dataclass(frozen=True)
class InterventionResult:
    slide: Slide
    original: SlideArtifact
    audit_json: str

    def restore(self):
        """Exact recovery uses retained original state, including replaced representations."""
        import json
        audit = json.loads(self.audit_json)
        if slide_identity(self.slide) != audit['result_identity']:
            raise RuntimeError('Intervention output changed after creation')
        return self.original.materialize()

    def verify(self, scorer=None):
        original, restored = self.original.materialize(), self.restore()
        if slide_identity(original) != slide_identity(restored):
            raise RuntimeError('Exact original-state recovery failed')
        if scorer is not None and scorer(original) != scorer(restored):
            raise RuntimeError('Exact prediction recovery failed')
        return restored


def _legacy_metadata(host, donor, indices, percent, seed, task, condition, translation):
    h, d = host.metadata, donor.metadata
    value = dict(kind=f'synthetic_PANDA_{task.upper()}_embedding_contamination')
    if task == 's2':
        value['condition'] = condition
    value.update(seed=seed, requested_percent=float(percent), realized_percent=100*len(indices)/len(host.feats),
        foreign_count=len(indices), original_host_count=len(host.feats), rounding='ceil(percent * original_host_count / 100)',
        donor_slide_id=d['slide_id'], donor_patient_id=d['patient_id'], patient_independence_verified=False,
        donor_indices=indices.tolist(), donor_tile_ids=donor.tile_ids[indices].tolist(), translation_um=translation.tolist(),
        placement='three x-grid steps beyond host right edge; y rounded to host grid', host_metadata=deepcopy(h))
    return value


def apply_intervention(host, donor, spec, *, occupancy=None):
    from dataclasses import asdict
    from .contracts import canonical
    validate_pair(host, donor, spec.task, spec.condition)
    indices, count = validate_indices(host, donor, np.asarray(spec.donor_indices, dtype=int), spec.percent)
    metadata = deepcopy(host.metadata)
    coords, translation = donor.coords[indices].copy(), np.zeros(2)
    if spec.mode == 'append_legacy':
        if count:
            step = np.asarray(host.metadata['tile_step'])
            origin = host.coords[:, 1].min()
            y = origin + np.rint((np.median(host.coords[:, 1])-origin)/step[1])*step[1]
            translation = np.array([host.coords[:, 0].max()+3*step[0], y])-coords.min(axis=0)
            coords += translation
    elif spec.mode in ('near_tissue', 'within_region_context'):
        anchor = placement_anchor(host, donor, indices, occupancy, spec.seed, spec.placement_anchor_um)
        if count:
            translation = anchor-coords.min(axis=0)
            coords += translation
    replacement = spec.mode == 'replacement'
    if replacement:
        target = np.asarray(spec.replacement_indices, dtype=int)
        if (len(target) != count or len(set(target.tolist())) != count or (target < 0).any() or (target >= len(host.feats)).any()):
            raise ValueError('Replacement requires unique existing host indices matching donor count')
        if count > 1:
            selected, seen, neighbors = set(target.tolist()), {int(target[0])}, grid_neighbors(host)
            queue = deque(seen)
            while queue:
                for j in neighbors[queue.popleft()]:
                    if j in selected and j not in seen:
                        seen.add(j); queue.append(j)
            if seen != selected:
                raise ValueError('Replacement host region must be four-connected')
        feats, all_coords, ids, truth = host.feats.copy(), host.coords.copy(), host.tile_ids.copy(), host.foreign_mask.copy()
        feats[target] = donor.feats[indices]
        truth[target] = spec.condition != 'same_source_sham'
    else:
        feats = np.concatenate([host.feats, donor.feats[indices]])
        all_coords = np.concatenate([host.coords, coords])
        added_ids = [f'{donor.metadata["slide_id"]}::{t}' for t in donor.tile_ids[indices]]
        # Preserve the historical S1 empty-array Unicode widening as well as the IDs.
        suffix = np.array(added_ids) if spec.task == 's1' and spec.mode == 'append_legacy' else np.array(added_ids, dtype=str)
        ids = np.concatenate([host.tile_ids, suffix])
        truth = np.concatenate([host.foreign_mask, np.full(count, spec.condition != 'same_source_sham', dtype=bool)])
    metadata['injection'] = _legacy_metadata(host, donor, indices, spec.percent, spec.seed, spec.task, spec.condition, translation)
    if spec.mode != 'append_legacy' or spec.condition == 'same_source_sham':
        metadata['injection'].update(kind='synthetic_PANDA_research_v1_representation_intervention', mode=spec.mode,
            condition=spec.condition, placement='retained host coordinates' if replacement else 'verified overview empty footprint; within 224 um Chebyshev tissue context',
            representation_only=True, pixel_composition=False, synthetic_foreign_tissue=spec.condition != 'same_source_sham',
            replacement_indices=list(spec.replacement_indices), altered_count=count, foreign_count=int(truth.sum()), context=spec.context,
            occupancy_source_sha256=occupancy.source_sha256 if occupancy else None)
    result = Slide(feats, all_coords, ids, metadata, truth)
    return InterventionResult(result, SlideArtifact.from_slide(host), canonical(dict(schema_version=1, spec=asdict(spec),
        host_identity=slide_identity(host), donor_identity=slide_identity(donor), result_identity=slide_identity(result),
        dose_denominator='original_host_tiles', realized_percent=100*count/len(host.feats), representation_only=True,
        synthetic_foreign_tissue=spec.condition != 'same_source_sham', oracle_original_state_retained=True,
        altered_indices=list(spec.replacement_indices) if replacement else list(range(len(host.feats), len(host.feats)+count)),
        actual_foreign_count=int(truth.sum()), altered_count=count,
        occupancy=(dict(source_sha256=occupancy.source_sha256, mask_sha256=hashlib.sha256(occupancy.mask_bytes).hexdigest(),
            shape=list(occupancy.shape), pixel_um=list(occupancy.pixel_um), origin_um=list(occupancy.origin_um),
            segmentation_rule=occupancy.segmentation_rule) if occupancy is not None else None))))


def legacy_s1(host, donor, indices, percent, seed):
    return apply_intervention(host, donor, InterventionSpec('s1', 'cancer', 'append_legacy', percent, seed, tuple(indices))).slide


def legacy_s2(host, donor, indices, percent, seed, condition):
    return apply_intervention(host, donor, InterventionSpec('s2', condition, 'append_legacy', percent, seed, tuple(indices))).slide
