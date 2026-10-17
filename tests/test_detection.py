import numpy as np
import pytest

from floater_finder.detection import auroc, calibrate, evaluate, organ_mismatch, visual_inconsistency
from floater_finder.injection import inject
from conftest import make_slide


def test_visual_signal_excludes_compact_foreign_neighbors():
    slide = make_slide(feats=[[1, 0], [1, 0], [0, 1], [0, 1]],
                       coords=np.array([[0, 0], [10, 0], [.1, 0], [.2, 0]]))
    result = visual_inconsistency(slide, exclusion_mm=1, chunk_size=2)
    np.testing.assert_allclose(result, [0, 0, 1, 1])
    np.testing.assert_allclose(result, visual_inconsistency(slide, exclusion_mm=1, chunk_size=1))


def test_physical_scale_and_distant_reference_required():
    slide = make_slide(n=2)
    slide.metadata.pop("microns_per_unit")
    with pytest.raises(ValueError, match="scale"):
        visual_inconsistency(slide)
    slide.metadata["microns_per_unit"] = 1
    with pytest.raises(ValueError, match="undefined"):
        visual_inconsistency(slide)


def test_organ_signal_does_not_use_diagnostic_label(text):
    slide = make_slide(feats=[[1, 0], [0, 1]])
    first = organ_mismatch(slide, text)
    slide.metadata["label"] = "secret-subtype-never-used"
    np.testing.assert_array_equal(first, organ_mismatch(slide, text))
    np.testing.assert_array_equal(first, [-1, 1])


def test_auroc_ties_undefined_and_known_values():
    assert auroc([False, True], [.5, .5]) == .5
    assert auroc([False, False, True, True], [0, 1, 2, 3]) == 1
    assert auroc([False, True], [1, 0]) == 0
    assert auroc([False, False], [0, 1]) is None


def test_calibration_cannot_use_eval_or_injected_slides(text):
    with pytest.raises(ValueError, match="development"):
        calibrate([make_slide()], text)
    dev = make_slide("dev", split="dev")
    donor = make_slide("dev-donor", split="dev", organ="bladder")
    with pytest.raises(ValueError, match="unmodified"):
        calibrate([inject(dev, donor, 5, 1)], text)


def test_no_patient_leakage_including_donor(text):
    dev = make_slide("dev", split="dev")
    calibration = calibrate([dev], text)
    reused = make_slide("dev")
    with pytest.raises(ValueError, match="independent"):
        evaluate(reused, text, calibration)
    mixed = inject(make_slide("eval"), make_slide("dev", organ="bladder"), 5, 0)
    with pytest.raises(ValueError, match="independent"):
        evaluate(mixed, text, calibration)


def test_clean_control_no_damage_and_all_baselines_present(text):
    calibration = calibrate([make_slide("dev", split="dev")], text)
    result, _, flags = evaluate(make_slide("clean-eval"), text, calibration)
    assert result["oracle"] == result["no_filter"]
    for name, values in flags.items():
        assert not values.any()
        metrics = result["variants"][name]
        assert metrics["auroc"] is None
        assert metrics["measured_false_alarm_rate"] == 0
        assert all(value is False for value in metrics["clean_prediction_changed"].values())
        assert metrics["random_same_count"] == result["no_filter"]


def test_detection_and_oracle_on_fixture_have_honest_provenance(text):
    calibration = calibrate([make_slide("dev", split="dev")], text)
    mixed = inject(make_slide("eval"), make_slide("donor", organ="bladder"), 2, 4)
    result, scores, flags = evaluate(mixed, text, calibration)
    assert result["source_kind"] == "fixture"
    assert set(result["variants"]) == {"organ_only", "visual_only", "combined"}
    assert result["variants"]["organ_only"]["fragment_hit"]
    assert result["variants"]["organ_only"]["genuine_host_tiles_removed"] == 0
    assert len(scores["combined"]) == len(mixed.feats)
    assert flags["combined"].dtype == bool


def test_calibration_prompt_change_rejected(text):
    calibration = calibrate([make_slide("dev", split="dev")], text)
    text.prompts["prostate"] = ["changed after calibration"]
    with pytest.raises(ValueError, match="provenance"):
        evaluate(make_slide(), text, calibration)
