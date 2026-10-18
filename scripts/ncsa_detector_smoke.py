#!/usr/bin/env python3
"""Calibrate on two clean development patients; evaluate the separate frozen pair."""

import argparse
import csv
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import socket


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("development", "evaluation", "config", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        parser.error("Run detector evaluation inside Slurm")
    import numpy as np
    from floater_finder.artifacts import Slide, TextEmbeddings, write_json
    from floater_finder.detection import calibrate, evaluate
    from floater_finder.experiments import file_sha256
    from floater_finder.injection import inject, verify_oracle
    from floater_finder.scoring import tile_scores

    settings = json.loads(Path(args.config).read_text())
    if settings["category"] != "smoke":
        raise ValueError("Explicit detector smoke category required")
    development, evaluation = Path(args.development), Path(args.evaluation)
    dev_paths = [development / (role + "_encoded/slide.npz") for role in ("dev_prostate", "dev_bladder")]
    eval_paths = [evaluation / (role + "_encoded/slide.npz") for role in ("host", "donor")]
    dev = [Slide.load(path) for path in dev_paths]
    hosts = [Slide.load(path) for path in eval_paths]
    text_path = evaluation / "host_encoded/text.npz"
    text = TextEmbeddings.load(text_path)
    if text.source_kind != "real" or text.model["name"] != "conch_v1" or any(slide.metadata["source_kind"] != "real" for slide in dev + hosts):
        raise ValueError("Detector smoke requires real CONCH v1 artifacts")
    for role in ("dev_prostate", "dev_bladder"):
        candidate = TextEmbeddings.load(development / (role + "_encoded/text.npz"))
        if candidate.model != text.model or candidate.prompts != text.prompts or not np.allclose(candidate.feats, text.feats, atol=1e-7, rtol=1e-6):
            raise ValueError("Development encoder/text provenance differs from the frozen evaluation text artifact")
    dev_ids = {slide.metadata["patient_id"] for slide in dev}
    eval_ids = {slide.metadata["patient_id"] for slide in hosts}
    if len(dev_ids) != 2 or len(eval_ids) != 2 or not dev_ids.isdisjoint(eval_ids):
        raise ValueError("Require two development and two independent evaluation patients")
    calibration = calibrate(dev, text, settings["exclusion_mm"], settings["smoothing_mm"], settings["weight"], settings["quantile"], settings["chunk_size"])
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "calibration.json", calibration)
    rows, clean_controls, example = [], [], None
    trials = 0
    for host, donor in (hosts, hosts[::-1]):
        direction = host.metadata["organ"]
        for percent in settings["contamination_percent"]:
            for seed in settings["seeds"]:
                mixed = inject(host, donor, percent, seed)
                verify_oracle(host, mixed, text)
                result, scores, flags = evaluate(mixed, text, calibration, seed)
                if direction == "prostate" and percent == 10 and seed == 0:
                    example = (mixed.coords.copy(), mixed.foreign_mask.copy(), scores["combined"].copy(), flags["combined"].copy())
                trial = output / "trials" / f"{direction}_p{percent:g}_s{seed}"
                context = {"host_patient": host.metadata["patient_id"], "donor_patient": donor.metadata["patient_id"],
                    "requested_percent": percent, "realized_percent": mixed.metadata["injection"]["realized_percent"],
                    "seed": seed, "oracle_verified": True}
                write_json(trial / "metrics.json", {"context": context, **result})
                write_json(trial / "injection.json", mixed.metadata["injection"])
                np.savez_compressed(trial / "scores.npz", tile_ids=mixed.tile_ids, coords=mixed.coords,
                    foreign_mask=mixed.foreign_mask, class_scores=tile_scores(mixed, text),
                    **{f"score_{key}": value for key, value in scores.items()},
                    **{f"flag_{key}": value for key, value in flags.items()})
                for variant, metrics in result["variants"].items():
                    rows.append({**context, "variant": variant,
                        **{key: metrics[key] for key in ("auroc", "detection_rate", "measured_false_alarm_rate", "precision", "fragment_hit", "genuine_host_tiles_removed", "foreign_tiles", "host_tiles", "removed_tiles")}})
                    if percent == 0 and seed == 0:
                        clean_controls.append({"host_patient": host.metadata["patient_id"], "variant": variant, **metrics})
                trials += 1
    if trials != 60 or len(rows) != 180:
        raise RuntimeError("Incomplete detector smoke")
    with (output / "metrics.csv").open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    if example is not None:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        coords, truth, values, flags = example
        coords = coords / 1000
        figure, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained", sharex=True, sharey=True)
        axes[0].scatter(*coords[~truth].T, s=45, marker="s", label="Original host tiles")
        axes[0].scatter(*coords[truth].T, s=45, marker="s", label="Synthetic donor tiles", color="tab:orange")
        axes[0].set_title("Known synthetic injection mask")
        axes[0].legend(fontsize=8)
        colored = axes[1].scatter(*coords.T, c=values, s=45, marker="s", cmap="viridis")
        axes[1].scatter(*coords[flags].T, s=65, facecolors="none", edgecolors="red", label="Flagged")
        axes[1].set_title("Combined score; fixed development threshold")
        axes[1].legend(fontsize=8)
        figure.colorbar(colored, ax=axes[1], label="Combined standardized score")
        for axis in axes:
            axis.set(xlabel="Physical x (mm)", ylabel="Physical y (mm)")
            axis.set_aspect("equal")
        axes[0].invert_yaxis()
        figure.suptitle("Detector smoke: prostate host + synthetic bladder fragment\n10% requested; one preselected 128-tile subset; not clinical floater detection", fontsize=11)
        figure.savefig(output / "detector_map.png", dpi=160)
        plt.close(figure)
    report = {"status": "passed", "category": "smoke", "slurm_job_id": os.environ["SLURM_JOB_ID"],
        "hostname": socket.gethostname(), "settings": settings, "model": text.model,
        "development_patients": sorted(dev_ids), "evaluation_patients": sorted(eval_ids),
        "patient_sets_disjoint": True, "calibration_tiles": sum(len(slide.feats) for slide in dev),
        "oracle_verified_trials": trials, "variant_rows": len(rows), "excluded_trials": 0,
        "frozen_text_fingerprint": text.fingerprint(), "unique_clean_host_controls": len(eval_ids),
        "clean_controls": clean_controls, "input_sha256": {str(p): file_sha256(p) for p in dev_paths + eval_paths + [text_path, Path(args.config)]},
        "source_sha256": {p.name: file_sha256(p) for p in Path(__file__).resolve().parents[1].joinpath("src/floater_finder").glob("*.py")},
        "workflow_sha256": file_sha256(__file__),
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "matplotlib": importlib.metadata.version("matplotlib")},
        "interpretation": "Four-patient, connected-subset detector smoke. Clean means no synthetic injection; native contamination is unreviewed. Repeated seeds/percentages are not independent patients. No clinical or population performance claim."}
    write_json(output / "smoke.json", report)
    print(json.dumps({key: report[key] for key in ("status", "slurm_job_id", "patient_sets_disjoint", "oracle_verified_trials", "variant_rows", "excluded_trials")}), flush=True)


if __name__ == "__main__":
    main()
