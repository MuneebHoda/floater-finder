import csv
import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from floater_finder.conch import ConchEncoder, check_interface, verify_encoder_weights
from floater_finder.experiments import run_stress, summarize
from floater_finder.inventory import barcode, inventory, select_pairs
from conftest import make_slide


def csv_file(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_tcga_barcode_and_missing_metadata(tmp_path):
    name = "TCGA-AB-1234-01Z-00-DX1"
    (tmp_path / f"{name}.svs").touch()
    records, report = inventory([tmp_path])
    assert barcode(name) == ("TCGA-AB-1234", "AB")
    assert records[0]["diagnostic_slide"] is True
    assert records[0]["diagnostic_verified"] is False
    assert records[0]["project"] is None
    assert records[0]["institution_id"] is None
    assert "project" in report["missing_by_slide"][0]["missing"]
    assert records[0]["report_available"] is False


def test_inventory_leakage_and_verified_institution_map(tmp_path):
    rows = [{"slide_id": "TCGA-AB-1234-01Z-00-DX1", "split": "dev"},
            {"slide_id": "TCGA-AB-1234-01Z-00-DX2", "split": "eval"}]
    manifest = tmp_path / "manifest.csv"
    csv_file(manifest, rows)
    with pytest.raises(ValueError, match="leakage"):
        inventory(manifest=manifest)
    rows[1]["split"] = "dev"
    csv_file(manifest, rows)
    mapping = tmp_path / "mapping.csv"
    csv_file(mapping, [{"tissue_source_site": "AB", "institution_id": "verified-A", "institution": "Institution A", "provenance": "curated test mapping"}])
    records, _ = inventory(manifest=manifest, institution_map=mapping)
    assert records[0]["institution_id"] == "verified-A"


def test_pairing_prefers_verified_institution_not_raw_site():
    host = dict(slide_id="host", patient_id="h", split="eval", diagnostic_slide=True, diagnostic_verified=True, organ="prostate", tissue_source_site="AA")
    raw = dict(slide_id="raw", patient_id="d1", split="eval", diagnostic_slide=True, diagnostic_verified=True, organ="bladder", tissue_source_site="AA")
    verified = dict(slide_id="verified", patient_id="d2", split="eval", diagnostic_slide=True, diagnostic_verified=True, organ="bladder", institution_id="I", institution_provenance="mapping")
    host.update(institution_id="I", institution_provenance="mapping")
    pairs = select_pairs([host, raw, verified], "prostate", "bladder", "eval")
    assert pairs[0]["donor"] == "verified"
    assert pairs[0]["verified_institution_match"]


def test_discovery_is_bounded_and_does_not_follow_symlinks(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "x.svs").touch()
    root = tmp_path / "root"
    root.mkdir()
    (root / "link").symlink_to(outside)
    assert inventory([root])[0] == []
    for index in range(3): (root / f"{index}.svs").touch()
    records, report = inventory([root], max_files=2)
    assert len(records) == 2 and report["discovery_truncated"]


def test_flip_denominator_excludes_original_errors_and_zero_is_undefined():
    rows = [dict(pooling="mean", requested_percent=1, seed=0, host_slide_id="a", original_correct=False, prediction_changed=True)]
    result = summarize(rows)[0]
    assert result["eligible_flip_rate"] is None
    assert result["eligible_slides"] == 0
    assert result["raw_prediction_change_rate"] == 1
    rows.append({**rows[0], "host_slide_id": "b", "original_correct": True, "prediction_changed": False})
    result = summarize(rows)[0]
    assert result["eligible_flip_rate"] == 0 and result["eligible_slides"] == 1


def test_stress_runner_end_to_end_and_provenance(tmp_path, host, donor, text):
    host.save(tmp_path / "host.npz")
    donor.save(tmp_path / "donor.npz")
    text.save(tmp_path / "text.npz")
    config = dict(category="fixture", split="eval", text_embeddings="text.npz", pairs=[dict(host="host.npz", donor="donor.npz")],
                  contamination_percent=[0, .5, 1, 2, 5, 10], seeds=[0, 1])
    path = tmp_path / "run.yaml"
    path.write_text(yaml.safe_dump(config))
    result = run_stress(path, tmp_path / "out")
    assert result["rows"] == 36 and result["failed_trials"] == 0
    summary = json.loads((tmp_path / "out/summary.json").read_text())
    assert all(row["eligible_slides"] == 1 for row in summary)
    assert json.loads((tmp_path / "out/experiment.json").read_text())["category"] == "fixture"
    config["category"] = "pilot"
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError, match="provenance"):
        run_stress(path, tmp_path / "not-real")


def test_runtime_image_projection_and_api_contract():
    class Model:
        def encode_image(self, value, proj_contrast=False, normalize=False):
            assert proj_contrast is True and normalize is True
            return value
        def encode_text(self, value, normalize=False):
            return value
    check_interface(Model())
    encoder = ConchEncoder.__new__(ConchEncoder)
    encoder.model = Model()
    assert encoder.encode_image_batch("batch") == "batch"
    with pytest.raises(ValueError):
        check_interface(object())


def test_no_conch_inference_outside_slurm(monkeypatch):
    monkeypatch.delenv("SLURM_JOB_ID", raising=False)
    with pytest.raises(RuntimeError, match="Slurm"):
        ConchEncoder("missing")


def test_partial_checkpoint_cannot_silently_produce_real_embeddings():
    model = {"visual.proj": np.zeros((2, 2)), "text.proj": np.zeros((2, 2)), "text_decoder.weight": np.zeros((2, 2))}
    complete = {key: value for key, value in model.items() if not key.startswith("text_decoder.")}
    verify_encoder_weights(model, complete)
    verify_encoder_weights(model, {"state_dict": {"module." + key: value for key, value in complete.items()}})
    with pytest.raises(ValueError, match="lacks"):
        verify_encoder_weights(model, {"visual.proj": np.zeros((2, 2))})
    with pytest.raises(ValueError, match="shapes"):
        verify_encoder_weights(model, {**complete, "text.proj": np.zeros((1, 2))})


def test_oracle_defect_stops_runner_instead_of_becoming_an_exclusion(tmp_path, host, donor, text, monkeypatch):
    import floater_finder.experiments as experiments
    host.save(tmp_path / "h.npz")
    donor.save(tmp_path / "d.npz")
    text.save(tmp_path / "t.npz")
    path = tmp_path / "run.yaml"
    path.write_text(yaml.safe_dump(dict(category="fixture", split="eval", text_embeddings="t.npz",
                                       pairs=[dict(host="h.npz", donor="d.npz")], contamination_percent=[0], seeds=[0])))
    def fail(*args):
        raise RuntimeError("Oracle pipeline defect")
    monkeypatch.setattr(experiments, "verify_oracle", fail)
    with pytest.raises(RuntimeError, match="Oracle"):
        run_stress(path, tmp_path / "out")
    assert not (tmp_path / "out/results.csv").exists()
