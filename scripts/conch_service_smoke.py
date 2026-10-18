#!/usr/bin/env python3
"""Two-tile hosted CONCH connection test; not a contamination experiment."""

import argparse
import base64
import csv
import getpass
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import warnings


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def validate_endpoint(endpoint):
    parsed = urlsplit(endpoint)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or not parsed.hostname.endswith(".delta.ncsa.illinois.edu")
            or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment or parsed.path not in {"", "/"}):
        raise ValueError("Supply the organizer's Delta service base URL without credentials")
    return endpoint.rstrip("/")


def load_tiles(manifest):
    manifest = Path(manifest)
    with manifest.open(newline="") as handle:
        rows = list(itertools.islice(csv.DictReader(handle), 3))
    if len(rows) != 2 or any(not row.get("path") or not row.get("tile_id") for row in rows):
        raise ValueError("The smoke manifest must contain exactly two tile_id,path rows")
    if len({row["tile_id"] for row in rows}) != 2:
        raise ValueError("Smoke tile identifiers must be unique")
    encoded, provenance = [], []
    for row in rows:
        path = (manifest.parent / row["path"]).resolve()
        with path.open("rb") as handle:
            raw = handle.read(2 * 1024 * 1024 + 1)
        if not raw or len(raw) > 2 * 1024 * 1024:
            raise ValueError("Each smoke image must be nonempty and at most 2 MiB")
        encoded.append(base64.b64encode(raw).decode("ascii"))
        provenance.append({"tile_id": row["tile_id"], "path": str(path),
                           "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    return encoded, provenance


def request_json(opener, endpoint, route, payload=None, api_key=None):
    headers = {}
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode()
    request = Request(endpoint + route, data=body, headers=headers)
    with opener.open(request, timeout=40) as response:
        raw = response.read(512 * 1024 + 1)
    if len(raw) > 512 * 1024:
        raise ValueError("Service response exceeds smoke-test limit")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object from the service")
    return value


def run_smoke(endpoint, manifest, output, api_key):
    endpoint = validate_endpoint(endpoint)
    if not isinstance(api_key, str) or not api_key.strip() or "\n" in api_key or "\r" in api_key:
        raise ValueError("A nonempty organizer API key is required")
    output = Path(output)
    if output.exists():
        raise FileExistsError("Choose a new smoke output directory")
    images, tiles = load_tiles(manifest)
    output.mkdir(parents=True, exist_ok=False)
    report = {"category": "hosted CONCH connectivity smoke", "research_result": False,
              "endpoint": endpoint, "tiles": tiles, "user_confirmed_individual_access": True,
              "checkpoint_provenance_verified": False, "full_experiment_compatible": False,
              "new_slurm_job_submitted": False, "service_inference_succeeded": False}
    opener = build_opener(NoRedirect())
    try:
        health = request_json(opener, endpoint, "/health")
        report["health"] = {key: health.get(key) for key in ("status", "model", "device")}
        if report["health"] != {"status": "ok", "model": "conch", "device": "cuda"}:
            raise ValueError("Expected the hosted CUDA CONCH service")
        started = time.perf_counter()
        response = request_json(opener, endpoint, "/embed", {"images": images}, api_key)
        report["request_seconds"] = time.perf_counter() - started
        embeddings = response.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != 2:
            raise ValueError("Wrong embedding row count")
        norms = []
        for row in embeddings:
            if (not isinstance(row, list) or len(row) != 512
                    or any(isinstance(v, bool) or not isinstance(v, (int, float))
                           or not math.isfinite(v) for v in row)):
                raise ValueError("Expected finite 512-dimensional CONCH embeddings")
            norm = math.sqrt(sum(v * v for v in row))
            if abs(norm - 1) > 1e-3:
                raise ValueError("CONCH image embeddings must be unit normalized")
            norms.append(norm)
        with (output / "embeddings.json").open("x") as handle:
            json.dump({"embeddings": embeddings}, handle, allow_nan=False)
        report.update(status="passed", service_inference_succeeded=True,
                      tile_count=2, dimensions=512, embedding_norms=norms,
                      timing_scope="HTTP round trip, not GPU throughput")
    except HTTPError as error:
        report.update(status="authentication_required" if error.code in (401, 403) else "http_error",
                      http_status=error.code)
    except (URLError, OSError, ValueError, TypeError, OverflowError) as error:
        # Error bodies and exception messages can echo authentication headers.
        report.update(status="failed", error_type=type(error).__name__)
    with (output / "smoke.json").open("x") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--tile-manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--access-approved", action="store_true", required=True)
    args = parser.parse_args()
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        parser.exit(2, "Run this in your own interactive Terminal; the key must not be echoed.\n")
    try:
        validate_endpoint(args.endpoint)
    except ValueError:
        parser.exit(2, "Invalid endpoint: use a plain Delta URL without Markdown link formatting or credentials.\n")
    if Path(args.output).exists():
        parser.exit(2, "Output directory already exists; choose a new directory to preserve previous results.\n")
    try:
        load_tiles(args.tile_manifest)
    except (OSError, ValueError):
        parser.exit(2, "Tile input check failed: verify the manifest, its two image paths, and the 2 MiB image limit.\n")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            api_key = getpass.getpass("Organizer CONCH API key (hidden, not saved): ")
        report = run_smoke(args.endpoint, args.tile_manifest, args.output, api_key)
    except (OSError, ValueError, getpass.GetPassWarning, EOFError):
        parser.exit(2, "Smoke test could not start: a hidden, nonempty key and a writable new output directory are required.\n")
    print(json.dumps({"status": report["status"], "report": str(Path(args.output) / "smoke.json"),
                      "research_result": False}))
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
