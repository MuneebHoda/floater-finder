#!/usr/bin/env python3
"""Draft two-stage PANDA engineering smoke. Run each stage only in approved Slurm."""

import argparse
import csv
import json
import os
from pathlib import Path
import socket


def run(config_path, output, stage, tiles=None):
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("PANDA smoke requires an authorized Slurm job")
    from floater_finder.artifacts import Slide, TextEmbeddings, write_json
    from floater_finder.experiments import file_sha256
    from floater_finder.panda import extract_panda_tiles

    project = Path(__file__).resolve().parents[1]
    config_path, output = Path(config_path), Path(output)
    config = json.loads(config_path.read_text())
    source_kind = config.get("source_kind", "real")
    if source_kind not in {"real", "fixture"}:
        raise ValueError("Explicit source_kind must be real or fixture")
    ids = [slide["image_id"] for slide in config["slides"]]
    cap = config["max_tiles_per_slide"]
    if not 1 <= len(ids) <= 3 or len(set(ids)) != len(ids) or type(cap) is not int or not 1 <= cap <= 32:
        raise ValueError("Smoke scope is at most three distinct slides and 32 tiles per slide")
    if stage not in {"tile", "encode"}:
        raise ValueError("Unknown smoke stage")
    if stage == "encode" and tiles is None:
        raise ValueError("Encoding requires a completed CPU tiling output")
    if stage == "encode" and source_kind != "real":
        raise ValueError("Fixture smoke cannot be encoded or relabelled as real")
    if output.exists():
        raise FileExistsError("Choose a new output; do not overwrite prior runs")
    checkpoint = None
    if stage == "encode":
        import torch
        from floater_finder.conch import encode_tiles
        from ncsa_pilot_preflight import verify_input
        if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
            raise ValueError("Exactly one scheduled CUDA GPU required")
        torch.set_num_threads(4)
        torch.manual_seed(0)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        checkpoint = json.loads((project / config["checkpoint_config"]).read_text())["checkpoint"]
        verify_input(checkpoint)
        tiling_report = json.loads((Path(tiles) / "tiling.json").read_text())
        if (tiling_report["status"] != "passed" or tiling_report["source_kind"] != "real" or
                tiling_report["config_sha256"] != file_sha256(config_path)):
            raise ValueError("CPU tiling config/status differs from this smoke")
        if [record["image_id"] for record in tiling_report["slides"]] != ids:
            raise ValueError("CPU tiling slide set mismatch")
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    records, fingerprint = [], None
    for slide in config["slides"]:
        image_id = slide["image_id"]
        if stage == "tile":
            directory = output / image_id
            result = extract_panda_tiles(config["root"], image_id, directory,
                field_um=config["field_um"], pixels=config["export_pixels"], max_tiles=cap,
                max_candidates=config["max_candidates_per_slide"], min_tissue_fraction=config["min_tissue_fraction"],
                recorded_mpp_xy=config["recorded_mpp_xy"], source_kind=source_kind)
            metadata = result["metadata"]
            if (metadata["isup_grade"] != slide["isup_grade"] or
                    metadata["panda"]["mask_available"] != slide["mask_available"] or
                    (slide.get("gleason_score") is not None and metadata["gleason_score"] != slide["gleason_score"])):
                raise ValueError("Original labels/mask availability differ from user-verified smoke inputs")
            record = {"image_id": image_id, "tiles": result["tiles"],
                      "metadata_sha256": file_sha256(directory / "metadata.json"),
                      "manifest_sha256": file_sha256(directory / "tiles.csv"),
                      "tile_png_sha256": {path.name: file_sha256(path) for path in sorted(directory.glob("*.png"))}}
        else:
            directory = Path(tiles) / image_id
            expected = next(record for record in tiling_report["slides"] if record["image_id"] == image_id)
            if (file_sha256(directory / "metadata.json") != expected["metadata_sha256"] or
                    file_sha256(directory / "tiles.csv") != expected["manifest_sha256"]):
                raise ValueError("Prepared tiling metadata/manifest changed")
            for name, digest in expected["tile_png_sha256"].items():
                if Path(name).name != name or file_sha256(directory / name) != digest:
                    raise ValueError("Prepared tile changed")
            with (directory / "tiles.csv").open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            if not 1 <= len(rows) <= cap or len(rows) != expected["tiles"]:
                raise ValueError("Prepared tile count exceeds smoke scope or differs from report")
            metadata = json.loads((directory / "metadata.json").read_text())
            if metadata["source_kind"] != "real" or metadata["slide_id"] != image_id:
                raise ValueError("Cannot encode fixtures or mismatched slide metadata as real")
            encoded = output / image_id
            encode_tiles(directory / "tiles.csv", directory / "metadata.json", project / config["prompts"],
                         checkpoint["path"], encoded, max_tiles=cap, batch_size=config["batch_size"])
            saved, text = Slide.load(encoded / "slide.npz"), TextEmbeddings.load(encoded / "text.npz")
            if saved.feats.shape != (len(rows), 512) or saved.metadata["model"]["checkpoint_sha256"] != checkpoint["checksum"]["value"]:
                raise ValueError("Unexpected CONCH v1 shape/checkpoint provenance")
            if fingerprint is not None and fingerprint != text.fingerprint():
                raise ValueError("Shared text/model fingerprint changed between slides")
            fingerprint = text.fingerprint()
            record = {"image_id": image_id, "tiles": len(rows), "slide_sha256": file_sha256(encoded / "slide.npz"),
                      "text_sha256": file_sha256(encoded / "text.npz"), "text_fingerprint": fingerprint}
        records.append(record)
    report = {"status": "passed", "category": "fixture_software_check" if source_kind == "fixture" else "PANDA engineering smoke only",
        "source_kind": source_kind, "stage": stage,
        "slurm_job_id": os.environ["SLURM_JOB_ID"], "hostname": socket.gethostname(),
        "config_sha256": file_sha256(config_path), "script_sha256": file_sha256(__file__),
        "panda_source_sha256": file_sha256(project / "src/floater_finder/panda.py"),
        "prompts_sha256": file_sha256(project / config["prompts"]), "slides": records,
        "tiling_report_sha256": file_sha256(Path(tiles) / "tiling.json") if stage == "encode" else None,
        "total_tiles": sum(record["tiles"] for record in records),
        "clinical_model_validity_verified": False, "cancer_performance_evaluated": False}
    write_json(output / ("tiling.json" if stage == "tile" else "encoding.json"), report)
    print(json.dumps({"status": "passed", "stage": stage, "tiles": report["total_tiles"]}), flush=True)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "configs/panda_smoke.json"))
    parser.add_argument("--stage", choices=["tile", "encode"], required=True)
    parser.add_argument("--tiles", help="Completed CPU-stage output; required by encode")
    parser.add_argument("--output", required=True, help="Fresh output directory")
    args = parser.parse_args(argv)
    if not os.environ.get("SLURM_JOB_ID"):
        parser.error("Run PANDA smoke only inside an authorized Slurm job")
    run(args.config, args.output, args.stage, args.tiles)


if __name__ == "__main__":
    main()
