"""Software fixtures only: invariance/oracle acceptance, not scientific evidence."""
from dataclasses import FrozenInstanceError, replace
import json
import numpy as np
import pytest
from floater_finder.artifacts import TextEmbeddings
from floater_finder.panda_stress import inject_development_s1, cancer_components, binary_predictions
from floater_finder.panda_s2 import inject as old_s2, pattern_components, predictions as grade_predictions
from floater_finder.injection import verify_oracle
from floater_finder.research import (PredictionTask, SlideArtifact, DonorSelection, InterventionSpec, DetectionResult,
    ExperimentRun, Registry, apply_intervention, donor_components, select_donors, VerifiedOccupancy, legacy_s1, legacy_s2)
from floater_finder.research.contracts import canonical, slide_identity
from floater_finder.research.engine import placement_anchor
from conftest import MODEL
from test_panda_stress import slide


def text():
    names = ['benign', 'cancer', 'low_grade', 'high_grade']
    return TextEmbeddings(np.eye(4, 512), names, {n: [n] for n in names}, MODEL, 'fixture')


def same(a, b, dtype=True):
    assert a.metadata == b.metadata
    for k in ('feats', 'coords', 'tile_ids', 'foreign_mask'):
        assert np.array_equal(getattr(a, k), getattr(b, k))
        if dtype:
            assert getattr(a, k).dtype == getattr(b, k).dtype


@pytest.mark.parametrize('task,condition,grade', [('s1', 'cancer', 4), ('s2', 'high_gp45', 4),
    ('s2', 'same_grade_gp3_only', 1), ('s2', 'high_gp4_only', 4), ('s2', 'high_gp5_positive', 5)])
@pytest.mark.parametrize('percent', [0, .25, 10])
def test_legacy_exact_arrays_metadata_and_predictions(task, condition, grade, percent):
    h, d = slide('host', int(task == 's2')), slide('donor', grade)
    count = int(np.ceil(percent*20/100))
    indices = np.arange(count)
    old = inject_development_s1(h, d, indices, percent, 20261020) if task == 's1' else old_s2(h, d, indices, percent, 20261020, condition)
    new = legacy_s1(h, d, indices, percent, 20261020) if task == 's1' else legacy_s2(h, d, indices, percent, 20261020, condition)
    same(old, new)
    same(h, verify_oracle(h, new, text()), dtype=False)
    assert binary_predictions(old, text()) == binary_predictions(new, text())
    assert grade_predictions(old, text()) == grade_predictions(new, text())


def test_contracts_are_explicit_and_slide_snapshot_cannot_alias_original():
    task = PredictionTask('s1', ('benign', 'cancer'), 'frozen-sha', 'mean')
    with pytest.raises(FrozenInstanceError): task.pooling = 'top1pct'
    h = slide('h', 0)
    artifact = SlideArtifact.from_slide(h)
    output = artifact.materialize()
    output.feats[:] = 0
    output.metadata['patient_id'] = 'modified'
    assert artifact.materialize().metadata['patient_id'] == 'unknown'
    assert np.linalg.norm(artifact.materialize().feats[0]) == 1
    with pytest.raises(ValueError, match='snapshot'): replace(artifact, identity='wrong').materialize()
    with pytest.raises(ValueError): DonorSelection('cancer', seeds=(1, 1))
    with pytest.raises(ValueError): DetectionResult(('x',), (.1,), (), (True,), ('why',))


def test_single_implementation_native_donor_components_match_both_legacy_conditions():
    d = slide('donor', 4, 5)
    d.coords[:, 0] = [0, 100, 300, 400, 600]
    rows = [dict(tile_id=f't{i}', gleason3_fraction=a, gleason4_fraction=b, gleason5_fraction=c)
            for i, (a, b, c) in enumerate([(.2, 0, 0), (0, .2, 0), (0, .1, .1), (0, .3, 0), (0, 0, .3)])]
    assert [p.tolist() for p in donor_components(d, rows, DonorSelection('cancer'))] == [p.tolist() for p in cancer_components(d, rows, .1)]
    for condition in ('high_gp45', 'high_gp4_only', 'high_gp5_positive', 'same_grade_gp3_only'):
        assert [p.tolist() for p in donor_components(d, rows, DonorSelection(condition))] == [p.tolist() for p in pattern_components(d, rows, condition)]
    rows[0]['tile_id'] = 'wrong'
    with pytest.raises(ValueError, match='align'): donor_components(d, rows, DonorSelection('cancer'))


def test_intervention_rejects_connectivity_repeat_split_source_and_scale_failures():
    h, d = slide('h', 0), slide('d', 4)
    spec = InterventionSpec('s1', 'cancer', 'append_legacy', 10, 1, (0, 2))
    with pytest.raises(ValueError, match='four-connected'): apply_intervention(h, d, spec)
    with pytest.raises(ValueError, match='Unique'): apply_intervention(h, d, replace(spec, donor_indices=(0, 0)))
    d.metadata['tile_size'] = [50, 50]
    with pytest.raises(ValueError, match='geometry'): apply_intervention(h, d, spec)
    d.metadata['tile_size'] = [100, 100]
    d.metadata['model'] = dict(MODEL, revision='different')
    with pytest.raises(ValueError, match='mismatch'): apply_intervention(h, d, spec)
    d.metadata['model'] = MODEL
    d.metadata['cohort_split'] = 'test'
    with pytest.raises(ValueError, match='development'): apply_intervention(h, d, spec)


def occupancy():
    # Actual observed foreground at row 20..29, with bounded slide coordinates.
    mask = np.zeros((100, 250), bool)
    mask[20:30, :200] = True
    return VerifiedOccupancy.from_mask(mask, (10., 10.), 'a'*64, 'fixture observed RGB foreground')


def test_near_tissue_requires_observed_empty_geometry_and_proves_bag_invariance():
    h, d = slide('h', 0), slide('d', 4)
    h.coords[:, 1] = 200
    spec = InterventionSpec('s1', 'cancer', 'near_tissue', 10, 1, (0, 1), (100., 400.))
    with pytest.raises(ValueError, match='occupancy'): apply_intervention(h, d, spec)
    near = apply_intervention(h, d, spec, occupancy=occupancy())
    far = apply_intervention(h, d, replace(spec, mode='append_legacy'))
    assert not np.array_equal(near.slide.coords, far.slide.coords)
    assert np.array_equal(near.slide.feats, far.slide.feats)
    assert binary_predictions(near.slide, text()) == binary_predictions(far.slide, text())
    assert grade_predictions(near.slide, text()) == grade_predictions(far.slide, text())
    same(h, near.verify(lambda s: binary_predictions(s, text())))
    with pytest.raises(ValueError, match='overlaps'): apply_intervention(h, d, replace(spec, placement_anchor_um=(100., 200.)), occupancy=occupancy())
    with pytest.raises(ValueError, match='bounds'): apply_intervention(h, d, replace(spec, placement_anchor_um=(2500., 400.)), occupancy=occupancy())
    with pytest.raises(ValueError, match='align'): apply_intervention(h, d, replace(spec, placement_anchor_um=(101., 400.)), occupancy=occupancy())
    a = placement_anchor(h, d, np.array([0, 1]), occupancy(), 2)
    assert np.array_equal(a, placement_anchor(h, d, np.array([0, 1]), occupancy(), 2))


def test_replacement_preserves_original_positions_ids_and_exact_oracle_not_removal():
    h, d = slide('h', 0), slide('d', 4)
    d.feats = np.roll(d.feats, 7, axis=1)
    spec = InterventionSpec('s1', 'cancer', 'replacement', 10, 1, (0, 1), replacement_indices=(3, 4))
    result = apply_intervention(h, d, spec)
    assert len(result.slide.feats) == 20 and result.slide.foreign_mask.sum() == 2
    assert np.array_equal(result.slide.feats[[3, 4]], d.feats[:2])
    assert np.array_equal(result.slide.tile_ids, h.tile_ids) and np.array_equal(result.slide.coords, h.coords)
    same(h, result.verify(lambda s: binary_predictions(s, text())))
    result.slide.coords[0] += 1
    with pytest.raises(RuntimeError, match='changed'): result.restore()
    with pytest.raises(ValueError, match='four-connected'): apply_intervention(h, d, replace(spec, replacement_indices=(3, 5)))


def test_context_mode_and_same_source_sham_are_explicit_representation_controls():
    h = slide('h', 0)
    h.coords[:, 1] = 200
    spec = InterventionSpec('s1', 'same_source_sham', 'within_region_context', 10, 1, (0, 1), (100., 400.), context='observed sparse edge')
    result = apply_intervention(h, h, spec, occupancy=occupancy())
    assert result.slide.metadata['injection']['synthetic_foreign_tissue'] is False
    assert not result.slide.foreign_mask.any()
    assert json.loads(result.audit_json)['altered_count'] == 2
    assert json.loads(result.audit_json)['actual_foreign_count'] == 0
    assert result.slide.metadata['injection']['pixel_composition'] is False
    same(h, result.verify())
    with pytest.raises(ValueError, match='context'): replace(spec, context=None)


def test_deterministic_multiple_donors_capacity_and_unknown_patient_disclosure():
    h, sources = slide('h', 0), {}
    for name in ('d1', 'd2', 'd3'):
        d = slide(name, 4)
        rows = [dict(tile_id=t, gleason3_fraction=0, gleason4_fraction=.2, gleason5_fraction=0) for t in d.tile_ids]
        sources[name] = dict(slide=d, rows=rows)
    selection = DonorSelection('cancer', donors_per_host=2)
    a = select_donors(h, sources, selection, 's1', 10, 20261020)
    assert a == select_donors(h, sources, selection, 's1', 10, 20261020)
    assert len(a) == 2 and len({r['donor_id'] for r in a}) == 2 and all(r['full_capacity'] for r in a)


def test_same_source_replacement_is_a_zero_edit_negative_control():
    h = slide('native-control', 0)
    result = apply_intervention(h, h, InterventionSpec('s1', 'same_source_sham', 'replacement', 10, 0,
        (0, 1), replacement_indices=(0, 1)))
    assert not result.slide.foreign_mask.any()
    assert np.array_equal(result.slide.feats, h.feats)
    assert binary_predictions(result.slide, text()) == binary_predictions(h, text())
    assert result.slide.metadata['injection']['foreign_count'] == 0
    assert result.slide.metadata['injection']['altered_count'] == 2


def test_maximal_fragment_near_boundary_does_not_prove_every_nested_prefix_is_near():
    from floater_finder.research.engine import _valid_position
    h = slide('wide-host', 0, 100); h.coords[:, 1] = 200
    mask = np.zeros((100, 1500), bool); mask[20:30, 990:1000] = True
    observed = VerifiedOccupancy.from_mask(mask, (10., 10.), 'a'*64, 'fixture sparse observed edge')
    fragment = np.c_[np.arange(10)*100.+9000, np.full(10, 400.)]
    assert _valid_position(fragment, h, observed)
    assert not _valid_position(fragment[:1], h, observed)


def test_near_placement_cell_ownership_ignores_actual_roundtrip_phantom_overlap():
    """Actual CSV geometry values; synthetic arrays/mask, never model evidence."""
    from floater_finder.research.engine import _valid_position
    step = 111.82315650205668
    h = slide('numeric-host-fixture', 0, 2)
    h.metadata['tile_step'] = h.metadata['tile_size'] = [step, step]
    h.coords[:] = [[894.5852520164534, 4696.5725730863805],
                   [894.5852520164534, 4808.395729588437]]
    exact = np.array([[1006.4084085185101, 4696.5725730863805]])
    roundtrip = exact.copy(); roundtrip[0, 0] = 4249.279947078154+(exact[0, 0]-4249.279947078154)
    assert roundtrip[0, 0] == 1006.40840851851
    assert np.all((h.coords[0] < roundtrip[0]+step) & (h.coords[0]+step > roundtrip[0]))
    mask = np.zeros((800, 300), bool)
    mask[603, 128] = True  # Nearby native tissue, outside the inserted footprint.
    observed = VerifiedOccupancy.from_mask(mask, (7.779002191447421,)*2, 'a'*64, 'numeric fixture')
    original = roundtrip.copy()
    assert _valid_position(exact, h, observed)
    assert _valid_position(roundtrip, h, observed)
    assert np.array_equal(roundtrip, original)  # Validate ownership without snapping stored coordinates.


def test_near_placement_rejects_owned_cells_off_grid_and_invalid_footprints():
    from floater_finder.research.engine import _valid_position
    h = slide('geometry-host-fixture', 0, 2)
    h.coords[:] = [[0., 200.], [100., 200.]]
    mask = np.zeros((100, 100), bool); mask[20:30, :20] = True
    observed = VerifiedOccupancy.from_mask(mask, (10., 10.), 'a'*64, 'cell ownership fixture')
    assert _valid_position(np.array([[200., 200.]]), h, observed)  # Touching edges are not overlap.
    assert not _valid_position(np.array([[100., 200.]]), h, observed)  # An occupied cell is rejected.
    with pytest.raises(ValueError, match='align'):
        _valid_position(np.array([[199., 200.]]), h, observed)  # Do not quantize an actual off-grid overlap.
    with pytest.raises(ValueError, match='Duplicate'):
        _valid_position(np.array([[200., 200.], [200., 200.]]), h, observed)
    h.metadata['tile_size'] = [101., 100.]
    with pytest.raises(ValueError, match='no larger'):
        _valid_position(np.array([[200., 200.]]), h, observed)
    h.metadata['tile_size'] = [100., 100.]; h.coords[1, 0] = 99.
    with pytest.raises(ValueError, match='aligned'):
        _valid_position(np.array([[200., 200.]]), h, observed)
