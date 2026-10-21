# Numeric-context eligibility and native-control accounting v1

This new development candidate follows the completed topology/context audit.
It consumes **only its sealed JSON for the original 72 training slides**; it does
not repeat image segmentation, feature extraction, ablations, classifier calls or
previous contamination experiments. The original 24 final-test predictions remain
sealed. The evaluated fresh 60 and known calibration are outside this stage.

## Contract and interpretation

`detectors.context_eligibility.assess_context(candidate_tiles, total_tiles,
diagnostic_score)` accepts no labels, annotations, source identity or synthetic
truth. It validates saved robust-NN5 score availability and returns structured
numeric eligibility and explicit reasons. Abstain from numeric comparison when:

- Fewer than six saved tiles remain outside the candidate. Both NN5 operations
  need this support; this is not an empirical stability threshold.
- The candidate occupies more than half of the saved tile bag. This is a new
  conservative engineering veto, proposed after inspecting the previous training
  audit, frozen before this accounting. Exactly half is allowed. It is not a
  calibrated physical-area cutoff or a clinical guarantee.

An abstention retains the original diagnostic score but exposes no comparison
score. Passing the gate means only `supported_numeric_comparison`; it does not
prove sufficient biological context. **Every result abstains from a review/foreignness
decision**: `review_alert=null`, `foreignness=null`, `automatic_tissue_action=none`.
Null is not a negative alert or benign diagnosis. Historical detectors are unchanged;
this new contract is not retroactively substituted into their reports.

Both existing topology proxies are measured separately, without selecting or
repairing either. Unassigned RGB tiles in candidate/reference are retained as
unknown. Physical boundaries and score stability remain unverified. Occupied
footprints and observed RGB area stay separate; sampled occupancy is not actual
biopsy extent. No new score cutoff, mapping coverage cutoff, isolation threshold,
majority tuning, or reference-size sweep is performed.

Native annotation counts join **after gate construction**. Report counts and
unique slide IDs for all components, NN5 support alone, conservative eligibility,
and abstentions. Report genuine annotation-positive and unknown controls,
overlapping abstention reasons, slides without an eligible comparison, and the
number of eligible components using unmapped context. A genuine cancer-containing
component may remain eligible. Eligibility is not an alert; these counts are not
false-alert rate, recall or tissue harm. Those metrics remain null because no
review policy or classifier action runs. Different component regroupings are not
new patients, and patient independence remains unverified.

## Frozen execution

Protocol: `configs/panda_context_safety_v1.json`.
SHA256: `9e8a75b0d0a9eb244e840850dd03b6cfb8aa742dec6770b6c9078f9bd5d92871`.
Source files, original protocol, manifest, old run/summary/seal are hash-bound.
The reader verifies all checkpoint hashes and the complete event chain without
opening the old registry writer lock. It checks exact training membership before
reading any slide JSON, and rechecks the old registry before sealing new output.
No NPZ, WSI, PNG, TIFF, model weights or patient-level final labels are read.

Verified new output, created by job 23102229:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review/context-safety-v1`

One CPU Slurm job on account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`:
**2 CPUs, 4 GB, five-minute maximum, zero GPUs**; cap 0.167 allocated CPU-hours.
Use the existing prepared CPU runtime. Latest user “next” supplies this bounded
new development direction; resources are agent-selected, not expressly selected
by the user. Show the immutable source and exact command before submission.
No retry or duplicate, GPU, acquisition, threshold fitting, new model or final test.

All **336 tests pass** with warnings as errors (30.99s), including 21 new
artificial-fixture checks. Fixtures are software evidence only. Raw outputs remain on Delta;
local notes may record bounded aggregates. No data/result files are downloaded.

Metadata-only local preflight:

```sh
python scripts/panda_context_safety.py --config configs/panda_context_safety_v1.json \
  --config-sha256 9e8a75b0d0a9eb244e840850dd03b6cfb8aa742dec6770b6c9078f9bd5d92871
```

`--check-inputs` adds remote metadata hash/destination checks. Execution requires
`--execute` inside the frozen CPU wrapper. Exact staged source/command and measured
results will be appended only after they exist.


## Verified staging and submission

Source `0340d605acd6bee8ea913d09307a326750cb1a5c` was pushed and separately staged at:

`/u/mhoda/floater-finder/releases/panda-context-safety-v1-20261021T170007Z/source`

All 253 source files, four input receipts, original protocol and 33 legacy
source hashes verified. Queue empty and output absent before submission.
Archive SHA256 `421ab1841fb2a6833680ff77276d6ce06230259510cdac4d2939905abc439cdb`;
source-manifest SHA256 `ed17998c4167c53d491522b038fa8abaa6a12363e541e98aec8a8cb291abbd69`.

Submitted once as **23102229** with the exact command:

```sh
sbatch --parsable /u/mhoda/floater-finder/releases/panda-context-safety-v1-20261021T170007Z/source/scripts/slurm/panda_context_safety.sbatch /u/mhoda/floater-finder/releases/panda-context-safety-v1-20261021T170007Z/source /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z 9e8a75b0d0a9eb244e840850dd03b6cfb8aa742dec6770b6c9078f9bd5d92871 /work/nvme/bfqi/mhoda/floater-finder/panda-review/context-safety-v1 0340d605acd6bee8ea913d09307a326750cb1a5c
```

Authorization receipt SHA256 `3baf39581f5032081388e6441ef42cd941446f55f9d2b7bd54a24ae786a9aaa1`.
Resource values were selected by the agent within the latest bounded-development
direction, not explicitly chosen by the user. No previous consumed job approval
was reused. Job **23102229 completed 0:0 in 12 seconds**, with 73 checkpoints /76 events
verified. [Coverage, native controls and unresolved limitations](../reports/panda_context_safety_results_v1.md).
The numeric gate does not validate foreignness; all review decisions remain null.
This bounded development scope is complete; no further job was submitted.
