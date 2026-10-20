from pathlib import Path
import tomllib

import PIL
import pytest

from floater_finder.conch import ConchEncoder
from floater_finder.image_runtime import PILLOW_VERSION, require_image_runtime
from floater_finder.tiling import extract_tiles


def test_supported_image_protocol_matches_project_pin():
    project = tomllib.loads(Path(__file__).resolve().parents[1].joinpath("pyproject.toml").read_text())
    assert "Pillow==" + PILLOW_VERSION in project["project"]["dependencies"]
    assert require_image_runtime() == PILLOW_VERSION


@pytest.mark.parametrize("version", ["11.3.0", "12.3.0.dev0", "13.0.0"])
def test_wrong_image_runtime_stops_real_io_before_optional_imports(monkeypatch, tmp_path, version):
    monkeypatch.setattr(PIL, "__version__", version)
    monkeypatch.setenv("SLURM_JOB_ID", "software-guard-check")
    with pytest.raises(RuntimeError, match="requires Pillow 12.3.0"):
        extract_tiles({}, tmp_path / "absent")
    with pytest.raises(RuntimeError, match="requires Pillow 12.3.0"):
        ConchEncoder("absent")
    assert not (tmp_path / "absent").exists()
