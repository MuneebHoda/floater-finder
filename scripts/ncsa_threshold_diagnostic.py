#!/usr/bin/env python3
"""Development-only cutoff diagnostic, reusing existing CONCH v1 artifacts."""

import argparse
from copy import deepcopy
import csv
import json
import os
from pathlib import Path
import platform
import socket


def run(slides, text, settings, output):
    import numpy as np
    from floater_finder.artifacts import write_json
    from floater_finder.detection import calibrate, detection_metrics, development_anomaly_scores, VARIANTS
    from floater_finder.injection import inject, verify_oracle
    from floater_finder.scoring import tile_scores

    patient_ids = {slide.metadata["patient_id"] for slide in slides}
    if settings["category"] != "development_diagnostic" or len(slides) != 2 or len(patient_ids) != 2:
        raise ValueError("Two distinct development patients and diagnostic category required")
    if patient_ids != set(settings["development_patients"]) or patient_ids & set(settings["excluded_evaluation_patients"]):
        raise ValueError("Diagnostic patients must match the development allowlist and exclude evaluation patients")
    base = calibrate(slides, text, settings["exclusion_mm"], settings["smoothing_mm"], settings["weight"], settings["reference_quantile"], settings["chunk_size"])
    clean = [development_anomaly_scores(slide, text, base) for slide in slides]
    calibrations, clean_controls = [], []
    for quantile in settings["quantiles"]:
        if not 0 < quantile < 1:
            raise ValueError("Quantiles must be between zero and one")
        calibration = deepcopy(base)
        calibration["quantile"] = quantile
        for variant in VARIANTS:
            values = np.concatenate([scores[variant] for scores in clean])
            threshold = float(np.quantile(values, quantile, method="higher"))
            calibration["thresholds"][variant] = threshold
            calibration["measured_development_false_alarm"][variant] = float(np.mean(values > threshold))
            for slide, scores in zip(slides, clean):
                clean_controls.append({"patient_id": slide.metadata["patient_id"], "organ": slide.metadata["organ"],
                    "quantile": quantile, "variant": variant, "threshold": threshold,
                    "removed_tiles": int((scores[variant] > threshold).sum()), "host_tiles": len(slide.feats),
                    "measured_false_alarm_rate": float(np.mean(scores[variant] > threshold))})
        calibrations.append(calibration)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "calibrations.json", calibrations)
    write_json(output / "clean_controls.json", clean_controls)
    for slide, scores in zip(slides, clean):
        np.savez_compressed(output / (slide.metadata["organ"] + "_clean_scores.npz"),
            tile_ids=slide.tile_ids, **scores)
    rows, trials = [], 0
    for host, donor in (slides, slides[::-1]):
        for percent in settings["contamination_percent"]:
            for seed in settings["seeds"]:
                mixed = inject(host, donor, percent, seed)
                verify_oracle(host, mixed, text)
                scores = development_anomaly_scores(mixed, text, base)
                trial = output / "trials" / f'{host.metadata["organ"]}_p{percent:g}_s{seed}'
                write_json(trial / "injection.json", mixed.metadata["injection"])
                np.savez_compressed(trial / "scores.npz", tile_ids=mixed.tile_ids, coords=mixed.coords,
                    foreign_mask=mixed.foreign_mask, class_scores=tile_scores(mixed, text), **scores)
                for calibration in calibrations:
                    for variant in VARIANTS:
                        threshold = calibration["thresholds"][variant]
                        rows.append({"host_patient": host.metadata["patient_id"], "donor_patient": donor.metadata["patient_id"],
                            "requested_percent": percent, "realized_percent": mixed.metadata["injection"]["realized_percent"],
                            "seed": seed, "quantile": calibration["quantile"], "variant": variant, "threshold": threshold,
                            **detection_metrics(mixed.foreign_mask, scores[variant], scores[variant] > threshold)})
                trials += 1
    with (output / "metrics.csv").open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return {"development_patients": sorted(patient_ids), "calibration_tiles": base["calibration_tile_count"],
        "oracle_verified_trials": trials, "metric_rows": len(rows), "excluded_trials": 0,
        "calibrations": calibrations, "clean_controls": clean_controls,
        "ten_percent_summary": summarize(rows, 10)}


def summarize(rows, percent):
    import numpy as np
    keys = sorted({(row["quantile"], row["variant"]) for row in rows})
    summary = []
    for quantile, variant in keys:
        selected = [row for row in rows if row["quantile"] == quantile and row["variant"] == variant and row["requested_percent"] == percent]
        if selected:
            summary.append({"quantile": quantile, "variant": variant, "requested_percent": percent,
                "trials": len(selected), "independent_patients": len({row["host_patient"] for row in selected}),
                **{name: float(np.mean([row[name] for row in selected])) for name in ("auroc", "detection_rate", "measured_false_alarm_rate")}})
    return summary


def plot(report, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figure, axis = plt.subplots(figsize=(8, 5), layout="constrained")
    for variant in ("organ_only", "visual_only", "combined"):
        entries = [row for row in report["ten_percent_summary"] if row["variant"] == variant]
        axis.plot([100 * row["measured_false_alarm_rate"] for row in entries],
            [100 * row["detection_rate"] for row in entries], "o-", label=variant.replace("_", " "))
        for row in entries:
            axis.annotate(f'q={row["quantile"]:g}', (100 * row["measured_false_alarm_rate"], 100 * row["detection_rate"]),
                xytext=(4, 4), textcoords="offset points", fontsize=7)
    axis.set(xlabel="Mean original-host removal (%)", ylabel="Mean injected-tile detection (%)",
        title="Development cutoff diagnostic: 10% requested contamination\nTwo calibration patients reused; five seeds; not held-out performance")
    axis.legend()
    axis.grid(alpha=0.2)
    axis.margins(x=0.12)
    axis.set_ylim(0, 107)
    figure.savefig(Path(output) / "threshold_tradeoff.png", dpi=160)
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("development", "config", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        parser.error("Run the development diagnostic inside Slurm")
    import numpy as np
    from floater_finder.artifacts import Slide, TextEmbeddings, write_json
    from floater_finder.experiments import file_sha256
    development = Path(args.development)
    slide_paths = [development / (role + "_encoded/slide.npz") for role in ("dev_prostate", "dev_bladder")]
    text_paths = [path.with_name("text.npz") for path in slide_paths]
    slides = [Slide.load(path) for path in slide_paths]
    texts = [TextEmbeddings.load(path) for path in text_paths]
    text = texts[0]
    if text.source_kind != "real" or text.model["name"] != "conch_v1" or text.feats.shape[1] != 512:
        raise ValueError("Real, projected 512-dimensional CONCH v1 artifacts required")
    if texts[1].fingerprint() != text.fingerprint():
        raise ValueError("Development text artifacts must match the frozen prompt/model ensemble")
    settings = json.loads(Path(args.config).read_text())
    report = run(slides, text, settings, args.output)
    plot(report, args.output)
    report.update(status="passed", category="development_diagnostic", slurm_job_id=os.environ["SLURM_JOB_ID"],
        hostname=socket.gethostname(), settings=settings, model=text.model, frozen_text_fingerprint=text.fingerprint(),
        input_sha256={str(path): file_sha256(path) for path in slide_paths + text_paths + [Path(args.config)]},
        source_sha256={p.name: file_sha256(p) for p in Path(__file__).resolve().parents[1].joinpath("src/floater_finder").glob("*.py")},
        workflow_sha256=file_sha256(__file__), runtime={"python": platform.python_version(), "numpy": np.__version__},
        selected_quantile=None, evaluation_artifacts_loaded=False,
        interpretation="Development resubstitution diagnostic only. Calibration patients are reused as synthetic hosts/donors. Not independent performance or a 1% unseen-FPR guarantee. Clean means unmodified, not pathologist-reviewed.")
    write_json(Path(args.output) / "diagnostic.json", report)
    print(json.dumps({key: report[key] for key in ("status", "slurm_job_id", "oracle_verified_trials", "metric_rows", "selected_quantile")}), flush=True)


if __name__ == "__main__":
    main()
