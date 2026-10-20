from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import os
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("one_pair", ROOT / "scripts/ncsa_one_pair_smoke.py")
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)
spec = importlib.util.spec_from_file_location("threshold", ROOT / "scripts/ncsa_threshold_diagnostic.py")
threshold = importlib.util.module_from_spec(spec)
spec.loader.exec_module(threshold)
spec = importlib.util.spec_from_file_location("runtime_check", ROOT / "scripts/ncsa_runtime_compatibility.py")
runtime_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime_check)
spec = importlib.util.spec_from_file_location("pilot_preflight", ROOT / "scripts/ncsa_pilot_preflight.py")
pilot_preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot_preflight)


def test_frozen_ncsa_patient_splits_and_encoding_modes():
    evaluation = json.loads((ROOT / "configs/ncsa_one_pair.json").read_text())
    development = json.loads((ROOT / "configs/ncsa_calibration.json").read_text())
    workflow.validate_pair_config(evaluation)
    workflow.validate_pair_config(development)
    assert {s["patient_id"] for s in evaluation["slides"]}.isdisjoint(s["patient_id"] for s in development["slides"])
    wrong = deepcopy(evaluation)
    wrong["mode"] = "calibration"
    with pytest.raises(ValueError, match="split"):
        workflow.validate_pair_config(wrong)
    wrong = deepcopy(development)
    wrong["slides"][1]["patient_id"] = wrong["slides"][0]["patient_id"]
    with pytest.raises(ValueError, match="distinct"):
        workflow.validate_pair_config(wrong)


def test_threshold_diagnostic_uses_only_development_and_records_counts(text, tmp_path):
    import csv
    from conftest import make_slide
    from floater_finder.detection import calibrate
    slides = [make_slide("dev", split="dev"), make_slide("dev-donor", split="dev", organ="bladder")]
    settings = json.loads((ROOT / "configs/ncsa_threshold_diagnostic.json").read_text())
    settings.update(development_patients=[s.metadata["patient_id"] for s in slides],
        quantiles=[0.9, 0.99], contamination_percent=[0, 10], seeds=[0])
    report = threshold.run(slides, text, settings, tmp_path / "diagnostic")
    assert report["oracle_verified_trials"] == 4
    assert report["metric_rows"] == 24
    assert report["calibrations"][1] == calibrate(slides, text)
    with (tmp_path / "diagnostic/metrics.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    assert all(int(row["host_tiles"]) == 100 for row in rows)
    assert all(int(row["foreign_tiles"]) == (0 if row["requested_percent"] == "0" else 10) for row in rows)
    assert all(row["auroc"] == "" for row in rows if row["requested_percent"] == "0")
    assert all(row["independent_patients"] == 2 and row["trials"] == 2 for row in report["ten_percent_summary"])
    wrong = deepcopy(settings)
    wrong["excluded_evaluation_patients"] = settings["development_patients"]
    with pytest.raises(ValueError, match="exclude evaluation"):
        threshold.run(slides, text, wrong, tmp_path / "rejected")
    assert not (tmp_path / "rejected").exists()


def test_threshold_diagnostic_refuses_login_node(tmp_path):
    environment = os.environ.copy()
    environment.pop("SLURM_JOB_ID", None)
    result = subprocess.run([sys.executable, str(ROOT / "scripts/ncsa_threshold_diagnostic.py"),
        "--development", "unused", "--config", "unused", "--output", str(tmp_path / "unused")],
        env=environment, capture_output=True, text=True)
    assert result.returncode != 0
    assert "inside Slurm" in result.stderr
    assert not (tmp_path / "unused").exists()


def test_runtime_comparison_reports_changes_without_hiding_them():
    import numpy as np
    before = np.array([[0.0, 1.0]])
    assert runtime_check.compare_arrays(before, before)["exactly_equal"]
    changed = runtime_check.compare_arrays(before, before + 0.01)
    assert not changed["exactly_equal"] and not changed["close_at_1e_5"]
    assert changed["maximum_absolute_difference"] > 0.009
    with pytest.raises(ValueError, match="shapes"):
        runtime_check.compare_arrays(before, before.T)


def test_pilot_integrity_gate_rejects_corruption_and_symlinks_without_changing_inputs(tmp_path):
    import hashlib
    path = tmp_path / "slide.svs"
    path.write_bytes(b"artificial software fixture")
    item = dict(path=str(path), bytes=path.stat().st_size,
                checksum=dict(algorithm="md5", value=hashlib.md5(path.read_bytes()).hexdigest()))
    pilot_preflight.verify_input(item)
    path.write_bytes(b"different fixture contents")
    with pytest.raises(ValueError, match="checksum"):
        pilot_preflight.verify_input({**item, "bytes":path.stat().st_size})
    link = tmp_path / "link.svs"
    link.symlink_to(path)
    with pytest.raises(ValueError, match="identity/type/size"):
        pilot_preflight.verify_input({**item, "path":str(link)})
    assert path.read_bytes() == b"different fixture contents"


def test_expanded_protocol_patient_separation_and_unique_control_denominators():
    protocol = json.loads((ROOT / "configs/ncsa_expanded_pilot_protocol.json").read_text())
    dev = {s["patient_id"] for s in protocol["slides"] if s["split"] == "dev"}
    held_out = {s["patient_id"] for s in protocol["slides"] if s["split"] == "eval"}
    assert len(dev) == 10 and len(held_out) == 8 and dev.isdisjoint(held_out)
    assert set(protocol["pixel_qc_patients"]) <= dev
    assert set(protocol["evaluation"]["retired_evaluation_patients"]).isdisjoint(dev | held_out)
    evaluation = protocol["evaluation"]
    trials = evaluation["directed_pairs"] * (len(evaluation["contamination_percent"]) - 1) * len(evaluation["seeds"])
    assert trials == evaluation["nonzero_trials"] == 800
    assert trials + len(held_out) == evaluation["total_trials"] == 808
