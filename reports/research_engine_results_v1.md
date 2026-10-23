# Shared engine and initial S2 v2 engineering checkpoint

**Observed:** corrected CPU job **23069070** completed 0:0 in **1:56** (task 1:48, 318,016 KiB peak). Source **`de220802f68098fac84119112157ee9078c6c13c`** was committed and staged before these outcomes. Its sealed registry verifies **1,017/1,017 exact recoveries**, **252 exact legacy S1/S2 comparisons**, and **345 coordinate-only prediction invariance checks**. This is a bounded real-input engineering/placement study on **four training hosts**, not independent disease-model or detector validation.

The preceding failure **23069018**, source `ba105d2`, is retained with all six checkpoints in [its failure record](research_engine_failure_23069018.json). It raised a nested-prefix placement-eligibility exception, not an oracle mismatch. Version 3 kept the maximal-fragment translations and distance fixed, explicitly excluded invalid subdose placements and imported the five completed trial checkpoints plus one geometry checkpoint by verified hash. The remaining 1,012 trial checkpoints were newly completed. No old experiment or outcome was overwritten.

## Implemented architecture

[Contracts, public API and acceptance design](../docs/research_engine_v1.md) describe the incremental `floater_finder.research` package: immutable artifact snapshots and experiment contracts; one dose/component/source/physical-compatibility engine; exact legacy adapters; appended, observed-near-tissue, replacement and alternate-context modes; truthful same-source sham labels; exact original-state recovery; and a hash-chained, resumable registry/status command. Historical TCGA/S1/S2 modules and published results remain unchanged. The existing `experiments.py` module is not shadowed.

Original vectors, IDs, coordinates and metadata are restored exactly. Replacement keeps original host positions/IDs and stores original representations for restoration; deleting marked representations cannot recover replaced evidence. Same-source shams have `foreign_mask=False`; audited edit indices/counts remain separate. Native annotations select eligible donors, not predictor inputs.

## Inputs and denominators

The [version 3 configuration](../configs/research_engine_acceptance_v3.json) fixes the first two slide-ID-sorted training hosts per task, two eligible donors per seed/host/condition, three seeds (`20261020`, `20261021`, `20261022`), and requested doses **0, 0.25, 0.5, 1, 2, 5, 10%**. This is 1,344 attempted mode/dose instances. The same connected donor prefix and rigid maximal-fragment placement are retained across doses. Different seeds/donors/doses are repeated measurements, never patients.

- Four unique host slides: two benign S1 hosts and two low-grade S2 hosts.
- Twenty-one unique non-sham donor slides; 24 unique source slides overall. Host/donor roles overlap. Patient-level independence remains unverified.
- 1,017 eligible instances: **192 zero-dose controls, 607 positive-dose non-sham donor instances, and 218 positive-dose same-source shams**.
- S1: 402 eligible instances, including 219 positive non-sham instances; 39 repeated prediction-change instances.
- S2: 615 eligible instances, including 388 positive non-sham instances; **zero prediction changes**.

Dose means foreign/altered tile count divided by the **original** host count, rounded upward to a unique connected tile count. Requested 0.25% realized **0.391–0.488%**; requested 10% realized **10.132–10.244%**. These are tile-representation doses, not directly measured cancer-area percentages. Every raw case retains exact requested/realized dose, source IDs, donor indices/IDs, scores and audited identities.

## Geometry feasibility and invariance

| Mode | Attempted | Eligible | Explicit exclusions |
|---|---:|---:|---:|
| Historical right-edge append | 336 | 336 | 0 |
| Verified near-tissue placement | 336 | 168 | 168 |
| Replacement at existing positions | 336 | 336 | 0 |
| Alternate observed boundary context | 336 | 177 | 159 |

Near/context candidates require a complete verified level-2 RGB foreground overview, measured pixel scale, empty nonoverlapping footprints inside known image bounds, and proximity within 224 µm Chebyshev distance. Sparse sampled-cell vacancies are never treated as proof of emptiness. The **327 exclusions are NA**, not presumed benign or successful predictions. They retain the exact combined occupancy/proximity rejection message; not every rejection was independently diagnosed as a distance failure. One same-grade 10% near candidate was excluded on revalidation after maximal-fragment proposal; numerical/raster-boundary conservatism has not been isolated. RGB-pyramid occupancy is a proxy, not histological boundary proof.

For all **345 eligible near/context cases**, the feature bag and frozen prediction exactly equal the matching appended case. This is the expected property of an order-invariant bag scorer: **coordinates alone cannot change its prediction**. Different aggregate means at lower doses can arise from eligibility exclusions; they do not demonstrate a location effect. Replacement changes the feature bag and can change the prediction. None of these modes is pixel composition or physically embedded histology.

## Initial S2 v2 smoke

The low/high primary was **`linear_mean_max_topk`**, selected by training-only nested-CV balanced accuracy/worst recall/simplicity before contamination. Its portable parameters and `selection_frozen.json` SHA **`acff113f130a6ac1650589009e002eef351787a791ad08a0508d41f869d973e7`** were pinned before any contaminated prediction. The model's training-only OOF result and known-calibration diagnosis are separate predictor evidence; contamination outcomes did not select this scorer.

This smoke uses the final head fit on training slides, including these two hosts: **resubstitution, not independent validation**. Both baseline low-grade hosts are correct, with high-minus-low logits −1.8411 and −2.1828. Across all eligible doses, both high-GP4/5 donor and same-grade-GP3 donor conditions have zero decision changes. The complete S2 v2 cohort has not been run.

At requested 10%, each primary cell has 12 originally correct host/donor/seed instances across two unique hosts. High-GP4/5 uses nine distinct donor slides across repeated seeds; same-grade controls use eight.

| S2 donor condition / mode | New errors / originally correct instances | Mean high-minus-low logit shift |
|---|---:|---:|
| High GP4/5 append | 0/12 | +0.9646 |
| High GP4/5 replacement | 0/12 | +1.0447 |
| Same-grade GP3 append | 0/12 | +0.01034 |
| Same-grade GP3 replacement | 0/12 | +0.00212 |
| Native same-source append | 0/6 | +0.03190 |
| Native same-source replacement | 0/6 | +0.02497 |

Near/context high-grade cases equal their matched append predictions. The same-grade near cell has 11 eligible instances and one exclusion; its mean cannot be compared as though it contained all 12 append cases. Scores are **uncalibrated model logits**, not probabilities or cross-model comparable confidence.

The within-model margin contrast is measurable in these two selected-before-outcomes training hosts. The null decision-change result does not establish grade-classifier robustness on independent patients and does not replace the historical S2 v1 negative result.

## S1 placement stress and controls

S1 retains the original fixed top-five-percent benign/cancer scorer. At requested 10%, append/near/context each induce **7/12** new cancer errors; replacement induces **9/12**. All 12 baseline trial instances are correct and represent **two** unique benign hosts, not 12 patients. Append host-wise counts are **3/6 and 4/6**; replacement counts are **5/6 and 4/6**. Nine distinct donor slides are reused across seed/pair conditions. All 266 eligible native-sham instances, including zero-dose controls, have zero decision changes.

The machine record includes descriptive unique-host-cluster resampling (2,000 repetitions, seed 20261022). With only two hosts, it is conditional on this tiny host/donor set and cannot estimate unseen-patient uncertainty. For S1 append and replacement at 10%, the descriptive ranges are [0.500, 0.667] and [0.667, 0.833]. S2 zero-event bootstrap intervals collapse to zero; this degeneracy is **not** evidence of zero population risk. No clinical or independent performance claim follows.

## Reproducibility and resources

- [Execution, resource receipt, source/config identities and uncertainty](research_engine_23069070.json).
- [Unmodified executed summary](research_engine_summary_23069070.json), [all 1,017 raw cases](research_engine_trials_23069070.json), [all 327 exclusions](research_engine_exclusions_23069070.json), and [sealed registry/checkpoint hashes](research_engine_registry_23069070.json).
- Remote source: `/u/mhoda/floater-finder/releases/panda-engine-v3-20261021T012457Z/source`.
- Immutable remote run: `/work/nvme/bfqi/mhoda/floater-finder/panda-engine/acceptance-v3-20261021T012457Z`.
- Strict remote and local verification agree: **1,350 checkpoints, 1,353 events**, terminal seal and all registered hashes valid.

The exact executed `sbatch` command is in the execution receipt. Both jobs requested two CPUs, 4 GB and at most 15 minutes through `bfqi-delta-cpu` / `cpu-interactive`, with **zero GPUs**. Allocated-core elapsed time is approximately **0.0783 CPU-core hours** including the failed attempt, excluding queue time; this is not a billing audit. No download or new encoder inference occurred. All 24 final-test predictions remain sealed. The separate 96-instance pixel-composition/control study is prepared only; any new CONCH inference remains approval-blocked.

The next useful scientific work is cross-fitted or fresh-cohort validation of the fixed grade head and detector under these interventions. More repeated seeds on these same two training hosts would not supply independent validation.
