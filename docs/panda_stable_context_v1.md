# Fixed-support review candidate v1

This **new training-only candidate**, not a revision of a historical result,
tests whether fixed comparison support and repeatable anomaly evidence improve
the failed full-context rule. Prior topology work found sparse-context sensitivity;
that motivates the design but does not establish that it will work. No real
candidate outcome is known at source freeze. Human review remains separate.

## Frozen feature and candidate rule

Use all 72 original training slides and exactly the 24 saved S1 **5%-dose** cases:
24 distinct benign host slides /16 reused cancer donor slides, 389 clean and
167 mixture RGB components (556 total). No new contamination draw, component
segmentation, WSI, PNG, mask or encoder operation. Retain all unavailable and
low-mapping cases in denominators. Missing RGB assignments remain unknown;
unassigned saved tiles remain in outside context, without guessed boundaries.

For each original component, abstain if it exceeds half the sampled bag or has
fewer than **32 outside tiles**. This concerns tile occupancy, not actual biopsy
area. Otherwise take 32 outside indices from each seeded permutation, under
seeds **20261026/27/28**. Keep candidate vectors fixed, sort each reference subset,
and use the unchanged robust NN5 implementation. The primary score is the
**minimum of the three** scores: an anomaly must persist under every sampled
context. Duplicate subsets are recorded and are not three independent observations.
Maximum 556 x3 =1,668 feature estimates; ineligible components have no invented score.

The feature function accepts only image vectors, recorded coordinates and component
indices. Annotation, source identities, disease scores, foreign truth and donor
labels cannot select the context or enter the anomaly score. Original S1 donors
were annotation-selected, which limits the treatment/evaluation design. Thirty-two
references and three-seed consensus are fixed engineering choices, not validated
biological reference rules. Genuine rare cancer may still look anomalous.

Compare **stable32_min3 (fixed primary)** with **matched_full_context**, which
reuses the old cached robust-NN5 score under identical eligibility/fold rules.
The comparator is not the historical v3 operating point: new eligibility and
source-disjoint folds change its estimation conditions. No post-outcome primary
switch, threshold relaxation, hyperparameter sweep or additional encoder/model.

## Source-disjoint cross-fitting and metrics

Form source-connected groups from each host and its actual donor, including all
reused-donor relationships. Other training slides form singleton groups. Assign
groups to five folds with the unchanged hash-order assignment and seed 20261022.
Both the held host and donor are excluded from clean threshold-fitting inputs.
Source IDs define study partition/provenance only, never detector features.
These are slide-source groups, not verified independent patients.

For each method/fold fit the strict `score > threshold` cutoff using **clean fitting
slides only**, retaining the existing targets: at most **10% alerted slides** and
**0.5 components/slide**. Low mapping (<0.9) abstains. Held-fold burdens and safety
are measured independently of fitting-fold target compliance. Visual shortlisting
precedes explanation of frozen prediction dependence; influence does not veto it.
No tissue is automatically removed.

Use the historical cached **CONCH v1 zero-shot benign/cancer top5pct** scores and
counterfactual explanations, not a retrospectively chosen classifier. Hypothetical
multi-component filtering pools saved tile scores; it is new diagnostic pooling,
**not new CONCH/model inference**. Record initial errors, prediction changes,
induced errors, donor/native tiles shortlisted, genuine cancer flags, unmodified
burden, empty exclusions and clean-prediction damage separately.

Separate any label return from **source-exact error recovery**: all appended donor
tiles must be shortlisted, no native host tile shortlisted, and the originally
correct host label restored. Removing a genuine host carrier while retaining
foreign tissue is never called recovery under this criterion. Saved exact-oracle
receipts must pass; a failure stops the run, preserves partial output and permits
no automatic retry. Receipts are checked, not reexecuted full oracle experiments.

The prespecified **training-candidate gate** requires all observed burden targets,
genuine annotated-cancer slide flag rate <=10%, clean-prediction damage <=5%,
fragment recall >=20% and source-exact induced-error recovery >=25%. Zero relevant
denominators fail. These are engineering selection targets, not clinical guarantees.
Even passing this gate leaves **independent validation and final readiness false**.
Human response forms are not filled by this program.

Report exact case/unique-slide/source-group denominators. Positive intervals use
2,000 donor-slide cluster resamples; clean-alert intervals use source-connected
groups. Seeds and folds are fixed, and intervals condition on fitted thresholds
and existing outcomes; they omit refitting/selection uncertainty and do not prove
population performance. Zero observed events can yield degenerate intervals.
Also report the clean-alert Wilson interval. Unknown patient identities and
synthetic disease differences constrain every generalization claim.

## Scope, freeze and execution

Protocol `configs/panda_stable_context_v1.json`, SHA256:

`bb92f57b73190cf207e32248720b7f963c742086942c7186b6a76d3540b093ae`.

Seven hash-bound inputs: manifest, directory index, original embedding verification,
saved case catalog, full-context feature cache/completion and original S1 trials.
Trials must match the already committed historical file. The strict loader resolves
training IDs before opening arrays; no final/calibration/fresh60 array is opened.
All 72 sources, original annotations/order and model/embedding identities must match.
Synthetic vectors are assembled using only saved donor indices/translation, with
original-source validation; no new draw or changed placement. Source identities
and input receipts are rechecked before sealing.

One planned CPU job: verified **bfqi-delta-cpu account/QoS /cpu-interactive**,
**2 CPUs, 8 GB, ten-minute cap, zero GPUs**, at most 0.333 allocated CPU-hours.
Exact source snapshot, command, current partition/queue and output absence must
verify before the single submission. No duplicate/retry, new model, weights,
dataset download, new GPU encoding, or original final-test job is included.
Latest user “So do that to” advances remaining technical validation; resource
values are agent-selected within the bounded existing-CONCH CPU research scope.

Intended new output, not a claim it exists:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review/stable-context-v1`

Expected: a sealed registry, 96 case feature checkpoints, summary containing both
methods/folds/metrics/explanations, event chain and source provenance. All vectors,
reference indices, detailed metrics and outputs stay on Delta; no local downloads.
Original 120/fresh60 artifacts, TCGA results, human worksheet and final-test seal
are preserved. The rejected final protocol is neither edited nor bypassed.

All **416 tests pass** with warnings as errors (18.86s), including eight new tests
with a complete artificial 72-clean/24-mixture run and oracle-failure preservation.
An initial artificial 512-dimensional repeated-vector fixture triggered a local
NumPy matmul warning; the fixture was reduced to two mathematical dimensions,
without changing production code or suppressing warnings. Fixtures never supply
PANDA performance evidence. All six previous runtime freezes, main and 33 legacy
source hashes remain intact.

Real execution is **unsubmitted**: the single shared-connection test returned
`Permission denied`; no retry was made. The user must reconnect privately with
`ssh ncsa-floater` and confirm before remote staging/inspection/submission resumes.
Actual expert review is pending, and no scientific outcome is claimed here.

Source-only preflight:

```sh
python scripts/panda_stable_context.py --config configs/panda_stable_context_v1.json \
  --config-sha256 bb92f57b73190cf207e32248720b7f963c742086942c7186b6a76d3540b093ae
```

`--check-inputs` adds remote metadata checks; arrays/measurements require the bounded
Slurm wrapper and explicit `--execute`. Exact staged command remains pending a
successful, user-confirmed reconnection. Do not interpret software tests or this
preparation document as measured detector success or permission to unseal final data.
