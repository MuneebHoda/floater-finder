import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.error import HTTPError

import pytest


spec = importlib.util.spec_from_file_location("conch_service_smoke", Path(__file__).resolve().parents[1] / "scripts/conch_service_smoke.py")
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


@pytest.fixture
def manifest(tmp_path):
    for name in ("one.png", "two.png"):
        (tmp_path / name).write_bytes(b"fixture bytes, never submitted to a real service")
    path = tmp_path / "tiles.csv"
    path.write_text("tile_id,path\none,one.png\ntwo,two.png\n")
    return path


def fake_requests(monkeypatch, response):
    calls = []
    def request(opener, endpoint, route, payload=None, api_key=None):
        calls.append((route, payload, api_key))
        if route == "/health":
            return {"status": "ok", "model": "conch", "device": "cuda"}
        return response
    monkeypatch.setattr(smoke, "request_json", request)
    return calls


def test_smoke_validates_vectors_and_keeps_key_out_of_artifacts(tmp_path, manifest, monkeypatch):
    rows = [[1.0] + [0.0] * 511, [0.0, 1.0] + [0.0] * 510]
    calls = fake_requests(monkeypatch, {"embeddings": rows, "ignored_server_field": "fixture-key"})
    output = tmp_path / "output"
    report = smoke.run_smoke("http://gpub055.delta.ncsa.illinois.edu:8000", manifest, output, "fixture-key")
    assert report["status"] == "passed" and report["research_result"] is False
    assert report["checkpoint_provenance_verified"] is False and report["full_experiment_compatible"] is False
    assert calls[0][2] is None and calls[1][2] == "fixture-key"
    assert len(calls[1][1]["images"]) == 2
    assert json.loads((output / "embeddings.json").read_text()) == {"embeddings": rows}
    assert all("fixture-key" not in path.read_text() for path in output.iterdir())
    with pytest.raises(FileExistsError):
        smoke.run_smoke("http://gpub055.delta.ncsa.illinois.edu:8000", manifest, output, "fixture-key")
    assert len(calls) == 2


@pytest.mark.parametrize("rows", [[], [[1.0]], [[float("nan")] * 512] * 2, [[2.0] * 512] * 2])
def test_smoke_rejects_invalid_vectors(tmp_path, manifest, monkeypatch, rows):
    fake_requests(monkeypatch, {"embeddings": rows})
    output = tmp_path / "failed"
    result = smoke.run_smoke("http://gpub055.delta.ncsa.illinois.edu:8000", manifest, output, "fixture-key")
    assert result["status"] == "failed" and not result["service_inference_succeeded"]
    assert not (output / "embeddings.json").exists()


def test_auth_failure_stops_without_retry_or_error_body(tmp_path, manifest, monkeypatch):
    calls = []
    def request(*args, **kwargs):
        calls.append(args[2])
        if args[2] == "/health":
            return {"status": "ok", "model": "conch", "device": "cuda"}
        raise HTTPError("http://fixture.invalid", 401, "fixture-key", {}, None)
    monkeypatch.setattr(smoke, "request_json", request)
    output = tmp_path / "failed"
    result = smoke.run_smoke("http://gpub055.delta.ncsa.illinois.edu:8000", manifest, output, "fixture-key")
    assert result["status"] == "authentication_required" and result["http_status"] == 401
    assert calls == ["/health", "/embed"]
    assert "fixture-key" not in (output / "smoke.json").read_text()


@pytest.mark.parametrize("endpoint", ["https://other.example", "http://secret@gpub055.delta.ncsa.illinois.edu:8000", "http://gpub055.delta.ncsa.illinois.edu:8000/?token=secret"])
def test_endpoint_rejects_credentials_and_unrelated_hosts(endpoint):
    with pytest.raises(ValueError):
        smoke.validate_endpoint(endpoint)


def test_manifest_cap_and_redirects_are_enforced(manifest):
    with manifest.open("a") as handle:
        handle.write("three,three.png\n")
    with pytest.raises(ValueError):
        smoke.load_tiles(manifest)
    assert smoke.NoRedirect().redirect_request(None, None, 302, None, None, None) is None


@pytest.mark.parametrize("failure,expected", [("markdown", "plain Delta URL"), ("existing_output", "already exists")])
def test_cli_explains_preflight_failure_before_key_prompt(tmp_path, manifest, monkeypatch, capsys, failure, expected):
    endpoint = "http://gpub055.delta.ncsa.illinois.edu:8000"
    output = tmp_path / "output"
    if failure == "markdown":
        endpoint = f"[{endpoint}]({endpoint})"
    else:
        output.mkdir()
    monkeypatch.setattr(sys, "argv", ["smoke", "--access-approved", "--endpoint", endpoint,
                                     "--tile-manifest", str(manifest), "--output", str(output)])
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)
    def forbidden_prompt(*args):
        pytest.fail("Invalid preflight must not prompt for a key")
    monkeypatch.setattr(smoke.getpass, "getpass", forbidden_prompt)
    with pytest.raises(SystemExit) as error:
        smoke.main()
    assert error.value.code == 2
    assert expected in capsys.readouterr().err


def test_launcher_supplies_plain_url_and_new_output_without_manual_arguments(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_python = fake_bin / "python3"
    fake_python.write_text('#!/bin/bash\nprintf \'%s\\n\' "$@" > "$FLOATER_SMOKE_CAPTURE"\n')
    fake_python.chmod(0o700)
    capture = tmp_path / "arguments.txt"
    launcher = Path(__file__).resolve().parents[1] / "scripts/run_ncsa_service_smoke.sh"
    result = subprocess.run(["bash", str(launcher)], capture_output=True, text=True,
                            env={**os.environ, "PATH": str(fake_bin) + os.pathsep + os.defpath,
                                 "FLOATER_SMOKE_CAPTURE": str(capture)})
    assert result.returncode == 0, result.stderr
    args = capture.read_text().splitlines()
    assert args[args.index("--endpoint") + 1] == "http://gpub055.delta.ncsa.illinois.edu:8000"
    assert Path(args[args.index("--tile-manifest") + 1]).is_file()
    assert args[args.index("--output") + 1].startswith("/work/nvme/bfqi/mhoda/conch-service-smoke-")
