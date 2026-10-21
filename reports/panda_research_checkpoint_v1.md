# PANDA research checkpoint v1 — October 20, 2026

The work now concerns research infrastructure and development evidence. All measurements below use existing CONCH v1 vectors. The submission package, historical TCGA/PANDA results, rejected v1 protocol and final-test predictions are preserved. Known calibration is iterative development, not fresh validation. No new GPU inference or dataset acquisition occurred.

## 1. Architecture audit and completed refactoring

Historical S1/S2 duplicated eligibility checks, connected donor selection, right-edge injection and provenance; review runners duplicated input verification/reporting. New code retains the historical modules and adds `predictors`, `detectors` and `research` packages around the existing `Slide`, `TextEmbeddings`, grid, dose and scoring primitives. The existing `experiments.py` is unchanged and is not shadowed by a package. No empty target directories or encoder rewrite were introduced.

The shared engine provides six frozen/versioned contracts, one source/geometry/connectivity validator, donor selection, four intervention modes, retained-state restoration and exact legacy adapters. The append-only registry records source/configuration/data/model identities, Slurm resources, planned/running/verified/failed/excluded states and hash-verified resumable checkpoints. Terminal records are sealed. Failed artifacts are preserved and successful records cannot be overwritten. [Architecture/API, interpretation and status command](../docs/research_engine_v1.md).

The new predictor loader resolves eligible slide IDs before opening arrays/metadata; the shared-engine runner reuses it. Detector v3 reused a legacy directory index that parsed all 120 label-bearing tiling metadata files to resolve IDs, but opened only training NPZs and computed no held-out predictions. This limited indexing access is explicitly recorded rather than described as untouched test metadata. Future detector runs should use the stricter loader.

## 2. Prediction baselines and model-failure audit

Five candidates per task were fixed before outcomes. Logistic models use class balancing and fold-fitted scaling, four outer and three inner slide-grouped folds, regularization grid .01/.1/1, seed 20261021. Mean/max/coordinatewise top-five pooling uses no annotations or spatial/identity features. The primary rule maximizes training out-of-fold balanced accuracy, then worst-class recall and a fixed simplicity tie-break; the selection artifact was written before known-calibration arrays were opened. Patient IDs are unavailable. All ten models completed; no fit failure was discarded. An attention/MIL model was deferred because 72 cancer-task / 48 grade-task training slides with unknown patient identities do not justify that additional complexity.

Balanced accuracy percentages below are fixed-score training estimates for zero-shot models and nested out-of-fold estimates for trained models. Calibration columns are descriptive reused development.

| Candidate | Cancer training | Cancer known calibration | Low/high training | Low/high known calibration |
| --- | ---: | ---: | ---: | ---: |
| Zero-shot mean | 73.96 | 65.63 | 72.92 | 75.00 |
| Zero-shot top 1% | 63.54 | 71.88 | 60.42 | 62.50 |
| Zero-shot top 5% | 82.29 | 78.13 | 62.50 | 68.75 |
| Logistic mean | 80.21 | 75.00 | 77.08 | 62.50 |
| Logistic mean/max/top-K (selected) | **84.38** | **71.88** | **85.42** | **81.25** |

Selected cancer confusion matrices, truth rows / prediction columns in benign,cancer order: training `[[23,1],[13,35]]` over 72 slides, reused calibration `[[6,2],[5,11]]` over 24. Selected grade matrices in low,high order: training `[[24,0],[7,17]]` over 48, reused calibration `[[8,0],[3,5]]` over 16. Training benign recall is 23/24 and cancer recall 35/48; training low recall is 24/24 and high recall 17/24. This exposes the remaining high-class errors rather than relying on overall accuracy.

Conditional stratified slide-bootstrap balanced-accuracy intervals are 76.04–91.67% cancer training and 75.0–93.75% grade training. Paired differences are uncertain: grade selected-minus-old-mean training +12.5 points, 95% interval −2.08 to +27.08; known-calibration +6.25 points, −12.5 to +25.16. Cancer selected-minus-old-top5 training +2.08 points, −9.38 to +13.54; known-calibration **−6.25 points**, −21.88 to +9.38. These intervals condition on saved predictions and omit model-refitting/selection uncertainty. No confident independent improvement is established, and the frozen primary was not switched after the cancer calibration decline.

Balanced logistic outputs are uncalibrated scores. Selected training Brier values are .15966 (cancer) and .15286 (grade), with fixed-bin calibration diagnostics reported; cosine similarities are never converted into purported probabilities. Final grade regularization is C=.01, but outer-fold selected values vary [1,1,.01,.01], another small-sample instability.

Posthoc error diagnosis joins exported coverage/density/size and native mask-audit metadata without using annotations as model features. Full native GP3+4+5 annotated areas are available for 92/96 development slides from hash-verified cached audits; three original profile cases and one unusable mask remain unknown. No WSI was reread for that join. High-grade misses can occur despite almost complete native GP4/5 capture and full eligible-grid sampling; undersampling cannot explain every failure. Native annotation remains noisy, missing masks remain unknown and exploratory correlations are not causal findings. [Every model, raw margins, case studies, folds, portable predictors and receipts](panda_predictors_v1/report.md).

Strict acceptance found a numerical adapter defect: labels agreed, but 158/480 initial zero-shot score vectors had float32 reduction-layout differences up to 3.8743e−7. Original job outputs are retained. Corrected all-class/column-layout scoring now matches **480/480** historical vectors exactly; **80/80** saved linear calibration predictions are unchanged. No CV or model selection was repeated.

The retained initial `run/models/.../zero_shot_*` files document that numerical defect. Use `reports/panda_predictors_v1/adapter_acceptance/corrected_models/{task}/{zero_shot_model}/` for exact historical zero-shot replay; selected linear parameters remain under `run/models/{task}/linear_mean_max_topk/`.

## 3. S2 v2 readiness and measured scope

The selected mean/max/top-K grade probe passes the predeclared engineering gate (training OOF BA≥.70 and both recalls≥.60). It supports mechanistic CPU sensitivity checks, not clinical Grade Group upgrades or independent performance claims. The improved model was fixed before new contamination predictions. S2 v1 and its null primary result remain unchanged.

The new acceptance study uses two benign and two low-grade training hosts, two eligible donors per condition, three deterministic seeds, doses 0/.25/.5/1/2/5/10%, high-grade GP4/5 donors, same-grade GP3-only donors and native shams. It is a bounded S2 v2 **engineering smoke**, using a head fitted on training slides; it is not a completed fresh-cohort S2 evaluation. Job **23069070 completed 0:0**: **1,017/1,017 exact oracle recoveries**, 252 exact legacy comparisons and 345 eligible coordinate-only invariance checks. Of 1,344 planned mode/dose trials, **327 are explicit geometry exclusions**. Eligible records comprise 192 repeated zero-dose controls, 607 positive-dose non-sham trials and 218 positive-dose native shams. Four unique training host slides and 21 distinct non-sham donor slides underpin the repeated measurements; there are 24 source IDs overall because roles overlap. [All raw cases, uncertainty, exclusions and execution identities](research_engine_results_v1.md).

At requested 10%, high-grade donor tissue induces **0/12 S2 trial errors** for both append and replacement, from two originally correct training hosts with nine high-grade donor slides reused across seeds. Mean grade-logit shifts are +.9646 append /+1.0447 replacement. Same-grade controls use eight donor slides and also have 0/12 trial errors, with shifts +.01034 /+.00212. S2 has zero prediction changes across its 615 eligible records. These score shifts do not establish clinical upgrades or robustness. Even treating two slides as independent, zero affected hosts out of two has a Wilson upper 95% bound of about 65.8%; donor reuse and unknown patient identity further restrict inference.

The same engineering experiment's S1 10% conditions induce **7/12** trial errors for append/near/context and **9/12** for replacement, across two originally correct benign hosts and nine reused donor slides. Addition and replacement are different evidence interventions. Coordinate-only placements always match their paired append prediction; apparent aggregate differences at smaller doses reflect geometry exclusions, not classifier sensitivity to coordinates. Requested 10% realizes approximately 10.13–10.24%, and requested .25% approximately .391–.488%, because tile counts round upward. These are percentages of sampled original host tiles, not measured whole-biopsy tissue contamination fractions. All 266 eligible native-sham records have zero prediction changes and zero foreign truth flags.

## 4. Intervention modes and correctness

Implemented modes are exact legacy append, observed-boundary near-tissue placement, connected host-region replacement and an alternate within-region-context stress. Near/context require a complete bounded RGB overview, measured physical scale, source hashes, empty-footprint/bounds checks and a fixed 224-µm Chebyshev context rule. Missing sampled cells are never assumed blank. These are coarse RGB geometry proxies, not pathologist-confirmed physical boundaries or actual tissue compositing.

Replacement retains every original vector/coordinate/ID for exact restoration. Native shams have **zero foreign truth flags** and separately recorded altered indices. Coordinate-only translation of an unchanged feature bag must give exactly the same permutation-invariant prediction; this is tested and checked in the runner. Replacement changes the bag and may change predictions. Spatial placements remain relevant to contextual detectors even when bag predictions are invariant.

The first real job 23069018 failed a nested-prefix near-boundary eligibility check after five valid trial checkpoints and one geometry checkpoint. There was no oracle failure. Its source/output are retained. Version 3 freezes per-dose exclusions using the same maximal-fragment anchor and distance; it does not relax geometry or search using prediction outcomes, and reuses six hash-verified interrupted checkpoints in a fresh run. [Preserved failure](research_engine_failure_23069018.json). The rejection message combines overlap/proximity checks; not every exclusion was diagnosed as true distance infeasibility. One same-grade 10% near candidate failed revalidation despite its maximal-fragment proposal, so numerical/raster-boundary conservatism remains unresolved before a larger spatial study.

Pixel-composition preparation now has tested bounded CPU code for foreign patches, same-source boundary shams, null cut/reinsert and unchanged controls, exact pixel/change/foreign masks and parent hashes. The null edit does not match a foreign seam, and native shams cannot eliminate all seam confounding. The planned 96-image study has **no real tile plan or new encoding yet**. Re-encoding composites and any additional encoder require separate explicit GPU approval.

## 5. Detector v3 measured results

Five training-host folds compare seven new morphology/context signals with clean-fold burden thresholds and a fixed robust-NN5 primary. Two-stage visual shortlisting reports prediction influence separately; an AND comparator is preserved. Cohort references use one centroid per slide rather than component-count weighting. Ground truth, source IDs, annotations and absolute-position features are excluded from detector inputs.

The primary finds **1/120** fragments (1/1,647 foreign tile observations), flags **7/72** clean slides and **5/88** genuine annotated-cancer components, hypothetically damages **3/61** initially correct clean predictions and recovers **0/38** induced-error instances. Recall is over 24 reused host slides / 16 donor slides, not 120 independent patients. The alert estimate 9.72% has Wilson interval 4.79–18.74%, so the population target is not established. All seven methods fail the fixed 20% useful-recall target; the cohort method additionally exceeds observed clean burden (9/72).

Robust-score native cancer tails overlap or exceed foreign tissue tails. This is an identifiability limitation of these vectors/components, not justification for deleting unusual cancer. The primary's one hit is lost by the ≥.01 influence AND veto, but avoiding that veto still yields no useful policy. Conditional host-cluster recall interval is 0–2.5%. Ninety-five of 120 mixtures have a donor represented in the cohort fitting references; no donor-disjoint claim is made. Different estimation procedures prevent a formal numerical improvement claim versus selected v1/v2 resubstitution results. [All methods, full PR/burden curves, native controls, abstentions and provenance](panda_detector_v3_results_v1.md).

This run preserves old right-edge mixtures; detector-v3 performance on the new placements has not yet been measured. Its 120 saved-case reconstruction checks are not mislabeled as a rerun of the historical full oracle study. No useful review detector or final-test readiness has been established.

## 6. Fresh independent-development plan and S4 blockers

Outcome-blind metadata selection excludes 129 exposed study/pilot IDs. The primary fresh Radboud option is 60 slides (20 benign /20 GG1 /20 ISUP 4–5), **1,348,184,402 catalog TIFF bytes**. Optional second-institution Karolinska has the same category counts and **3,512,683,208 bytes**. All 120 candidate masks are catalog-listed; none of the 240 candidate image/mask paths is locally present, and usable-mask coverage is unknown. No new inputs were acquired. Slide separation is verified; patient independence is unknown. Sixty clean slides still give an approximately 6% Wilson upper bound with zero alerts, with much wider category-level uncertainty.

Karolinska needs a new verified mask interpretation; its cancer-region annotations do not provide Radboud GP4/5 labels. Freeze model/policy and candidate membership before acquisition/outcomes; retain unusable candidates and all negative findings rather than replace them opportunistically. [Manifests, hashes, bytes, uncertainty and validation gates](../docs/panda_fresh_validation_v1.md).

Read-only PathGen review identified an architecture/tokenizer specification discrepancy between the historical adapter and current official instructions, no OpenCLIP distribution in the prepared runtime, and no PathGen checkpoint in the bounded model-directory check. Exact compatibility and checkpoint bytes remain unverified. No weights/model were installed. [S4 interface/access audit and primary sources](../docs/panda_encoder_readiness_v1.md). MUSK and ordinal grades remain future separately authorized work; CONCH spaces are not mixed with another model.

## 7. Resources and permitted next experiments

All executed research jobs are CPU-only using `bfqi-delta-cpu` / `cpu-interactive`; CPU QoS permits one submitted job per user, so work is serialized. Prepared runtime versions are NumPy2.0.2, SciPy1.16.1 and scikit-learn1.7.2. Source snapshots are separate, archive/hash verified and not mutable working copies. The initial site balance snapshot was 5,467 rounded CPU hours /8 GPU hours, shared and not reserved.

| Work | CPU/memory/wall cap | Actual scheduler elapsed |
| --- | --- | ---: |
| Detector v3 23068965 | 2 /8 GB /20 min | 23 s, completed |
| Nested-CV predictors 23068979 | 2 /8 GB /30 min | 23 s, completed |
| First engine 23069018 | 2 /4 GB /15 min | 25 s, failed geometry gate, preserved |
| Exact adapter verification 23069033 | 2 /4 GB /10 min | 13 s, completed |
| Corrected engine 23069070 | 2 /4 GB /15 min | 116 s, completed |

The five jobs total 200 scheduler wall seconds, or approximately **0.111 allocated CPU-hours** at two requested CPUs each, including the preserved failure; queue time is excluded. No GPU allocation was consumed by this work. A future paired-placement detector analysis can reuse the saved vectors and verified geometry in a bounded 2-CPU/8-GB/20-minute job, after freezing its component mapping and comparisons. That new measurement is not yet completed. A fresh 60-slide cohort would need approved acquisition (2 CPUs/4 GB/1 hour), six bounded ten-slide CPU validation/tiling chunks, and a separately approved ≤30-minute one-A100 encoding batch (≤.5 GPU-hour, estimated from prior throughput). Estimated working space is 10 GB Radboud or 15 GB Karolinska; transfer/reader costs remain estimates. The proposed 96-image composite encoding envelope is one A100/4 CPUs/16 GB/5 minutes (≤.0833 GPU-hour) after exact real-input preparation and approval. No such GPU command is currently authorized or submitted.

## 8. Source revisions, verification and reproducibility

Runtime source identities are `0f2fc5fa3413ac3c7c5d1cd81181fd9c57017140` (initial predictors), `22f44d9af6191df283ffe9d9f0b1243ac8ec2d02` (exact adapter), `4bf89cd1e2f1dc838ccd84bc626d090709e83476` (v3 detector), `ba105d2fa9f7b985b62380a52d948cd9f20d53e9` (preserved engine failure) and `de220802f68098fac84119112157ee9078c6c13c` (corrected engine). Exact commands, source snapshots, file hashes, model fingerprints and raw outputs accompany each workstream report. Isolated research branches preserve those execution commits; tested changes are integrated into `feature/panda-tiling` as separate architecture/science commits.

Main remains `bdb13e5ee2fd8f61bf4a1885e0c6771d1ce9f39e`. All 33 source files pinned by the rejected frozen final protocol still match. Protocol SHA256 remains `695e2097aa0916bdd03b9b0721fc1f58dd5fda338e9c4975c171d64d2d36c881`. Existing source/result/submission artifacts were not overwritten. New figures are research figures; temporary synthetic fixtures remain software evidence only. Final verification: **258 tests pass with warnings treated as errors**, new Slurm scripts pass shell syntax checks, the final output remains absent and the own queue is empty. All 57 original predictor outputs and 14 adapter outputs verify against their committed completions; the engine's mirrored terminal registry verifies 1,350 checkpoints /1,353 events and its seal.

Exact next command, for read-only verification of the local mirrored real run:

```sh
cd "/Users/muneebhoda/Documents/Masters - Fall 2026/Ashby Hackathon-panda-tiling"
PYTHONPATH=src .venv/bin/python scripts/research_status.py \
  results/panda/research_engine_v3_23069070 --summary
```

This command was executed successfully and reports `status=verified`, `hashes_verified=true`. The mirrored full registry is an ignored local artifact; a new clone can retrieve the immutable remote run listed in the engine report. Source installation/tests use `uv sync --locked --no-editable --reinstall-package floater-finder --extra test --extra plots --extra panda --extra research` and `.venv/bin/python -m pytest -q -W error`. This is a research checkpoint, not a final-test authorization. The next scientific design should freeze a blinded component mapping for paired-placement detector analysis before new outcomes, then independently validate a fixed candidate; more seeds on these same training hosts do not establish generalization.
