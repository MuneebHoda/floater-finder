"""Explicit, scriptable workflows without hidden model downloads or job submission."""

import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import sys

import numpy as np

from .artifacts import Slide, TextEmbeddings, write_json
from .experiments import run_stress, summarize
from .injection import inject, verify_oracle
from .inventory import inventory, save_inventory
from .scoring import predictions


def inspect_environment():
    packages = {}
    for name in ("numpy", "pandas", "torch", "Pillow", "pytest", "PyYAML", "conch", "open_clip_torch", "trident"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {"platform": platform.system(), "macos": platform.mac_ver()[0] or None,
            "python": platform.python_version(), "python_executable": sys.executable,
            "repository": str(Path.cwd()), "packages": packages,
            "model_note": "Checkpoint paths are supplied explicitly; no model cache or weights are inspected.",
            "ssh_note": "No connection attempted by inspect; connection status is recorded separately."}


def parser():
    result = argparse.ArgumentParser(prog="floater-finder", description="CONCH and PathGen-CLIP research tooling. Fixture output is not scientific evidence.")
    sub = result.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect", help="Inspect local package availability without SSH or model-file access")
    inspect.add_argument("--output")
    inv = sub.add_parser("inventory", help="Bounded slide discovery and explicit cohort metadata CSV")
    inv.add_argument("--root", action="append", default=[])
    inv.add_argument("--manifest")
    inv.add_argument("--institution-map")
    inv.add_argument("--max-files", type=int, default=1000)
    inv.add_argument("--max-depth", type=int, default=3)
    inv.add_argument("--output", required=True)
    fixture = sub.add_parser("fixture", help="Create artificial software-check arrays, not model embeddings")
    fixture.add_argument("--output", required=True)
    for name, help_text in (("validate", "Validate a slide artifact and optional text compatibility"),
                            ("score", "Score an original or contaminated slide")):
        command = sub.add_parser(name, help=help_text)
        command.add_argument("--slide", required=True)
        command.add_argument("--text", required=name == "score")
        if name == "score": command.add_argument("--output", required=True)
    encode = sub.add_parser("encode", help="Encode capped tiles using a local CONCH or PathGen-CLIP checkpoint inside Slurm/CUDA")
    encode.add_argument("--model", choices=("conch", "pathgen-clip"), default="pathgen-clip",
                        help="Encoder architecture (default: pathgen-clip)")
    for name in ("tile-manifest", "metadata", "prompts", "checkpoint", "output"):
        encode.add_argument("--" + name, required=True)
    encode.add_argument("--max-tiles", type=int, default=128)
    encode.add_argument("--batch-size", type=int, default=16)
    injection = sub.add_parser("inject", help="Create a synthetic connected embedding fragment")
    for name in ("host", "donor", "output"): injection.add_argument("--" + name, required=True)
    injection.add_argument("--percent", type=float, required=True)
    injection.add_argument("--seed", type=int, default=0)
    stress = sub.add_parser("stress", help="Run scoring, contamination, mandatory oracle checks, and metrics")
    stress.add_argument("--config", required=True)
    stress.add_argument("--output", required=True)
    oracle = sub.add_parser("oracle", help="Remove known injected tiles and verify exact host recovery")
    for name in ("slide", "original", "text", "output"): oracle.add_argument("--" + name, required=True)
    calibration = sub.add_parser("calibrate", help="Calibrate only on clean, separate development patients")
    calibration.add_argument("--slides", nargs="+", required=True)
    for name in ("text", "output"): calibration.add_argument("--" + name, required=True)
    calibration.add_argument("--exclusion-mm", type=float, default=1)
    calibration.add_argument("--smoothing-mm", type=float, default=.1)
    calibration.add_argument("--weight", type=float, default=.5)
    calibration.add_argument("--quantile", type=float, default=.99)
    calibration.add_argument("--chunk-size", type=int, default=256)
    detection = sub.add_parser("detect", help="Held-out detector/ablation/control evaluation")
    for name in ("slide", "text", "calibration", "output"): detection.add_argument("--" + name, required=True)
    detection.add_argument("--seed", type=int, default=0)
    for name in ("summarize", "plot"):
        command = sub.add_parser(name, help="Recompute denominators" if name == "summarize" else "Plot sufficiently populated real-data results")
        command.add_argument("--run", required=True)
        command.add_argument("--output", required=True)
    return result


def execute(args):
    if args.command == "inspect":
        result = inspect_environment()
        if args.output: write_json(args.output, result)
        return result
    if args.command == "inventory":
        records, report = inventory(args.root, args.manifest, args.institution_map, args.max_files, args.max_depth)
        save_inventory(records, report, args.output)
        return {"candidates": len(records), "truncated": report["discovery_truncated"], "output": args.output}
    if args.command == "fixture":
        from .fixtures import create_fixture
        return create_fixture(args.output)
    if args.command in {"validate", "score"}:
        slide = Slide.load(args.slide)
        if args.command == "validate":
            if args.text:
                from .artifacts import check_compatible
                check_compatible(slide, TextEmbeddings.load(args.text))
            return {"valid": True, "tiles": len(slide.feats), "dimensions": slide.feats.shape[1], "source_kind": slide.metadata["source_kind"]}
        scored = predictions(slide, TextEmbeddings.load(args.text))
        write_json(args.output, {"source_kind": slide.metadata["source_kind"], "predictions": scored})
        return {"source_kind": slide.metadata["source_kind"], "output": args.output}
    if args.command == "encode":
        if args.model == "conch":
            from .conch import encode_tiles
        else:
            from .pathgen import encode_tiles
        return encode_tiles(args.tile_manifest, args.metadata, args.prompts, args.checkpoint, args.output, args.max_tiles, args.batch_size)
    if args.command == "inject":
        mixed = inject(Slide.load(args.host), Slide.load(args.donor), args.percent, args.seed)
        mixed.save(args.output)
        return {"source_kind": mixed.metadata["source_kind"], "synthetically_injected_tiles": int(mixed.foreign_mask.sum()), "output": args.output}
    if args.command == "stress":
        return run_stress(args.config, args.output)
    if args.command == "oracle":
        restored = verify_oracle(Slide.load(args.original), Slide.load(args.slide), TextEmbeddings.load(args.text))
        restored.save(args.output)
        return {"oracle_verified": True, "source_kind": restored.metadata["source_kind"], "output": args.output}
    if args.command == "calibrate":
        from .detection import calibrate
        result = calibrate([Slide.load(path) for path in args.slides], TextEmbeddings.load(args.text), args.exclusion_mm,
                           args.smoothing_mm, args.weight, args.quantile, args.chunk_size)
        write_json(args.output, result)
        return {"source_kind": result["source_kind"], "calibration_tiles": result["calibration_tile_count"], "output": args.output}
    if args.command == "detect":
        from .detection import evaluate
        slide = Slide.load(args.slide)
        calibration = json.loads(Path(args.calibration).read_text())
        result, scores, flags = evaluate(slide, TextEmbeddings.load(args.text), calibration, args.seed)
        output = Path(args.output)
        output.mkdir(parents=True, exist_ok=False)
        write_json(output / "metrics.json", result)
        np.savez_compressed(output / "tile_scores.npz", tile_ids=slide.tile_ids, foreign_mask=slide.foreign_mask,
                            **{f"score_{key}": value for key, value in scores.items()},
                            **{f"flag_{key}": value for key, value in flags.items()})
        return {"source_kind": result["source_kind"], "output": str(output)}
    from .reporting import load_rows, plot_rates
    if args.command == "summarize":
        summary = summarize(load_rows(args.run))
        write_json(args.output, summary)
        return {"strata": len(summary), "output": args.output}
    if args.command == "plot":
        plot_rates(args.run, args.output)
        return {"output": args.output}
    raise ValueError("Unknown command")


def main(argv=None):
    command_parser = parser()
    args = command_parser.parse_args(argv)
    try:
        result = execute(args)
    except (ValueError, KeyError, OSError, RuntimeError, ImportError) as error:
        command_parser.exit(2, f"floater-finder: {error}\n")
    print(json.dumps(result, indent=2, allow_nan=False))
