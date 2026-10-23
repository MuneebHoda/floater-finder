#!/usr/bin/env python3
"""Save/reload artificial embeddings and emit a piece-dependence software fixture."""

import argparse
from pathlib import Path

import numpy as np

from floater_finder.artifacts import Slide, write_json
from floater_finder.fragment_dependence import analyze_fragment_dependence


def fixture_scorer(embeddings, coords):
    """Artificial max-positive scorer, neither CONCH nor a validated cancer model."""
    value = float(embeddings[:, 1].max())
    return {"prediction": "cancer" if value >= 0.5 else "benign",
            "scores": {"artificial_positive_feature_max": value}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New fixture output directory")
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=False)
    metadata = {"slide_id": "artificial-biopsy", "patient_id": "fixture-only",
                "project": "FIXTURE", "organ": "prostate", "split": "dev", "source_kind": "fixture",
                "coordinate_units": "microns", "tile_step": [112, 112], "tile_size": [112, 112],
                "microns_per_unit": 1, "geometry_provenance": "Invented fixture geometry, not a measured slide",
                "model": {"name": "artificial-one-hot", "revision": "fixture-v1",
                          "checkpoint_sha256": "no-checkpoint-fixture-only", "projection": True,
                          "normalized": True, "preprocessing": "Artificial arrays; no image or model inference"}}
    slide = Slide(np.array([[1., 0.], [1., 0.], [1., 0.], [0., 1.]]),
                  np.array([[0, 0], [112, 0], [224, 0], [2240, 0]]),
                  np.array(["benign-0", "benign-1", "benign-2", "positive-0"]), metadata)
    slide.save(args.output / "slide.fixture.npz")
    saved = Slide.load(args.output / "slide.fixture.npz")
    report = analyze_fragment_dependence(
        saved.feats, saved.coords, fixture_scorer, tile_step=saved.metadata["tile_step"],
        tile_size=saved.metadata["tile_size"], coordinate_units=saved.metadata["coordinate_units"],
        microns_per_unit=saved.metadata["microns_per_unit"], source_kind="fixture",
        scorer_id="artificial-max-positive-v1-threshold-0.5", tile_ids=saved.tile_ids,
        alert_policy={"max_area_mm2": 2., "min_isolation_mm": 0.5})
    write_json(args.output / "alert.fixture.json", report)
    print(f"Fixture only: {report['piece_count']} pieces, {len(report['alerts'])} review alert; {args.output}")
    return report


if __name__ == "__main__":
    main()
