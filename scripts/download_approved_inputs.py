#!/usr/bin/env python3
"""Download approved public GDC slides with bounded size and checksum checks."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import uuid


def checksum(path, algorithm):
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_slide(item):
    source = urlsplit(item["source_url"])
    if (item["kind"] != "diagnostic_wsi" or source.scheme != "https"
            or source.hostname != "api.gdc.cancer.gov"
            or source.path != "/data/" + item["file_id"]
            or source.username is not None or source.password is not None
            or source.query or source.fragment):
        raise ValueError("Only the approved public GDC file endpoint is accepted")
    destination = Path(item["proposed_destination"])
    expected = item["bytes"]
    algorithm = item["checksum"]["algorithm"]
    expected_hash = item["checksum"]["value"]
    if expected <= 0 or algorithm != "md5":
        raise ValueError("Expected the verified GDC file size and MD5 checksum")
    if destination.is_symlink():
        raise FileExistsError("Preserve existing symlink")
    if destination.exists():
        if destination.stat().st_size != expected or checksum(destination, algorithm) != expected_hash:
            raise FileExistsError("Existing destination does not match; preserve it")
        return {"file_id": item["file_id"], "path": str(destination), "status": "verified_existing",
                "bytes": expected, "checksum": item["checksum"]}

    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part-" + uuid.uuid4().hex)
    digest = hashlib.new(algorithm)
    received = 0
    started = time.monotonic()
    last_update = started
    request = Request(item["source_url"], headers={"Accept-Encoding": "identity"})
    try:
        with urlopen(request, timeout=60) as response, partial.open("xb") as handle:
            # Delta default ACLs can override umask for newly created files.
            os.fchmod(handle.fileno(), 0o600)
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                received += len(block)
                if received > expected:
                    raise ValueError("Response exceeds the approved file size")
                handle.write(block)
                digest.update(block)
                if time.monotonic() - last_update >= 15:
                    print(json.dumps({"event": "progress", "file_id": item["file_id"],
                                      "bytes": received, "expected_bytes": expected}), flush=True)
                    last_update = time.monotonic()
        if received != expected or digest.hexdigest() != expected_hash:
            raise ValueError("Downloaded size or checksum does not match")
        # Hard-link creation fails if another process created the final name.
        os.link(partial, destination)
        partial.unlink()
        return {"file_id": item["file_id"], "path": str(destination), "status": "verified",
                "bytes": received, "checksum": item["checksum"],
                "download_seconds": time.monotonic() - started}
    except Exception as error:
        return {"file_id": item["file_id"], "path": str(destination), "status": "failed",
                "bytes_received": received, "partial_path": str(partial),
                "error_type": type(error).__name__}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text())
    if plan.get("approved") is not True:
        parser.exit(2, "Explicit user download approval must be recorded in the plan.\n")
    report_path = Path(args.report)
    if report_path.exists():
        parser.exit(2, "Preserve the existing report; choose a new report path.\n")
    os.umask(0o077)
    results = []
    for item in plan["files"]:
        if item["kind"] != "diagnostic_wsi":
            continue
        print(json.dumps({"event": "starting", "file_id": item["file_id"],
                          "expected_bytes": item["bytes"]}), flush=True)
        try:
            result = download_slide(item)
        except (OSError, ValueError) as error:
            result = {"file_id": item["file_id"], "status": "failed", "error_type": type(error).__name__}
        results.append(result)
        report_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary_report = report_path.with_name(report_path.name + ".updating")
        with temporary_report.open("x") as handle:
            os.fchmod(handle.fileno(), 0o600)
            json.dump({"created_at_utc": datetime.now(timezone.utc).isoformat(), "files": results,
                       "model_checkpoint_download_attempted": False}, handle, indent=2)
        temporary_report.replace(report_path)
        print(json.dumps(result), flush=True)
    return 0 if results and all(result["status"].startswith("verified") for result in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
