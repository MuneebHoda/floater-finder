from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest

from conftest import make_slide
from floater_finder.cohort import frozen_protocol, omitted_development_scores, select_development
from floater_finder.detection import calibrate
from floater_finder.injection import inject

DETECTOR = dict(exclusion_mm=1.0, smoothing_mm=0.1, weight=0.5, chunk_size=32)
POLICY = dict(quantiles=[0.9,0.99,0.995], clean_host_removal_budget_per_patient=0.01)


def patients():
    return [make_slide(f"dev-{i}", n=8, split="dev", organ="prostate" if i%2==0 else "bladder") for i in range(4)]


def test_lopo_excludes_omitted_patient_and_matches_full_calibration(text, tmp_path):
    slides = patients()
    output = tmp_path / "selection"
    report = select_development(slides, text, DETECTOR, POLICY, output)
    assert report["status"] == "passed" and report["selected_quantile"] == 0.9
    assert report["folds"] == 4 and report["selection_rows"] == 36
    for slide in slides:
        fold = output / "folds" / slide.metadata["patient_id"]
        calibration = json.loads((fold / "base_calibration.json").read_text())
        assert slide.metadata["patient_id"] not in calibration["development_patients"]
        assert len(calibration["development_patients"]) == 3
    final = json.loads((output / "final_calibration.json").read_text())
    assert final == calibrate(slides, text, quantile=0.9, **DETECTOR)
    assert report["source_kind"] == "fixture" and not report["evaluation_artifacts_loaded"]


def test_no_feasible_cutoff_stops_before_final_calibration(text, tmp_path):
    slides = patients()
    slides[0] = make_slide("dev-0", split="dev", feats=np.tile([0.0,1.0], (8,1)))
    report = select_development(slides, text, DETECTOR, POLICY, tmp_path / "selection")
    assert report["status"] == "no_feasible_cutoff" and report["selected_quantile"] is None
    assert report["feasible_quantiles"] == []
    assert not (tmp_path / "selection/final_calibration.json").exists()
    assert all(not row["within_budget"] for row in report["controls"] if row["omitted_patient"] == "patient-dev-0" and row["variant"] == "organ_only")


def test_omitted_scoring_rejects_calibration_overlap_evaluation_and_injection(text):
    slides = patients()
    calibration = calibrate(slides[:3], text)
    with pytest.raises(ValueError, match="omitted"):
        omitted_development_scores(slides[0], text, calibration)
    evaluation = deepcopy(slides[3]);evaluation.metadata["split"]="eval"
    with pytest.raises(ValueError, match="development"):
        omitted_development_scores(evaluation, text, calibration)
    with pytest.raises(ValueError, match="unmodified"):
        omitted_development_scores(inject(slides[3], slides[0], 10, 0), text, calibration)


def test_selection_rejects_evaluation_and_duplicate_patients_before_writing(text, tmp_path):
    slides = patients()
    slides[0].metadata["split"] = "eval"
    with pytest.raises(ValueError, match="development"):
        select_development(slides, text, DETECTOR, POLICY, tmp_path / "bad")
    with pytest.raises(ValueError, match="Distinct"):
        select_development([slides[1]]*3, text, DETECTOR, POLICY, tmp_path / "bad")
    assert not (tmp_path / "bad").exists()


def test_frozen_protocol_checks_hashes_without_modifying_design(tmp_path):
    project = Path(__file__).resolve().parents[1]
    config, freeze, preflight = frozen_protocol(project)
    assert len(config["slides"]) == 18 and preflight["status"] == "passed"
    (tmp_path / "reports").mkdir()
    (tmp_path / "configs").mkdir()
    (tmp_path / "reports/conch_pilot_protocol_freeze_20261019.json").write_text(json.dumps(freeze))
    (tmp_path / freeze["protocol"]).write_text("{}")
    with pytest.raises(ValueError, match="hash mismatch"):
        frozen_protocol(tmp_path)
