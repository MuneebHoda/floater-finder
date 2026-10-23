"""Configuration regression checks; no real images, model or scientific result."""
import json
from pathlib import Path

import pytest

from floater_finder.research import pixel_program as pp


PROJECT = Path(__file__).resolve().parents[1]
CONFIG = PROJECT / "configs/panda_gpu_program_v2/protocol.json"


def test_v2_corrects_only_verified_reuse_paths_and_preserves_science():
    current, rows = pp.load_config(PROJECT, CONFIG, pp.file_sha256(CONFIG))
    original_path = PROJECT / "configs/panda_gpu_program_v1/protocol.json"
    original = json.loads(original_path.read_text())
    previous = pp.csv_rows(PROJECT / original["sources_csv"])
    correction = current["source_path_correction"]
    assert pp.file_sha256(original_path) == correction["previous_config_sha256"]
    provenance = PROJECT / correction["reuse_provenance_path"]
    assert pp.file_sha256(provenance) == correction["reuse_provenance_sha256"]
    reused = {r["image_id"]: r["input_directory"]
              for r in json.loads(provenance.read_text())["records"] if r["reused_profile"]}
    assert len(reused) == 3 and sorted(reused) == correction["reused_image_ids"]
    for old, new in zip(previous, rows, strict=True):
        expected = old.copy()
        if old["image_id"] in reused:
            directory = Path(reused[old["image_id"]])
            expected.update(tile_manifest_path=str(directory / "tiles.csv"),
                            tile_metadata_path=str(directory / "metadata.json"))
        assert new == expected
    assert pp.make_pairs(rows) == current["pairs"] == original["pairs"]
    for key in ("selection_seed", "excluded_pilot_ids", "cohort_manifest", "target_records",
                "sides_pixels", "placements", "shapes", "variants", "source_candidate_bound",
                "checkpoint", "checkpoint_sha256", "encoded_root", "embedding_model",
                "drift_tolerances", "cpu_resources", "gpu_profile_resources",
                "original_embedding_verification"):
        assert current[key] == original[key]
    assert current["cpu_output"] != original["cpu_output"]
    assert all(current["source_files"][name] == digest
               for name, digest in original["source_files"].items())


def test_v2_pin_rejects_modified_source_manifest(tmp_path):
    config = json.loads(CONFIG.read_text())
    sources = tmp_path / "sources.csv"
    sources.write_bytes((PROJECT / config["sources_csv"]).read_bytes() + b"\n")
    config["sources_csv"] = str(sources)
    changed = tmp_path / "protocol.json"
    changed.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="Selected source manifest changed"):
        pp.load_config(PROJECT, changed, pp.file_sha256(changed))
