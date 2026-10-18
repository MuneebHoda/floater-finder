import hashlib
import importlib.util
import io
from pathlib import Path
import stat

import pytest


spec = importlib.util.spec_from_file_location("download_approved_inputs", Path(__file__).resolve().parents[1] / "scripts/download_approved_inputs.py")
download = importlib.util.module_from_spec(spec)
spec.loader.exec_module(download)


def entry(tmp_path, payload):
    return {"kind": "diagnostic_wsi", "file_id": "fixture-id",
            "source_url": "https://api.gdc.cancer.gov/data/fixture-id",
            "proposed_destination": str(tmp_path / "inputs" / "fixture.svs"),
            "bytes": len(payload), "checksum": {"algorithm": "md5", "value": hashlib.md5(payload).hexdigest()}}


def test_verified_download_and_existing_data_are_preserved(tmp_path, monkeypatch):
    payload = b"fixture download bytes; not pathology data"
    item = entry(tmp_path, payload)
    calls = []
    def open_response(*args, **kwargs):
        calls.append(1)
        return io.BytesIO(payload)
    monkeypatch.setattr(download, "urlopen", open_response)
    assert download.download_slide(item)["status"] == "verified"
    destination = Path(item["proposed_destination"])
    assert destination.read_bytes() == payload
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert download.download_slide(item)["status"] == "verified_existing" and len(calls) == 1
    destination.write_bytes(b"existing different work")
    with pytest.raises(FileExistsError):
        download.download_slide(item)
    assert destination.read_bytes() == b"existing different work" and len(calls) == 1


@pytest.mark.parametrize("response", [b"incorrect", b"too much downloaded data"])
def test_invalid_download_never_becomes_final_file(tmp_path, monkeypatch, response):
    item = entry(tmp_path, b"expected!")
    monkeypatch.setattr(download, "urlopen", lambda *args, **kwargs: io.BytesIO(response))
    result = download.download_slide(item)
    assert result["status"] == "failed"
    assert not Path(item["proposed_destination"]).exists()
    assert Path(result["partial_path"]).exists()


def test_downloader_rejects_unapproved_source_without_network(tmp_path, monkeypatch):
    item = entry(tmp_path, b"fixture")
    item["source_url"] = "https://other.example/data/fixture-id"
    monkeypatch.setattr(download, "urlopen", lambda *args, **kwargs: pytest.fail("Network must not be used"))
    with pytest.raises(ValueError):
        download.download_slide(item)
