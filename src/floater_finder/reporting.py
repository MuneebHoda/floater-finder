"""Standard scientific plotting, gated on sufficient real-data observations."""

from collections import defaultdict
from pathlib import Path
import csv
import json
import numpy as np

from .experiments import summarize


def load_rows(run):
    with (Path(run) / "results.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for key in ("original_correct", "prediction_changed"):
            if row[key] not in {"True", "False"}:
                raise ValueError("Malformed boolean result column")
            row[key] = row[key] == "True"
        row["seed"] = int(row["seed"])
        row["requested_percent"] = float(row["requested_percent"])
    return rows


def plot_rates(run, output):
    run = Path(run)
    metadata = json.loads((run / "experiment.json").read_text())
    rows = load_rows(run)
    if metadata["category"] == "fixture" or metadata["source_kind"] != "real":
        raise ValueError("Scientific plots require real observations, not unit fixtures")
    if len({row["host_slide_id"] for row in rows}) < 2 or len({row["requested_percent"] for row in rows}) < 2:
        raise ValueError("Need at least two real hosts and two contamination levels for this pilot chart")
    values = defaultdict(list)
    for row in summarize(rows):
        if row["eligible_flip_rate"] is not None:
            values[(row["pooling"], row["requested_percent"])].append(row["eligible_flip_rate"])
    if not values:
        raise ValueError("No originally correct eligible hosts; flip rate is undefined")
    output = Path(output)
    if output.exists():
        raise FileExistsError("Choose a new plot path")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 4), layout="constrained")
    for rule in sorted({key[0] for key in values}):
        levels = sorted(key[1] for key in values if key[0] == rule)
        ax.plot(levels, [np.mean(values[(rule, percent)]) for percent in levels], marker="o", label=rule)
    ax.set(xlabel="Synthetic foreign tiles / original host tiles (%)", ylabel="Eligible flip rate (mean over seeds)", ylim=(-.02, 1.02),
           title=f"{metadata['model']['name']} {metadata['category']}: synthetic embedding contamination")
    ax.legend()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)
