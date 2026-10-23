# PANDA review-policy evaluation v1 — development only

**No useful operating point was found among the 81 preregistered candidates.** The selected combined rule meets the burden/harm targets but detects 5/120 training fragments and 0/40 calibration fragments. The frozen protocol records this rejection and blocks final predictions. All 24 final-test slides remain unscored. No previous acquisition, tiling, GPU encoding or S1 draws were repeated.

## Scientific audit and denominators

The [audit of commit 434b401](panda_scientific_audit_v1.md) confirms 120 real Radboud slides, 50,729 saved CONCH v1 embeddings, 72 training / 24 calibration / 24 test slides. Patient identifiers are unavailable: distinct slides and disjoint slide splits do **not** establish different patients.

The frozen benign/cancer top-5% scorer's existing calibration confusion is `[[5,3],[1,15]]` (truth rows benign/cancer): accuracy 20/24, balanced accuracy 78.125%. These are development observations, not independent test performance. The 192 original S1 trials are 32 benign hosts × six doses, including zero. Their 21 donor slides are reused; only 53 source slides are distinct. Native annotated cancer is synthetically inserted, not evidence of actual foreign tissue.

For calibration top-5% S1, eight benign hosts include **five originally correct and three initially incorrect**. At 0.5/1/2/5/10% requested foreign/original-host tile counts, newly induced cancer errors are **1/5, 1/5, 2/5, 2/5, 2/5**. These eight error instances affect two unique hosts. Initially incorrect hosts that remain cancer are not new errors. Prediction changes, initial-error reversals and induced errors have separate transition tables in the audit. All 192 original exact-oracle recoveries pass; oracle success validates plumbing, not a detector.

The old piece diagnostic's 7/18 evaluable clean decision dependencies exclude six empty-counterfactual cases. That number is not an alert rate. A sampled component with 435/512 tiles and 0.171 mm² native annotated cancer legitimately changes cancer to benign when excluded; its sampled footprint is 5.439 mm². A known injected three-tile component (0.0375 mm² footprint) also changes cancer to benign. Neither example alone establishes a foreignness rule. [Preserved examples and charts](panda_s1_and_piece_results_20261020.md).

## Candidate policy and comparison

The [development specification](../docs/panda_review_development_v1.md) was committed before the new measurements. Visual inconsistency is median component-tile distance to up to five nearest outside-component CONCH neighbors. Influence is the signed decrease in the frozen cancer-minus-benign margin under exclusion. The combined rule also requires observed RGB component area and bbox-isolation evidence. Native annotation and injection truth enter evaluation only, not review features or component construction. All tissue and original predictions are retained.

Training alone selected visual distance **>0.24603846669197083**, margin influence **≥0.01**, observed area **≤0.25 mm²**, bbox isolation lower bound **≥0 mm**. The selected isolation constraint provides no positive minimum-separation requirement. The 81-point grid varied visual quantile, influence, maximum area and minimum gap; even the best training fragment recall anywhere in that grid was only 5/120. Calibration validated one selected point, with no runner-up or threshold relaxation after failure.

User-confirmed development targets were ≤10% unmodified-slide alerts and ≤0.5 flagged components/slide. Predeclared additional engineering targets were ≤10% annotation-positive cancer slides with a genuine-cancer component flagged, ≤5% damage among originally correct clean predictions, ≥20% fragment recall and ≥25% induced-error recovery on both training and calibration. These are research selection targets, not clinical guarantees.

Calibration results from [saved measurements](panda_review_selection_v1.json):

| Rule | Unmodified slides alerted | Mean components/slide | Foreign tiles flagged | Fragments hit | Complete fragments | New errors recovered | Genuine cancer components flagged | Hypothetical clean damage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Combined | 0/24 | 0 | 0/607 | 0/40 | 0/40 | 0/8 | 0/26 | 0/20 |
| Visual only | 0/24 | 0 | 0/607 | 0/40 | 0/40 | 0/8 | 0/26 | 0/20 |
| Decision only | 4/24 | 0.167 | 153/607 | 8/40 | 8/40 | 8/8 | 1/26 | 3/20 |
| Spatial only | 19/24 | 3.583 | 277/607 | 32/40 | 29/40 | 6/8 | 4/26 | 0/20 |

“Fragment hit” means at least one known injected tile is flagged; complete-fragment recall requires all injected tiles. The 40 positive-dose mixtures reuse eight hosts and nested fragments, not 40 independent slides. Genuine-cancer controls cover 26 evaluable annotated components on 15 unmodified calibration slides; one other cancer slide has an unavailable/corrupt mask and remains unknown. Decision-only flags one of these 15 slides; spatial-only flags three. Genuine-cancer slide grades are never substituted for per-tile annotations.

Training combined results are 0/72 clean alerts, 5/120 fragment hits, 4/38 induced-error recoveries, 0/61 clean damage and 0/88 genuine-cancer components flagged (87 of 88 are counterfactually evaluable). Decision-only flags 23/72 clean slides and damages 19/61 originally correct clean predictions. [All per-case measurements](panda_review_metrics_by_case_v1.json) retain abstentions, raw predictions, component indices and initial-correctness denominators.

Twenty size/burden-matched random controls use fixed seed 20261021 and are repeated draws rather than independent observations. On training, their mean fragment recall is 2.71% versus combined 4.17%, and mean induced-error recovery is 7.5% versus combined 10.53%; these are descriptive repeated-draw comparisons, not a superiority claim. Two of the five primary component selections have no alternate size-bin match. Since the combined rule flags nothing on calibration, its matched controls also flag nothing: this comparison is **uninformative**, not evidence that the combined rule beats chance.

A descriptive failure funnel uses injection truth only to locate misses. All 40 calibration mixtures have an evaluable mapped component overlapping injected tiles. Five pass the combined visual threshold; none also pass its influence threshold. Training counts are 120 mapped →16 visual →5 visual-plus-influence →5 combined. This diagnoses the observed failure without changing the policy.

## Topology investigation

The new proxy uses observed factor-16 RGB foreground (`min RGB<220`, chroma>10), eight-connectivity, no closing, dilation or gap bridging. Saved tiles map only with ≥80% component purity and ≥10% observed foreground coverage. Unassigned tiles remain in counterfactuals; <90% mapped tiles triggers review abstention. Synthetic mixtures project actual saved donor RGB foreground using the existing physical translation and recompute connectivity, without using injection truth for segmentation.

Across 96 development slides, mean mapping is 98.15%, minimum 76%. Two training slides abstain; no calibration slide abstains (minimum calibration mapping 96.27%). Old sampled-cell single-component cases decrease **28→8 training and 6→2 calibration**; specifically four formerly single-component calibration slides now map to multiple observed components. A single observed component still has an empty exclusion and remains unevaluable.

The preregistered lenient RGB sensitivity check yields mean pair-membership agreement 96.25% training / 98.47% calibration, with minima **37.05% / 84.28%**. Some faint tissue and small structures are threshold-sensitive. [Four training RGB quality examples](figures/panda_review_v1_final/topology_quality_checks.png) include worst mapping, worst agreement, largest component-count change and median agreement, selected by quality metrics only. These images were visually inspected. RGB components are not pathologist-confirmed tissue pieces; overview foreground area is approximate and bbox gap is only a lower bound. No missing tissue boundaries were invented.

## Uncertainty and limits

The 0/24 combined clean-alert observation has a Wilson 95% interval **0–13.8%**, so it does not establish a population rate below 10%. Decision-only clean damage 3/20 has interval **5.2–36.0%**. [Diagnostics](panda_review_diagnostics_v1.json) include per-dose Wilson intervals and unique-host bootstrap intervals preserving repeated doses. Conditional bootstrap intervals can collapse to 0 or 1 when every observed event agrees; they do not imply certainty, particularly with only two induced-error hosts. Shared donors, missing patient identities, one seed, synthetic placement, limited masks, representative sampling and an unvalidated zero-shot cancer scorer limit inference. Alerts on unmodified slides are operational controls, not adjudicated true foreignness false positives. No clinical usefulness is established.

## Execution, freeze and next action

New CPU measurement job **23066481** wrote all 96 topology records and 256 clean/mixture case measurements, then failed serializing a NumPy integer in the selection report. The original outputs and empty failed selection file were preserved. A regression-tested fix resumed reporting only from checksum-pinned measurements: job **23066553 completed 0:0 in 17 seconds**. No WSI measurement, embeddings or old S1 experiment was recomputed for that recovery.

[Frozen protocol v1](../configs/panda_frozen_protocol_v1.json) SHA256 `695e2097aa0916bdd03b9b0721fc1f58dd5fda338e9c4975c171d64d2d36c881` pins the rejected thresholds, prompts, cohort, checkpoint fingerprint, topology, statistical plan and final runtime source **cde0e4a257898c6abe93d6a4df6ad52c744f31cc**. The separate Delta source snapshot verified 323 files; source files and protocol are mode 444. Exact executed measurement and reporting commits are recorded separately.

Read-only CPU preflight **23066843 completed 0:0 in 31 seconds**, verified **10,988 files / 24 slides**, and reported `test_labels_decoded=false`, `test_predictions_computed=false`, `ready_for_final_predictions=false`. It hashed label-bearing CSV/JSON/NPZ/WSI/PNG files without decoding them. The cohort manifest already contains acquisition labels; none were used for test-based tuning. The final output directory is absent, the queue was empty at inspection, and no final-test or GPU job was submitted. [Preflight evidence](panda_final_preflight_completed_v1.json).

**The final command is prepared but blocked, and must not be submitted under this rejected protocol.** [Exact command, resource request and outputs](../docs/panda_final_test_v1.md). A future supported development policy requires a new version and independent validation; do not edit this frozen rejection or tune on the 24 test outcomes. For the October 21 presentation, report the verified pipeline, genuine-cancer counterexample, and measured review-policy limitation. [Presentation outline and reproducible figures](panda_presentation_v1.md).

Software verification: **192 tests passed** with warnings treated as errors, including preserved TCGA behavior, exact oracle, label guards, source/input tampering, unsupported-policy refusal and single-execution locking. A temporary synthetic 24-ID fixture exercises the final-runner path; it is software evidence only, never a real held-out result.
