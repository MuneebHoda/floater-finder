from copy import deepcopy
import math

import numpy as np
import pytest

from floater_finder.artifacts import Slide, TextEmbeddings, normalize
from floater_finder.injection import connected_fragment, grid_neighbors, inject, oracle_remove, verify_oracle
from floater_finder.scoring import POOLING, ensemble_prompts, pool, predictions, tile_scores
from conftest import make_slide


def test_artifact_roundtrip_without_pickle(tmp_path, host, text):
    host.save(tmp_path / "slide.npz")
    text.save(tmp_path / "text.npz")
    restored = Slide.load(tmp_path / "slide.npz")
    np.testing.assert_array_equal(host.feats, restored.feats)
    assert restored.metadata == host.metadata
    assert text.fingerprint() == TextEmbeddings.load(tmp_path / "text.npz").fingerprint()


@pytest.mark.parametrize("fault", ["nan", "norm", "projection", "coords", "ids", "zero", "real_hash"])
def test_artifact_rejects_bad_contracts(host, fault):
    feats, coords, ids, metadata = host.feats.copy(), host.coords.copy(), host.tile_ids.copy(), deepcopy(host.metadata)
    if fault == "nan": feats[0, 0] = np.nan
    if fault == "norm": feats *= 2
    if fault == "projection": metadata["model"]["projection"] = False
    if fault == "coords": coords = coords[:-1]
    if fault == "ids": ids[0] = ids[1]
    if fault == "zero": feats[0] = 0
    if fault == "real_hash": metadata["source_kind"] = "real"
    with pytest.raises(ValueError):
        Slide(feats, coords, ids, metadata)


def test_embedding_compatibility_checks_revision_and_dim(host, text):
    text.model["revision"] = "other"
    with pytest.raises(ValueError, match="mismatch"):
        tile_scores(host, text)
    with pytest.raises(ValueError):
        normalize(np.zeros((1, 2)))


def test_pooling_hand_calculated_and_independent_classes():
    scores = np.array([[1., 0.], [0., 1.], [.5, .25]])
    np.testing.assert_allclose(pool(scores, "mean"), [.5, 1.25 / 3])
    for rule in ("top1pct", "top5pct"):
        np.testing.assert_allclose(pool(scores, rule), [1, 1])


@pytest.mark.parametrize("rule,fraction", [("top1pct", .01), ("top5pct", .05)])
def test_k_recomputed_after_tile_count_changes(rule, fraction):
    scores = np.column_stack([np.arange(100), np.arange(100)[::-1]]).astype(float)
    for values in (scores, np.vstack([scores, [1000, 1000]])):
        k = math.ceil(len(values) * fraction)
        np.testing.assert_allclose(pool(values, rule), np.sort(values, axis=0)[-k:].mean(axis=0))


def test_class_tie_uses_fixed_class_order(text):
    slide = make_slide(feats=[[1, 1]])
    assert all(value["prediction"] == "prostate" for value in predictions(slide, text).values())


def test_prompt_ensemble_normalizes_before_and_after_average():
    prompts = {"a": ["a1", "a2", "a3"], "b": ["b1", "b2", "b3"]}
    vectors = np.array([[10., 0], [1, 0], [0, 1], [0, 2], [0, 1], [0, 1]])
    np.testing.assert_allclose(ensemble_prompts(vectors, prompts), normalize(np.array([[2., 1], [0, 3]])))


@pytest.mark.parametrize("percent", [0, .5, 1, 2, 5, 10])
def test_determinism_realized_fraction_identity_and_oracle(host, donor, text, percent):
    before = host.feats.copy()
    first, second = inject(host, donor, percent, 12), inject(host, donor, percent, 12)
    expected = math.ceil(percent * len(host.feats) / 100)
    assert first.foreign_mask.sum() == expected
    np.testing.assert_array_equal(first.feats, second.feats)
    np.testing.assert_array_equal(first.coords, second.coords)
    np.testing.assert_array_equal(first.tile_ids, second.tile_ids)
    np.testing.assert_array_equal(host.feats, before)
    verify_oracle(host, first, text)
    assert oracle_remove(first).metadata == host.metadata
    assert first.metadata["injection"]["seed"] == 12
    assert first.metadata["injection"]["requested_percent"] == percent
    if expected:
        assert first.metadata["injection"]["realized_percent"] == 100 * expected / len(host.feats)
        assert first.coords[len(host.feats):, 0].min() > host.coords[:, 0].max()


def test_same_patient_rejected(host, donor):
    donor.metadata["patient_id"] = host.metadata["patient_id"]
    with pytest.raises(ValueError, match="different patients"):
        inject(host, donor, 1, 0)


def test_connected_fragment_is_connected(donor):
    indices = connected_fragment(donor, 20, 7)
    graph = grid_neighbors(donor)
    reached = {int(indices[0])}
    while True:
        expanded = reached | {other for node in reached for other in graph[node] if other in indices}
        if expanded == reached:
            break
        reached = expanded
    assert reached == set(indices)


def test_impossible_disconnected_fragment_rejected():
    slide = make_slide(n=4, coords=np.array([[0, 0], [1, 0], [10, 0], [11, 0]]))
    with pytest.raises(ValueError, match="component"):
        connected_fragment(slide, 3, 0)


@pytest.mark.parametrize("fault", ["missing_step", "off_grid", "units", "split", "capacity"])
def test_invalid_spatial_requests_rejected(host, donor, fault):
    if fault == "missing_step":
        host.metadata.pop("tile_step")
        donor.metadata.pop("tile_step")
    if fault == "off_grid": donor.coords[1, 0] += .25
    if fault == "units": donor.metadata["coordinate_units"] = "pixels"
    if fault == "split": donor.metadata["split"] = "dev"
    if fault == "capacity": donor = make_slide("tiny", n=1, organ="bladder")
    with pytest.raises(ValueError):
        inject(host, donor, 10, 0)


def test_corrupted_oracle_is_a_pipeline_failure(host, donor, text):
    mixed = inject(host, donor, 1, 0)
    mixed.foreign_mask[0] = True
    with pytest.raises(RuntimeError, match="Oracle"):
        verify_oracle(host, mixed, text)
