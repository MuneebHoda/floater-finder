#!/usr/bin/env python3
"""Render README artwork and plots from committed aggregate evidence only."""
import argparse
import hashlib
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
INK, MUTED, TEAL, PINK = "#17313b", "#607981", "#087f8c", "#bd597d"
PAPER = "#f5f8f8"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hero(output):
    fig = plt.figure(figsize=(12, 4.25), facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set(xlim=(0, 1200), ylim=(0, 425)); ax.axis("off")
    ax.text(50, 367, "COMPUTATIONAL PATHOLOGY  /  ASHBY HACKATHON 2026", color=TEAL,
            fontsize=10, weight="bold", va="center")
    ax.text(48, 285, "Floater Finder", color=INK, fontsize=40, weight="bold")
    ax.text(50, 226, "Which tissue piece drives\nthe AI prediction?", color=INK,
            fontsize=22, linespacing=1.35, va="top")
    ax.text(50, 126, "Trace the influence. Preserve the tissue.", color=MUTED, fontsize=12)
    ax.add_patch(FancyBboxPatch((730, 110), 410, 254, boxstyle="round,pad=0,rounding_size=22",
                               facecolor="#e6eff0", edgecolor="none"))
    for x in range(758, 1125, 24):
        for y in range(130, 350, 24):
            ax.plot(x, y, ".", color="#c6dadd", markersize=2)
    # Schematic geometry only: no patient image, inferred boundary or detector output.
    a = [(776, 174), (782, 212), (810, 230), (817, 268), (849, 294),
         (883, 302), (902, 280), (893, 246), (863, 222), (853, 190), (823, 165)]
    b = [(882, 149), (893, 181), (923, 188), (943, 212), (967, 202),
         (976, 176), (956, 151), (919, 136)]
    ax.add_patch(Polygon(a, closed=True, facecolor="#a9d0d1", edgecolor=TEAL, linewidth=1.5))
    ax.add_patch(Polygon(b, closed=True, facecolor="#b6d8d7", edgecolor=TEAL, linewidth=1.5))
    ax.add_patch(Polygon([(1007, 269), (1012, 291), (1033, 304), (1055, 291),
                         (1051, 267), (1030, 258)], closed=True,
                        facecolor="#e7bbce", edgecolor=PINK, linewidth=1.8))
    ax.add_patch(Rectangle((989, 245), 84, 74, fill=False, edgecolor=PINK,
                           linestyle=(0, (4, 3)), linewidth=1.2))
    ax.text(1030, 337, "Exclude one piece?", ha="center", color=PINK, fontsize=11, weight="bold")
    ax.text(935, 91, "Concept illustration · not a detection result", ha="center", color=MUTED, fontsize=8)
    for i, (label, x) in enumerate(zip(("READ TISSUE", "ENCODE WITH CONCH", "TEST PIECE INFLUENCE", "REVIEW EVIDENCE"), (50, 325, 610, 920))):
        ax.text(x, 39, f"0{i+1}", color=TEAL, fontsize=11, weight="bold")
        ax.text(x+34, 39, label, color=INK, fontsize=9, va="baseline")
        if i < 3:
            ax.add_patch(FancyArrowPatch((x+210, 44), (x+250, 44), arrowstyle="->", mutation_scale=12,
                                        color="#96aeb3", linewidth=1))
    fig.savefig(output / "hero.png", dpi=150, facecolor=PAPER)
    plt.close(fig)


def evidence(output):
    baseline_path = ROOT / "reports/panda_fresh_baseline_results_v1.md"
    trials_path = ROOT / "reports/panda_s1_trials_23065666.json"
    match = re.search(r"Benign/cancer — frozen primary linear: `([^`]+)`", baseline_path.read_text())
    matrix = np.array(json.loads(match[1]))
    assert matrix.tolist() == [[18, 2], [12, 28]] and matrix.sum() == 60
    trials = json.loads(trials_path.read_text())
    doses = sorted({r["requested_percent"] for r in trials})
    counts, supports = [], []
    for dose in doses:
        rows = [r for r in trials if r["split"] == "calibration" and r["requested_percent"] == dose]
        assert len(rows) == len({r["host_id"] for r in rows}) == 8
        correct = [r for r in rows if r["baseline"]["top5pct"]["prediction"] == "benign"]
        assert len(correct) == 5 and all(r["oracle_exact_recovery"] for r in rows)
        supports.append(sorted(r["host_id"] for r in correct))
        counts.append(sum(r["contaminated"]["top5pct"]["prediction"] != "benign" for r in correct))
    assert all(s == supports[0] for s in supports) and counts == [0, 1, 1, 2, 2, 2]

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "text.color": INK,
                         "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), gridspec_kw={"width_ratios": [1, 1.25]})
    fig.patch.set_facecolor("white"); fig.subplots_adjust(left=.1, right=.965, bottom=.34, top=.76, wspace=.6)
    ax = axes[0]
    ax.imshow(matrix / matrix.sum(axis=1, keepdims=True), vmin=0, vmax=1,
              cmap=LinearSegmentedColormap.from_list("readme", ["#f0f5f5", TEAL]))
    for (row, col), value in np.ndenumerate(matrix):
        ax.text(col, row, str(value), ha="center", va="center", fontsize=28, weight="bold",
                color="white" if value/matrix[row].sum() > .5 else INK)
    ax.set(xticks=[0, 1], xticklabels=["Benign", "Cancer"], yticks=[0, 1],
           yticklabels=["Benign", "Cancer"], xlabel="Predicted class", ylabel="True class")
    ax.tick_params(length=0, pad=8)
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.set_title("Can the model classify tissue?", loc="left", pad=46, fontsize=16, weight="bold")
    ax.text(0, 1.07, "Frozen primary · separate 60-slide cohort", transform=ax.transAxes, color=MUTED, fontsize=10)
    ax.text(0, -.33, "80% balanced accuracy", transform=ax.transAxes, weight="bold", fontsize=14, color=TEAL)
    ax.text(0, -.44, "95% slide-bootstrap interval: 70–88.75%", transform=ax.transAxes, color=MUTED, fontsize=9)

    ax = axes[1]; x = np.array(doses)
    ax.plot(x, counts, color=PINK, linewidth=2.8, marker="o", markersize=8)
    ax.fill_between(x, counts, color="#f8e9ef")
    ax.set(xticks=[0, 1, 2, 5, 10], yticks=range(6), ylim=(-.15, 5.15),
           xlabel="Requested foreign / original host tiles (%)", ylabel="New cancer errors / 5 correct hosts")
    ax.grid(axis="y", color="#e8eeee"); ax.set_axisbelow(True)
    for side in ("top", "right", "left"): ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#d4dfe1"); ax.tick_params(length=0, pad=8)
    ax.set_title("Can a fragment change a decision?", loc="left", pad=46, fontsize=16, weight="bold")
    ax.text(0, 1.07, "Development stress · historical top-5% scorer", transform=ax.transAxes, color=MUTED, fontsize=10)
    ax.text(0, -.33, "2 of 5 initially correct hosts flip at 10%", transform=ax.transAxes,
            weight="bold", fontsize=12, color=PINK)
    ax.text(0, -.44, "Repeated hosts across doses · synthetic embedding mixtures", transform=ax.transAxes, color=MUTED, fontsize=9)
    fig.text(.5, .04, "Classification and contamination stress are separate experiments. Neither validates foreign-tissue detection.",
             ha="center", fontsize=10, color=MUTED)
    fig.savefig(output / "evidence.png", dpi=170)
    plt.close(fig)
    return {"baseline_confusion_matrix": matrix.tolist(), "baseline_slides": int(matrix.sum()),
            "stress_requested_percent": doses, "stress_new_errors": counts,
            "stress_originally_correct_unique_hosts": 5, "stress_all_calibration_hosts": 8,
            "stress_prediction_role": "historical top5pct; not the later frozen linear primary",
            "stress_dose_denominator": "foreign tiles / original host tiles; ceil-rounded",
            "independent_patients_verified": False,
            "inputs": {str(p.relative_to(ROOT)): digest(p) for p in (baseline_path, trials_path)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/assets/readme")
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    hero(output)
    facts = evidence(output)
    facts.update(hero="Concept artwork only; no patient pixels or model predictions",
                 build_script_sha256=digest(Path(__file__)),
                 outputs={p.name: digest(p) for p in (output/"hero.png", output/"evidence.png")})
    (output / "provenance.json").write_text(json.dumps(facts, indent=2, allow_nan=False)+"\n")
    print(f"Rendered README artwork and two evidence panels to {output}")


if __name__ == "__main__":
    main()
