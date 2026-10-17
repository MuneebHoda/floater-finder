import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from floater_finder.artifacts import Slide
from floater_finder.cli import main


def test_installed_command_in_an_isolated_interpreter(tmp_path):
    result = subprocess.run([sys.executable, "-I", "-m", "floater_finder", "--help"], cwd=tmp_path,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "stress" in result.stdout


def test_installed_package_matches_current_source(tmp_path):
    installed = subprocess.check_output([sys.executable, "-I", "-c", "import floater_finder; print(floater_finder.__file__)"],
                                        cwd=tmp_path, text=True).strip()
    source = Path(__file__).resolve().parents[1] / "src/floater_finder"
    for path in source.glob("*.py"):
        assert path.read_bytes() == (Path(installed).parent / path.name).read_bytes(), \
            "Reinstall current source: uv sync --locked --no-editable --reinstall-package floater-finder --extra test"


def test_cli_full_fixture_workflow(tmp_path, capsys):
    fixtures = tmp_path / "fixture"
    main(["fixture", "--output", str(fixtures)])
    def path(name): return str(fixtures / name)
    main(["validate", "--slide", path("host.npz"), "--text", path("text.npz")])
    main(["score", "--slide", path("host.npz"), "--text", path("text.npz"), "--output", path("clean-score.json")])
    main(["stress", "--config", path("run.yaml"), "--output", str(tmp_path / "stress")])
    main(["inject", "--host", path("host.npz"), "--donor", path("donor.npz"), "--percent", "5", "--seed", "7", "--output", path("mixed.npz")])
    main(["oracle", "--slide", path("mixed.npz"), "--original", path("host.npz"), "--text", path("text.npz"), "--output", path("restored.npz")])
    np.testing.assert_array_equal(Slide.load(path("restored.npz")).feats, Slide.load(path("host.npz")).feats)
    main(["calibrate", "--slides", path("dev.npz"), "--text", path("text.npz"), "--output", path("calibration.json")])
    main(["detect", "--slide", path("mixed.npz"), "--text", path("text.npz"), "--calibration", path("calibration.json"), "--output", str(tmp_path / "detection")])
    main(["detect", "--slide", path("clean_eval.npz"), "--text", path("text.npz"), "--calibration", path("calibration.json"), "--output", str(tmp_path / "clean-control")])
    main(["summarize", "--run", str(tmp_path / "stress"), "--output", str(tmp_path / "summary.json")])
    assert json.loads((tmp_path / "detection/metrics.json").read_text())["source_kind"] == "fixture"
    assert json.loads((tmp_path / "summary.json").read_text()) == json.loads((tmp_path / "stress/summary.json").read_text())
    assert "fixture" in capsys.readouterr().out


def test_cli_does_not_overwrite_existing_work(tmp_path):
    main(["fixture", "--output", str(tmp_path / "fixture")])
    with pytest.raises(SystemExit) as error:
        main(["fixture", "--output", str(tmp_path / "fixture")])
    assert error.value.code == 2


def test_cli_inspect_and_empty_inventory(tmp_path):
    main(["inspect", "--output", str(tmp_path / "environment.json")])
    main(["inventory", "--root", str(tmp_path), "--output", str(tmp_path / "inventory")])
    assert json.loads((tmp_path / "inventory/missing_data.json").read_text())["candidate_count"] == 0


@pytest.mark.parametrize("template", ["configs/conch_smoke.yaml", "configs/pathgen_clip_smoke.yaml"])
def test_real_templates_and_fixture_plot_are_explicitly_blocked(tmp_path, template):
    real_output = tmp_path / "real"
    with pytest.raises(SystemExit) as error:
        main(["stress", "--config", template, "--output", str(real_output)])
    assert error.value.code == 2 and not real_output.exists()
    fixtures = tmp_path / "fixture"
    main(["fixture", "--output", str(fixtures)])
    main(["stress", "--config", str(fixtures / "run.yaml"), "--output", str(tmp_path / "run")])
    with pytest.raises(SystemExit) as error:
        main(["plot", "--run", str(tmp_path / "run"), "--output", str(tmp_path / "scientific.png")])
    assert error.value.code == 2 and not (tmp_path / "scientific.png").exists()
