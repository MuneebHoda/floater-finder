# Fresh Radboud60 baseline validation

**Execution update:** the separately approved Delta-only intake, CONCH encoding and frozen baseline evaluation are complete: 60 slides / 25,915 verified 512D embeddings. See the [fresh results and exact denominators](../reports/panda_fresh_baseline_results_v1.md) and [CPU intake record](../reports/panda_fresh_cpu_execution_v1.md). Both frozen primaries and all parameters remain unchanged; no original final-test prediction was computed. The preparation record below is historical.

## Historical preparation record — before acquisition approval

The next study checks whether the already frozen CONCH prediction models transfer
to new slides. It does not validate the failed floater detector or release the
original final test. No fresh image, mask or embedding has been acquired, opened
or scored during this preparation. No jobs have been submitted.

## Fixed cohort and models

The existing outcome-blind candidate manifest is unchanged: 20 benign, 20 GG1,
20 ISUP4–5 Radboud slides, excluding all 129 exposed slide IDs. Patient identities
are unavailable, so slide disjointness is verified and patient independence is
unknown. Selection prioritized catalog masks, not mask contents or predictions.
Sixty catalog masks do not establish usable/aligned annotations.

Both task primaries remain the training-only nested-CV selections
`linear_mean_max_topk`, even though the cancer primary underperformed historical
top-5% scoring on repeatedly inspected calibration. Do not switch the primary
using fresh outcomes. The only comparators are historical CONCH cancer top-5%
and low/high mean scoring, using the exact corrected float32 adapters. The
protocol pins all four JSON/NPZ hashes, full checkpoint/preprocessing identity,
text fingerprint and prompt hash. No fitting, calibration, new model or threshold
selection occurs. CONCH remains the sole encoder.

Cancer classification includes all 60 slides; low/high includes only the 40
ISUP1 versus ISUP4–5 slides. Benign slides and absent ISUP2/3 cases are not silently
treated as low-grade cancer. Report all raw predictions, class support/confusion,
recall with Wilson intervals, balanced accuracy with a 2,000-replicate stratified
unique-slide bootstrap (seed20261024), and descriptive uncalibrated probability
diagnostics for the two linear models. These are nonclinical performance
estimates; patient independence, full grade-range validity and clinical utility
remain unverified. Do not interpret bootstrap intervals as including training
or selection uncertainty.

## Compatible inputs and strict execution gate

The old tiler accepts `train/calibration/test/engineering`; it rejects the
metadata planner's `fresh_development_validation` tag. A derived execution
manifest keeps every selected slide/label and the original tag in
`candidate_split` and `validation_role`, and uses **engineering** solely as the
legacy adapter's transport tag. Its exact manifest hash and 60-ID whitelist bind
every evaluation input. It is not a training set. The historical tiler, existing
train/calibration loader and all frozen legacy files are unchanged.

Clean tiling keeps 112-µm requested FOV, 224-pixel saved exports, 512 tiles/slide,
20,000 candidate cells, RGB tissue fraction 0.1 and seed 20261020. The existing
canonical CONCH preprocessing still applies during separately approved encoding.
Mask fractions never enter prediction or clean sampling.

The fresh loader checks membership/exclusion lists before opening arrays; verifies
the embedding/tiling receipts, source metadata, prompt/text/model fingerprints,
coordinates, tile IDs, original grades, physical units and unbiased sampling;
and rejects original test IDs, enriched/injected bags, incomplete receipts and
corrupt artifacts. All 60 sources must pass **before the first prediction**. A
technical shortfall stops v1 with no silent replacement/exclusion. Record failures;
any necessary intake amendment must be explicit and frozen before predictions,
preserving v1 and every unusable case. Missing/corrupt masks may require an
explicit SHA-bound mask exclusion while retaining the image and unbiased sample;
do not fabricate annotation coverage or automatically drop the slide.

The default CLI only verifies fixed metadata/models and never calls a predictor.
Actual clean validation requires `--execute-fresh`, CPU Slurm and a new output
directory. Fresh results cannot authorize a floater policy or the rejected final
job. The 24 original final-test predictions stay sealed.

## Reviewable acquisition and CPU scope

The frozen [acquisition plan](../configs/panda_fresh_baseline_v1/acquisition.json)
contains exactly 60 images plus 60 masks, totaling **1,348,184,402 catalog TIFF
bytes** (about 1.35 GB). Transfer packaging/wire bytes and network duration are
unmeasured. Kaggle terms/access and live download availability are not checked
by reading credential files or authenticating in this preparation.

| Stage | Exact bound | Gate |
| --- | --- | --- |
| Selective acquisition | 1 CPU Slurm job; 2 CPUs, 4 GB, 1 hour maximum; at most 2 allocated CPU-hours | Explicit exact-plan approval |
| Reader/mask audit and representative tiling | Six serialized ten-slide CPU chunks, 2 CPUs, 8 GB, 15 minutes each; at most 3 CPU-hours total | Acquisition integrity, then inspect the first chunk before the remaining five; preserve failures |
| Future CONCH encoding | At most 30,720 tiles, one A100, 4 CPUs, 16 GB, 30 minutes (0.5 GPU-hour) proposal | Actual CPU artifacts/tile counts verified, then separate explicit GPU approval |
| Future clean prediction | 2 CPUs, 8 GB, 20 minutes; all 60 verified embeddings | Frozen protocol/input verification and approved execution scope |

The immediate approval request is **acquisition plus bounded CPU input validation/
tiling only**, at most five allocated CPU-hours in requested wall-time caps.
It includes no GPU job, checkpoint/data expansion, contamination draw or final
prediction. Expected working storage is about 10 GB, an estimate rather than a
quota. The first tiling chunk profiles real costs and stops on incompatibility.
CPU QoS allows one submitted job per user; do not submit arrays/duplicates.

At the bounded Delta recheck, all 120 proposed paths were absent; the acquisition
and CPU interpreter paths existed, the user's queue was empty and
`cpu-interactive` was up with a one-hour limit. Site balances were 5,425 rounded
CPU hours /8 GPU hours, shared snapshots rather than reservations. Approximately
4.03 TB filesystem space was available, also shared. No WSI or mask was opened.

Authoritative existing data root: `/work/nvme/bfqi/mhoda/panda/`.
New intended acquisition receipts:
`/work/nvme/bfqi/mhoda/panda/acquisition-receipts/fresh-radboud60-v1/`.
New intended downstream output root:
`/work/nvme/bfqi/mhoda/floater-finder/panda-fresh-baseline/radboud60-v1/`.
These new output paths are proposals, not claims that data artifacts exist there.

Exact staged source path, full acquisition command and six CPU chunk commands
are in the [preparation receipt](../reports/panda_fresh_baseline_preparation_v1.json).
Source `bfd4416936d2c35d764d6fd46e1017f110ef48db` verified all 226 staged files;
the Delta metadata/model preflight passed without predictions. Submit
only after scope approval; do not use this draft as an automatic job chain.

## Frozen files, software checks and next command

- Candidate SHA256: `30bf03fe9eb09b88a9b8b30db792ec0c5ff437fd8c49240d65124fa3f65f81ea`.
- Execution manifest: `037d177732e8d0ada30992ef50d896e9e5926f0b9ec755f6cde6debfeebe5427`.
- Acquisition plan: `be3ce5829ade783e6c37abb585edb0c3d0c1f9189860b16ecc40ef0b0ecd1eb8`.
- Protocol: `d06827fe964cc7bb14f9cd7403759fd6c106e9f3c41707bd5855f48bb4a30da4`.

All **284 software tests pass** with warnings treated as errors, after rebuilding
the installed package to match edited source. Artificial checks cover metadata-
only preflight, exact acquisition membership/bytes, physical/sampling/label
provenance, original-test exclusion before I/O, changed/corrupt artifacts,
incomplete receipts, grade denominators, explicit CPU execution and output
preservation. These do not establish real reader/encoding compatibility or fresh
scientific performance. The default local preflight verifies 60 IDs/four models/
129 exclusions and computes no predictions.

Read-only next command:

```sh
PYTHONPATH=src .venv/bin/python scripts/panda_fresh_baseline.py \
  --protocol configs/panda_fresh_baseline_v1/protocol.json \
  --protocol-sha256 d06827fe964cc7bb14f9cd7403759fd6c106e9f3c41707bd5855f48bb4a30da4
```

The same preparation can be reproduced into a fresh output directory:

```sh
PYTHONPATH=src .venv/bin/python scripts/panda_fresh_baseline_prepare.py \
  --train /tmp/floater-fresh-validation-metadata/train.csv \
  --catalog /tmp/floater-fresh-validation-metadata/official_catalog-20261020-paced.json \
  --pilot /tmp/floater-fresh-validation-metadata/pilot.csv \
  --output results/panda/fresh-baseline-preparation-reproduction
```

The metadata source paths/hashes are preserved in the earlier proposal. No
credentials are requested or recorded. `AGENTS.md` explicitly requires approval
for new downloads/GPU scope; the already completed 120-slide approval is not reused
for these new candidates.
