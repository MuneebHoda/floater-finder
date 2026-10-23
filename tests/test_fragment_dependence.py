import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from floater_finder.artifacts import Slide
from floater_finder.fragment_dependence import (
    analyze_fragment_dependence, analyze_saved_slide, connected_pieces,
)


POLICY = {"max_area_mm2": 2., "min_isolation_mm": .5}


def cancer_scorer(features, coords):
    score = float(features[:, 0].max())
    return {"prediction": "cancer" if score >= .5 else "benign", "score": score}


def analyze(values, coords, **kwargs):
    options = dict(tile_step=112, tile_size=112, coordinate_units="microns",
                   microns_per_unit=1, source_kind="fixture", scorer_id="artificial-max-v1",
                   alert_policy=POLICY)
    options.update(kwargs)
    return analyze_fragment_dependence(np.array(values, dtype=float).reshape(-1, 1), coords,
                                       cancer_scorer, **options)


def test_isolated_decision_changing_piece_and_full_scorer_reruns():
    calls = []
    def scorer(features, coords):
        calls.append((features.copy(), coords.copy()))
        return cancer_scorer(features, coords)
    features = np.array([[0.], [0.], [1.]])
    coords = np.array([[0, 0], [112, 0], [2240, 0]])
    report = analyze_fragment_dependence(features, coords, scorer, tile_step=112, tile_size=112,
        coordinate_units="microns", microns_per_unit=1, source_kind="fixture", scorer_id="max-fixture",
        tile_ids=["b0", "b1", "p0"], alert_policy=POLICY)
    assert [len(call[0]) for call in calls] == [3, 1, 2]
    assert report["baseline"]["prediction"] == "cancer"
    first, second = report["pieces"]
    assert first["counterfactual"]["result"]["prediction"] == "cancer"
    assert not first["decision_changing"] and not first["review_alert"]
    assert second["counterfactual"]["result"]["prediction"] == "benign"
    assert second["decision_changing"] and second["review_alert"]
    assert second["tile_ids"] == ["p0"] and second["tile_indices"] == [2]
    assert second["area_mm2"] == pytest.approx(.012544)
    assert second["isolation_mm"] == pytest.approx(2.016)
    assert len(report["alerts"]) == 1
    assert report["tissue_action"] == "preserve_all_tissue"
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize("offset", [[112, 0], [112, 112], [224, 0], [224, 224]])
def test_adjacent_diagonal_and_one_gap_tiles_merge(offset):
    assert [piece.tolist() for piece in connected_pieces([[0, 0], offset], 112)] == [[0, 1]]
    report = analyze([0, 1], [[0, 0], offset])
    assert report["piece_count"] == 1
    assert report["pieces"][0]["counterfactual"]["status"] == "not_evaluable_empty_slide"
    assert report["pieces"][0]["decision_changing"] is None
    assert report["pieces"][0]["review_alert"] is None
    assert report["alerts"] == []


def test_gap_policy_is_explicit_and_components_are_transitive():
    coords = [[0, 0], [224, 0], [448, 0], [784, 0]]
    assert [p.tolist() for p in connected_pieces(coords, 112)] == [[0, 1, 2], [3]]
    assert len(connected_pieces(coords, 112, max_gap_tiles=0)) == 4


def test_piece_ids_follow_geometry_after_input_permutation():
    coords = np.array([[0, 0], [112, 0], [1120, 0]])
    order = [2, 0, 1]
    pieces = connected_pieces(coords[order], 112)
    assert [p.tolist() for p in pieces] == [[1, 2], [0]]


def test_non_decisive_pieces_do_not_alert():
    report = analyze([1, 1], [[0, 0], [2240, 0]])
    assert report["baseline"]["prediction"] == "cancer"
    assert not any(piece["decision_changing"] for piece in report["pieces"])
    assert report["alerts"] == []


def test_genuine_small_positive_can_trigger_review_but_never_removal_or_foreign_claim():
    # This software fixture represents genuine small cancer; the algorithm gets no donor label.
    report = analyze([0, 0, 1], [[0, 0], [112, 0], [2240, 0]])
    assert report["pieces"][1]["decision_changing"]
    assert report["pieces"][1]["review_alert"]
    assert report["baseline"]["prediction"] == "cancer"
    assert report["tissue_action"] == "preserve_all_tissue"
    assert "foreign tissue is not established" in report["alerts"][0]["message"]
    assert report["alert_policy"]["validation"] == "uncalibrated_exploratory_only"


def test_decision_change_is_reported_without_an_alert_policy():
    report = analyze([0, 1], [[0, 0], [2240, 0]], alert_policy=None)
    assert report["pieces"][1]["decision_changing"]
    assert report["pieces"][1]["review_alert"] is None
    assert not report["alerts_evaluated"] and report["alerts"] == []


def test_physical_area_uses_occupied_footprints_not_bounding_box_or_model_resize():
    # Two diagonally touching 224px footprints at .5um/px, regardless of model input resize.
    report = analyze([0, 1], [[0, 0], [224, 224]], coordinate_units="level0_pixels",
                     tile_step=224, tile_size=224, microns_per_unit=.5)
    assert report["pieces"][0]["area_mm2"] == pytest.approx(2 * .012544)
    assert report["pieces"][0]["area_fraction"] == 1
    assert report["pieces"][0]["bbox_coordinate_units"] == [0, 0, 448, 448]
    anisotropic = analyze([0, 1], [[0, 0], [1000, 0]], coordinate_units="level0_pixels",
                          tile_step=[100, 200], tile_size=[80, 160], microns_per_unit=[.5, .25])
    assert anisotropic["pieces"][0]["area_mm2"] == pytest.approx(.0016)
    assert anisotropic["pieces"][0]["isolation_mm"] == pytest.approx(.46)


def test_empty_counterfactual_is_never_scored_or_called_benign():
    calls = []
    def scorer(features, coords):
        assert len(features) > 0
        calls.append(len(features))
        return {"prediction": "cancer"}
    report = analyze_fragment_dependence(np.ones((1, 2)), [[0, 0]], scorer,
        tile_step=1, tile_size=1, coordinate_units="grid", microns_per_unit=112,
        source_kind="fixture", scorer_id="singleton")
    assert calls == [1]
    piece = report["pieces"][0]
    assert piece["counterfactual"]["result"] is None
    assert piece["counterfactual"]["remaining_tile_count"] == 0
    assert piece["isolation_mm"] is None


def test_scorer_cannot_mutate_inputs_and_unnormalized_embeddings_are_supported():
    features, coords = np.array([[0., 0.], [10., 3.]]), np.array([[0., 0.], [2240., 0.]])
    before_features, before_coords = features.copy(), coords.copy()
    def scorer(values, positions):
        result = cancer_scorer(values, positions)
        values[:] = -1
        positions[:] = -1
        return result
    report = analyze_fragment_dependence(features, coords, scorer, tile_step=112, tile_size=112,
        coordinate_units="microns", microns_per_unit=1, source_kind="fixture", scorer_id="mutation-fixture")
    np.testing.assert_array_equal(features, before_features)
    np.testing.assert_array_equal(coords, before_coords)
    assert report["pieces"][1]["decision_changing"]


@pytest.mark.parametrize("coords,kwargs", [
    ([[0, 0], [0, 0]], {}), ([[0, 0], [111, 0]], {}),
    ([[0, 0], [np.nan, 0]], {}), ([[0, 0], [112, 0]], {"tile_size": 113}),
    ([[0, 0], [112, 0]], {"microns_per_unit": None}),
    ([[0, 0], [112, 0]], {"microns_per_unit": .5}),
    ([[0, 0], [112, 0]], {"max_gap_tiles": 2}),
    ([[0, 0], [112, 0]], {"tile_ids": ["same", "same"]}),
    ([[0, 0], [112, 0]], {"alert_policy": {"max_area_mm2": 2}}),
    ([[0, 0], [112, 0]], {"alert_policy": {"max_area_mm2": 2, "min_isolation_mm": np.nan}}),
])
def test_rejects_ambiguous_or_invalid_geometry_and_policy(coords, kwargs):
    with pytest.raises(ValueError):
        analyze([0, 1], coords, **kwargs)


@pytest.mark.parametrize("result", [{}, {"prediction": 1}, {"prediction": "cancer", "score": np.nan}])
def test_rejects_invalid_scorer_outputs(result):
    with pytest.raises(ValueError, match="Scorer"):
        analyze_fragment_dependence(np.ones((1, 2)), [[0, 0]], lambda *_: result,
            tile_step=112, tile_size=112, coordinate_units="microns", microns_per_unit=1,
            source_kind="fixture", scorer_id="invalid-fixture")


def test_demo_saved_artifact_example_and_no_overwrite(tmp_path):
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "demo"
    command = [sys.executable, str(root / "scripts/fragment_dependence_demo.py"), "--output", str(output)]
    run = subprocess.run(command, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    path = output / "alert.fixture.json"
    before = path.read_bytes()
    report = json.loads(before)
    assert (output / "slide.fixture.npz").is_file()
    assert report["source_kind"] == "fixture" and len(report["alerts"]) == 1
    assert report == json.loads((root / "examples/fragment_dependence/alert.fixture.json").read_text())
    assert subprocess.run(command, capture_output=True).returncode != 0
    assert path.read_bytes() == before


def save_piece_fixture(path, **metadata_changes):
    metadata = {
        "slide_id": "artificial-panda-biopsy", "patient_id": "unknown", "patient_id_known": False,
        "project": "FIXTURE", "organ": "prostate", "split": "dev", "source_kind": "fixture",
        "split_provenance": "engineering smoke only; no patient-separated evaluation",
        "data_provider": "artificial-radboud", "coordinate_units": "microns",
        "coordinate_reference": "tile_top_left", "tile_step": [112., 112.],
        "tile_size": [112., 112.], "microns_per_unit": 1.,
        "model": {"name": "artificial-one-hot", "revision": "fixture-v1",
                  "checkpoint_sha256": "no-checkpoint-fixture-only", "projection": True,
                  "normalized": True, "preprocessing": "Artificial arrays; no image inference"},
        # These deliberately disagree with the artificial scorer: they are not model inputs.
        "isup_grade": 0, "tile_label_fractions": [{"benign": 1.}, {"benign": 1.}],
    }
    metadata.update(metadata_changes)
    slide = Slide(np.array([[0., 1.], [1., 0.]]), np.array([[0., 0.], [2240., 0.]]),
                  np.array(["fixture-benign", "fixture-positive"]), metadata,
                  foreign_mask=np.array([True, False]))
    slide.save(path)
    return slide


def test_saved_slide_handoff_preserves_provenance_and_ignores_labels(tmp_path):
    path = tmp_path / "slide.fixture.npz"
    slide = save_piece_fixture(path)
    report = analyze_saved_slide(path, cancer_scorer, scorer_id="artificial-max-v1",
                                 alert_policy=POLICY)
    assert report["source_kind"] == "fixture"
    assert report["baseline"]["prediction"] == "cancer"
    assert report["pieces"][1]["decision_changing"]
    assert report["pieces"][1]["tile_ids"] == ["fixture-positive"]
    assert report["pieces"][1]["area_mm2"] == pytest.approx(.012544)
    assert report["geometry"]["microns_per_unit_xy"] == [1., 1.]
    provenance = report["slide_provenance"]
    assert provenance["slide_id"] == slide.metadata["slide_id"]
    assert provenance["model"] == slide.metadata["model"]
    assert provenance["patient_id"] == "unknown" and provenance["patient_id_known"] is False
    assert provenance["split_provenance"] == slide.metadata["split_provenance"]
    assert "isup_grade" not in provenance and "tile_label_fractions" not in provenance
    json.dumps(report, allow_nan=False)


def test_saved_slide_uses_recorded_physical_pixel_scale_and_preserves_file(tmp_path):
    path = tmp_path / "slide.fixture.npz"
    save_piece_fixture(path, coordinate_units="level0_pixels", tile_step=[224., 224.],
                       tile_size=[224., 224.], microns_per_unit=.486)
    before = path.read_bytes()
    calls = []
    def scorer(features, positions):
        calls.append(positions.copy())
        result = cancer_scorer(features, positions)
        features[:] = -1
        positions[:] = -1
        return result
    report = analyze_saved_slide(path, scorer, scorer_id="artificial-mutation-fixture")
    assert report["pieces"][0]["area_mm2"] == pytest.approx((224 * .486) ** 2 / 1e6)
    assert report["pieces"][0]["isolation_mm"] == pytest.approx((2240 - 224) * .486 / 1000)
    assert [len(positions) for positions in calls] == [2, 1, 1]
    np.testing.assert_array_equal(calls[0], [[0., 0.], [2240., 0.]])
    assert path.read_bytes() == before


@pytest.mark.parametrize("key", ["tile_step", "tile_size", "microns_per_unit"])
def test_saved_slide_rejects_missing_geometry_without_calling_scorer(tmp_path, key):
    path = tmp_path / "slide.fixture.npz"
    save_piece_fixture(path, **{key: None})
    def scorer(*_):
        pytest.fail("Ambiguous physical geometry must fail before scoring")
    with pytest.raises(ValueError, match=f"explicit physical geometry: {key}"):
        analyze_saved_slide(path, scorer, scorer_id="unused-fixture")
