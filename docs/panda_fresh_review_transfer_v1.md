# S3 conservative visual-rule transfer — preparation

This development diagnostic reuses the completed S1 registry from CPU 23083320.
It measures new review outcomes on exactly **140 saved bags**: 60 unmodified
slides and the 80 fixed 5%/first-seed append/replacement foreign/sham bags.
No new contamination draw, acquisition, tiling, embedding, baseline experiment,
component rule or model fitting is planned. Data and raw results stay on Delta.
The original 24 final-test slides remain sealed.

## Frozen comparison

The visual signal is the existing CONCH `robust_nn5` within-slide morphology
score, with its fixed 0.01 MAD floor. Require strict agreement with all five
original training-clean fold thresholds. Their values are
8.268793622836606, 9.32818765238456, 7.99559233897009,
8.268856228155098 and 8.268856228155098; therefore the transferred threshold is
**score >9.32818765238456**. All fitting/held fold IDs must be disjoint from the
60 evaluated study IDs. No fresh visual outcome selects this aggregation or
changes the threshold. A missing fold threshold causes abstention.

This is a **new conservative transfer aggregation**, not a newly calibrated or
previously validated operating point. The earlier thresholds used RGB-derived
pieces; the saved S1 pieces use 8-neighbor sampled occupied cells without gaps.
The old burden calibration therefore does not transfer automatically. More
permissive thresholds are not searched if this rule fails. Existing v1/v2/v3
negative evidence remains unchanged.

Both unchanged cancer scorers are evaluated. The training-selected linear
scorer remains primary; the exact historical top-5% scorer remains a comparator.
The fixed primary review comparison is `combined`:

| Policy | Review flags |
| --- | --- |
| `visual` | Evaluable components above every old visual threshold |
| `dependence` | Evaluable components whose saved exclusion changes the prediction |
| `combined` | Intersection of the preceding two rules |
| `random_matched` | Uniform random evaluable components, with the same count as combined in each bag |

The random control has 32 fixed draws (seed 20261025 plus a case/draw hash).
Those draws are repeated controls, not new slides or patients. They match
component-count burden, not physical area, tissue identity or biological realism.
Physical occupied area, isolation, signed cancer influence, decision change and
preserve-tissue explanations accompany each candidate. No new size/isolation
cutoffs are picked from the known cancer-control results. A review flag never
asserts foreignness, recommends deletion or changes a saved tissue artifact.

## Input and truth boundary

The fixed protocol is `configs/panda_fresh_review_transfer_v1.json`. It pins the
old threshold report, prior S1 protocol, all new source paths, and the sealed
S1 run/summary/seal hashes. Execution verifies every source-registry artifact,
loads only the strict 60-slide whitelist and matches original input identities.
Edited bags are reconstructed using the saved shared-engine specs and must
match their exact result audit and retained-state restoration identity.

The original saved component memberships, tile IDs, physical geometry and
empty-exclusion states are verified, never inferred afresh. Visual features
receive image vectors and geometry. Grades, annotations, synthetic truth and
source/altered indices do not enter anomaly scoring or flag selection. Evaluation
joins those fields only afterward. Both saved scorer baselines must match the
sealed clean/trial records before review. Cached baseline and one-component
counterfactual predictions are reused; only genuinely new multi-component
hypothetical filtering invokes a frozen scorer. Arrays and files are preserved.

Report foreign-tile hits/recall, any-overlap and complete-fragment hits, unique
hosts/donors, unmodified review rate, components per slide, abstentions, native
tiles and genuine annotated-cancer components flagged, hypothetical clean damage,
and recovery of induced original-host-label errors among originally correct
hosts. The inserted-cancer response is a different diagnostic target. Replacement
flags refer to native carriers and can remove additional native evidence; they
are not verified donor boundaries or isolated fragment removal.

Burden targets remain <=10% unmodified-slide flags and <=0.5 components per
slide. All 60 unmodified slides remain in denominators, including the 17 known
single-component abstentions. Report genuine-cancer harm even when burden targets
are met. Grouped bootstrap uncertainty uses 2000 unique-host resamples, keeping
repeated bags and all random draws together, conditional on fixed donors and
policy. Shared donors and unknown patient identity limit inference. No automatic
operating-point approval or original final-test readiness follows from these data.

## Bounded execution scope

One proposed CPU job: `bfqi-delta-cpu` account/QoS, `cpu-interactive`, 2 CPUs,
8 GB and 20 minutes, zero GPUs; maximum 0.667 allocated CPU-hours. It produces
at most 9800 model/policy records (140 bags x 2 scorers x [3 fixed policies + 32
random draws]), an upper bound on new filtered predictions; many reuse cached
predictions or need no new score. Runtime is unmeasured. There are no dataset,
weight or local downloads, no WSI/PNG reads, no refitting or threshold selection.

Intended output, not a claim of executed results:

`/work/nvme/bfqi/mhoda/floater-finder/panda-fresh-baseline/radboud60-v1/fresh-review-transfer-v1`

Expected sealed outputs: `run.json`, `events/`, per-bag `checkpoints/review-*.json`
with visual scores, physical/explanatory metadata and policy-specific evaluation,
`checkpoints/summary.json` with denominator/uncertainty ledgers, and `seal.json`.
Any source/identity/oracle-state mismatch stops and preserves the failure; no
automatic retry or overwritten output. The completed S1 approval is not reused.
The latest user request to push and advance authorizes this bounded next
CPU development stage under the existing research plan; it is not an explicit
user choice of these resource values and does not reuse the consumed S1 approval.
The exact new source/command is recorded after staging, before submission.
All 306 software tests pass with warnings as errors in a clean offline
environment; nine new tests use artificial arrays. Bash syntax and the original
protocol/main/33 legacy source guards pass. No dependency was added.

Default local preflight opens no slide arrays and makes no predictions:

```sh
python scripts/panda_fresh_review.py --config configs/panda_fresh_review_transfer_v1.json \
  --config-sha256 f6c27f854187978ec5d2cb2e889adb8279b618d1a98c1d03cb370494109f68e9
```

`--check-inputs` additionally checks small remote receipts/output absence.
`--execute` requires the exact output/source identity and an approved CPU Slurm
allocation. Local tests use artificial arrays only; no real S3 outcomes have
been computed during preparation.
