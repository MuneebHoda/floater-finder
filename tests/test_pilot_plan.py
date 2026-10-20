import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("plan", Path(__file__).resolve().parents[1] / "scripts/prepare_pilot_plan.py")
plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan)


def test_pilot_selection_separates_patients_and_source_prefixes_without_outcomes():
    hits = []
    for organ, project in enumerate(plan.PROJECTS):
        for index in range(8):
            patient = f"TCGA-{organ}{index}-P001"
            hits.append({"file_name": patient + "-01Z-00-DX1.uuid.svs", "file_size": 123,
                "md5sum": "a" * 32, "access": "open", "experimental_strategy": "Diagnostic Slide",
                "cases": [{"submitter_id": patient, "project": {"project_id": project}}]})
    selected = plan.select_candidates(hits)
    assert len(selected) == 16
    assert len({item["patient_id"] for item in selected}) == 16
    assert len({item["source_site"] for item in selected}) == 16
    assert selected == plan.select_candidates(hits[::-1])
    assert sum(item["split"] == "eval" for item in selected) == 8
    with pytest.raises(ValueError, match="Not enough"):
        plan.select_candidates(hits[:3])
