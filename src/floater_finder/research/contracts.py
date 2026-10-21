"""Small versioned contracts around the established saved-CONCH artifacts."""
from dataclasses import dataclass
import hashlib
import json
import numpy as np
from ..artifacts import Slide

SCHEMA_VERSION = 1


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def slide_identity(slide):
    digest = hashlib.sha256(canonical(slide.metadata).encode())
    for key in ('feats', 'coords', 'tile_ids', 'foreign_mask'):
        a = getattr(slide, key)
        digest.update(canonical([key, str(a.dtype), list(a.shape)]).encode())
        digest.update(a.tobytes())
    return digest.hexdigest()


@dataclass(frozen=True)
class PredictionTask:
    name: str
    labels: tuple[str, ...]
    model_fingerprint: str
    pooling: str
    decision_rule: str = 'argmax; ties choose first label'
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self):
        if (self.schema_version != 1 or not self.name or not isinstance(self.labels, tuple) or len(self.labels) < 2 or
                len(set(self.labels)) != len(self.labels) or not self.model_fingerprint or
                not self.pooling or self.decision_rule != 'argmax; ties choose first label'):
            raise ValueError('Explicit versioned task, labels, model, pooling and decision rule required')


@dataclass(frozen=True)
class SlideArtifact:
    """A private immutable snapshot; materialization never exposes the saved arrays."""
    payload: bytes
    identity: str
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_slide(cls, slide):
        import io
        buffer = io.BytesIO()
        np.savez_compressed(buffer, feats=slide.feats, coords=slide.coords, tile_ids=slide.tile_ids,
                            foreign_mask=slide.foreign_mask, metadata=canonical(slide.metadata))
        return cls(buffer.getvalue(), slide_identity(slide))

    def materialize(self):
        import io
        if self.schema_version != 1:
            raise ValueError('Unsupported artifact contract version')
        with np.load(io.BytesIO(self.payload), allow_pickle=False) as a:
            result = Slide(a['feats'], a['coords'], a['tile_ids'], json.loads(str(a['metadata'].item())),
                           a['foreign_mask'])
        if slide_identity(result) != self.identity:
            raise ValueError('Slide artifact snapshot identity differs')
        return result


@dataclass(frozen=True)
class FollowupCohort:
    """Explicit membership for previously verified fresh engineering artifacts."""
    manifest_sha256: str
    baseline_protocol_sha256: str
    members: tuple[tuple[str, str], ...]
    excluded_ids: tuple[str, ...]

    def __post_init__(self):
        hashes = [self.manifest_sha256, self.baseline_protocol_sha256]
        if (not isinstance(self.members, tuple) or not self.members or
                any(not isinstance(p, tuple) or len(p) != 2 for p in self.members) or
                not isinstance(self.excluded_ids, tuple)):
            raise ValueError('Immutable follow-up whitelist required')
        ids = [p[0] for p in self.members]
        hashes += [p[1] for p in self.members]
        if (any(not isinstance(s, str) or not s for s in ids) or len(set(ids)) != len(ids) or
                set(ids) & set(self.excluded_ids) or any(not isinstance(h, str) or len(h) != 64 or
                    any(c not in '0123456789abcdef' for c in h) for h in hashes)):
            raise ValueError('Hash-bound disjoint follow-up whitelist required')

    def validate(self, slide):
        m = slide.metadata
        if (m.get('cohort_split') != 'engineering' or
                m.get('selection_manifest_sha256') != self.manifest_sha256 or
                dict(self.members).get(m['slide_id']) != slide_identity(slide)):
            raise ValueError('Slide differs from verified follow-up whitelist or engineering provenance')


@dataclass(frozen=True)
class DonorSelection:
    condition: str
    minimum_fraction: float = .1
    seeds: tuple[int, ...] = (20261020, 20261021, 20261022)
    donors_per_host: int = 2
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self):
        allowed = ('cancer', 'high_gp45', 'same_grade_gp3_only', 'high_gp4_only', 'high_gp5_positive', 'same_source_sham')
        if (self.schema_version != 1 or self.condition not in allowed or not 0 < self.minimum_fraction <= 1 or not isinstance(self.seeds, tuple) or
                not self.seeds or len(set(self.seeds)) != len(self.seeds) or
                any(type(s) is not int or s < 0 for s in self.seeds) or self.donors_per_host < 1):
            raise ValueError('Valid annotation condition, independent seeds and bounded donor count required')


@dataclass(frozen=True)
class InterventionSpec:
    task: str
    condition: str
    mode: str
    percent: float
    seed: int
    donor_indices: tuple[int, ...]
    placement_anchor_um: tuple[float, float] | None = None
    replacement_indices: tuple[int, ...] = ()
    context: str | None = None
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self):
        if (self.schema_version != 1 or self.task not in ('s1', 's2') or
                self.mode not in ('append_legacy', 'near_tissue', 'replacement', 'within_region_context') or
                type(self.seed) is not int or self.seed < 0 or not np.isfinite(self.percent) or not 0 <= self.percent <= 10):
            raise ValueError('Known task/mode, nonnegative integer seed and bounded dose required')
        DonorSelection(self.condition)
        for field in ('donor_indices', 'replacement_indices'):
            values = getattr(self, field)
            if not isinstance(values, tuple) or any(not isinstance(i, (int, np.integer)) or isinstance(i, (bool, np.bool_)) for i in values):
                raise ValueError('Immutable integer index tuples required')
            object.__setattr__(self, field, tuple(int(i) for i in values))
        if self.mode == 'within_region_context' and not self.context:
            raise ValueError('Within-region stress requires an explicit context description')


@dataclass(frozen=True)
class DetectionResult:
    component_ids: tuple[str, ...]
    scores: tuple[float | None, ...]
    ranks: tuple[int | None, ...]
    flagged: tuple[bool, ...]
    explanations: tuple[str, ...]
    abstentions: tuple[str, ...] = ()
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self):
        n = len(self.component_ids)
        if (self.schema_version != 1 or len(set(self.component_ids)) != n or
                any(len(a) != n for a in (self.scores, self.ranks, self.flagged, self.explanations)) or
                any(x is not None and not np.isfinite(x) for x in self.scores) or
                any(x is not None and (type(x) is not int or x < 1) for x in self.ranks) or
                any(type(x) is not bool for x in self.flagged)):
            raise ValueError('Aligned finite component results required')


@dataclass(frozen=True)
class ExperimentRun:
    experiment_id: str
    hypothesis: str
    source_commit: str
    config_json: str
    dataset_identity: str
    split: str
    checkpoint_fingerprint: str
    embedding_fingerprint: str
    resources_json: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self):
        if (self.schema_version != 1 or self.split not in ('train', 'known_calibration', 'fresh_followup') or
                any(not value for value in (self.experiment_id, self.hypothesis, self.source_commit,
                                           self.dataset_identity, self.checkpoint_fingerprint, self.embedding_fingerprint))):
            raise ValueError('Identified development-only experiment required')
        for value in (self.config_json, self.resources_json):
            if canonical(json.loads(value)) != value:
                raise ValueError('Configuration/resources must be canonical immutable JSON')
