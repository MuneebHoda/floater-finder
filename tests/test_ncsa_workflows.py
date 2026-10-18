from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("one_pair", ROOT / "scripts/ncsa_one_pair_smoke.py")
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


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
