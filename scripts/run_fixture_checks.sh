#!/bin/bash
# Local artificial-array integration check. Does not connect to NCSA or encode images.
set -euo pipefail
if [ "$#" -ne 1 ]; then
    printf 'Usage: bash scripts/run_fixture_checks.sh NEW_OUTPUT_DIRECTORY\n' >&2
    exit 2
fi
FLOATER_RUN_DIR=$1
FLOATER_BIN=.venv/bin/floater-finder
if [ -e "$FLOATER_RUN_DIR" ]; then
    printf 'Choose a new output directory; existing work is preserved.\n' >&2
    exit 2
fi
"$FLOATER_BIN" fixture --output "$FLOATER_RUN_DIR/inputs"
"$FLOATER_BIN" validate --slide "$FLOATER_RUN_DIR/inputs/host.npz" --text "$FLOATER_RUN_DIR/inputs/text.npz"
"$FLOATER_BIN" score --slide "$FLOATER_RUN_DIR/inputs/host.npz" --text "$FLOATER_RUN_DIR/inputs/text.npz" --output "$FLOATER_RUN_DIR/clean_scores.json"
"$FLOATER_BIN" stress --config "$FLOATER_RUN_DIR/inputs/run.yaml" --output "$FLOATER_RUN_DIR/stress"
"$FLOATER_BIN" inject --host "$FLOATER_RUN_DIR/inputs/host.npz" --donor "$FLOATER_RUN_DIR/inputs/donor.npz" --percent 5 --seed 7 --output "$FLOATER_RUN_DIR/mixed.npz"
"$FLOATER_BIN" oracle --slide "$FLOATER_RUN_DIR/mixed.npz" --original "$FLOATER_RUN_DIR/inputs/host.npz" --text "$FLOATER_RUN_DIR/inputs/text.npz" --output "$FLOATER_RUN_DIR/restored.npz"
"$FLOATER_BIN" calibrate --slides "$FLOATER_RUN_DIR/inputs/dev.npz" --text "$FLOATER_RUN_DIR/inputs/text.npz" --output "$FLOATER_RUN_DIR/calibration.json"
"$FLOATER_BIN" detect --slide "$FLOATER_RUN_DIR/mixed.npz" --text "$FLOATER_RUN_DIR/inputs/text.npz" --calibration "$FLOATER_RUN_DIR/calibration.json" --output "$FLOATER_RUN_DIR/detection"
"$FLOATER_BIN" detect --slide "$FLOATER_RUN_DIR/inputs/clean_eval.npz" --text "$FLOATER_RUN_DIR/inputs/text.npz" --calibration "$FLOATER_RUN_DIR/calibration.json" --output "$FLOATER_RUN_DIR/clean_control"
"$FLOATER_BIN" summarize --run "$FLOATER_RUN_DIR/stress" --output "$FLOATER_RUN_DIR/recomputed_summary.json"
