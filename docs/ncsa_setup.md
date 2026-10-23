# Floater Finder: NCSA setup

## Source-path correction prepared — October 22

The original profile metadata for the three reused smoke slides matches the
existing embedding receipts exactly. Only `selection_manifest` and its SHA256
differ in the cohort copies. A new v2 source list points to the verified original
profile directories; the metadata/CSV/unbiased-training checks now pass57/57.
No hash guard, source ID, fold, scientific parameter or historical file changes.
The new versioned CPU configuration/launcher is prepared and tested locally;
no replacement job has run. WSI/PNG/native-mask and feasibility gates still need
scheduled execution. [Correction, pins and pending CPU command](panda_pixel_program_v2.md).

## Pixel results inspection — October 22, 20:33 CDT

Shared SSH verified `mhoda` / `dt-login03.delta.ncsa.illinois.edu` from Darwin.
CPU23109277 completed0:0 in13s and GPU23109340 completed0:0 in43s this morning.
The real96-image pilot has all399 prepared and five encoded receipt-file hashes
verified; both source-anchor and null drift gates pass. Across four repeated
training pairs, foreign NN5 exceeds its matched native sham in3/8,8/8,7/8
comparisons at1%,5%,10% within-tile patch area. Both frozen scorers have0/24
foreign mixed-image prediction changes; this is descriptive engineering evidence,
not a calibrated detector or independent clinical validation.

10k CPU23109667 failed1:0 in15s on a provenance check; its dependent GPU23109849
was cancelled before starting. Read-only metadata checks identify three reused
smoke sources whose current cohort metadata SHA256 differs from their original
embedding receipts. Five partial source facts, zero images/masks, no successful
record manifest/profile. Exact field differences remain unresolved; preserve
failures and reconcile provenance before a versioned correction or retry.

Own-QoS raw GPU usage5,816,000 billing-TRES seconds leaves8.3844444 normal-batch
A100-hour equivalents, reconciling exactly with the43-second interactive pilot
at billing2000. User queue empty. No new jobs/downloads/model calls or final-test
access during inspection. [Observed metrics, paths, hashes and limitations](../reports/panda_pixel_results_20261022.md).

The dated sections below preserve earlier submission states.

## Approved pixel GPU submission — October 21

User explicitly requested GPU submission and code commit. GPU23109340 is
PENDING (Dependency) as of17:55:22CDT,with`afterok:23109277(unfulfilled)` and
invalid-dependency cancellation requested. Slurm verified account
`bfqi-delta-gpu`,QoS`bfqi-delta-gpu-mhoda`,partition`gpuA100x4-interactive`,
one GPU,four CPUs,16GB,five minutes. CPU23109277 remains PENDING(Priority).
No new inference or real-image completion is verified; do not duplicate jobs.

Launcher1b4d19b is staged at
`/u/mhoda/floater-finder/releases/panda-pixel-gpu-launch-v1-20261021T225437Z/source`
(five files verified),using unchanged runtime61959fa/all276 files verified.
The resolver freezes the actual real-image manifest only after the successful
CPU dependency and validates all sources before the existing CONCH drift gates.
All432 tests pass. [Exact command,authorization and immutable receipts](../reports/panda_pixel_gpu_submission_v1.md).

## Pixel-contamination preparation handoff — October 21

Local Darwin and shared SSH identity `mhoda` / `dt-login04.delta.ncsa.illinois.edu`
verified. Existing account balances reported rounded4692 CPU hours and8 GPU
sub-allocation hours; no new GPU submission. Runtime source `61959fa` is staged
at `/u/mhoda/floater-finder/releases/panda-pixel-contamination-v1-20261021T223344Z/source`;
all276 files and frozen metadata/model inputs verified. The unchanged private
runtime is `panda-cpu-1598f9b-20261020T040441Z` under the documented envs root.

CPU23109222 timed out613s in scheduler Prolog on cn018, before any observed
Python step/log/preparation output. The inspected replacement CPU23109277
excludes cn018 and uses identical source/scientific inputs,2 CPUs,8GB,ten
minutes,`bfqi-delta-cpu` account/QoS,`cpu-interactive`. As of17:48:34CDT it is
PENDING (Priority), estimated start19:39:58CDT; this is a scheduler estimate,
not a guaranteed start. Old timeout is in terminal cleanup. No real96-image
manifest or GPU output exists. Do not duplicate the pending job or infer GPU
approval. [Exact commands, immutable receipts, tests and unresolved checks](../reports/panda_pixel_contamination_preparation_v1.md).

## Original-training topology/context execution — October 21

Local Darwin and SSH `mhoda` / `dt-login04.delta.ncsa.illinois.edu` verified. CPU **23101968 completed 0:0 in 27s** on `cn061`, account/QoS `bfqi-delta-cpu` / partition `cpu-interactive`, 2 CPUs, 8 GB, 20-minute cap, no GPU. Actual 0.015 allocated CPU-hours; Python MaxRSS 378,920 KiB. One submission, no retry.

Source `a1597699d3e6381a2f2baa35cebde1b687bdd6ff` at `/u/mhoda/floater-finder/releases/panda-topology-context-v1-20261021T164149Z/source` verified all 246 source files and six pinned original metadata/cache inputs. Results are sealed at `/work/nvme/bfqi/mhoda/floater-finder/panda-review/topology-context-v1`; authorization/output/common-support/completion receipts are sibling JSON files under `panda-review/`. All 72 training sources and 2160 planned context records verify, with no classification predictions or threshold changes. The original test output remains absent and the queue empty. [Findings and receipt hashes](../reports/panda_topology_context_results_v1.md); [frozen scope and exact command](panda_topology_context_v1.md).

No dataset, model or raw-result files were downloaded to the Mac; no WSI/PNG, fresh 60, calibration or original-test arrays were opened. Old input hashes, S1/S3 registry receipts, frozen source/protocol and main remain preserved. The audit provides topology/context feasibility evidence, not an approved foreignness policy or clinical validation.

## S3 conservative review transfer — October 21

Shared SSH verified `mhoda` / `dt-login04.delta.ncsa.illinois.edu`. Site snapshot: 4908 rounded CPU hours, 8 rounded GPU hours, empty queue and CPU-interactive up. Latest request to push and move forward supplied next-stage research direction; agent chose the bounded 2-CPU/8-GB/20-minute scope and showed the exact staged command before submission. No explicit user choice of those resource values is claimed.

CPU **23101320 completed 0:0 in 35s** on `cn100`, `bfqi-delta-cpu` account/QoS / `cpu-interactive`, zero GPUs; Python MaxRSS 345,324 KiB and 0.01944 allocated CPU-hours. Source `a5d819c360950d15ad0de84569ea5289edcb8942` at `/u/mhoda/floater-finder/releases/panda-fresh-review-transfer-v1-20261021T161755Z/source` verified all 240 files. Results are separately sealed at `/work/nvme/bfqi/mhoda/floater-finder/panda-fresh-baseline/radboud60-v1/fresh-review-transfer-v1`; authorization/output/interpretation/completion receipts are in the parent `reports/`. All 140 bags /9800 records, original S1 identities and 33 legacy files verify. The queue is empty, original final output absent, and no data/raw artifact was downloaded locally.

Primary combined has zero foreign hits per 20 cases per mode with four genuine-cancer native flags and four hypothetical clean-prediction harms. No useful detector or final readiness follows. [Measured report and receipt hashes](../reports/panda_fresh_review_transfer_results_v1.md); [frozen design and exact command](panda_fresh_review_transfer_v1.md). The bounded stage is complete; no more job was submitted.


## Fresh S1 execution — October 21

Local Darwin and shared SSH `mhoda` / `dt-login01.delta.ncsa.illinois.edu` verified. Explicitly approved CPU **23083320** ran once on `cn137`, account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`, 2 CPUs /8 GB /20-minute cap, zero GPUs. It completed 0:0 in 148s; Python MaxRSS 281,436 KiB /0.08222 allocated CPU-hours. All 233 staged source files and three baseline input receipts matched before submission; sealed output hashes and input receipts verified afterward.

Frozen source `3a3faf199bf2a334648227281a685a999a60f7c9` is at `/u/mhoda/floater-finder/releases/panda-fresh-s1-v1-20261021T073227Z/source`. Results are separately preserved at `/work/nvme/bfqi/mhoda/floater-finder/panda-fresh-baseline/radboud60-v1/fresh-s1-v1`; authorization, output/safety checks and completion receipts are in the parent root’s `reports/`. No datasets, weights or raw reports were downloaded to the Mac. All 2382 exact oracle checks passed; nine capacity exclusions remain. [Observed results, uncertainty, tissue-safety limits and receipt hashes](../reports/panda_fresh_s1_results_v1.md); [frozen protocol and exact submitted command](panda_fresh_s1_v1.md).

This consumes the approved CPU follow-up. No alert threshold, useful foreignness policy, patient independence or clinical validity is established. No additional jobs, GPU, downloads, fitting or original 24 final-test predictions are authorized by this run. Historical preparation notes below describe earlier states, not current pending work.

## Fresh baseline preparation — October 20

Local Darwin and shared SSH `mhoda` / `dt-login03.delta.ncsa.illinois.edu` were confirmed. Site inspection observed 5,425 rounded shared CPU hours and 8 GPU hours, `cpu-interactive` up with a one-hour cap, and an empty user queue. Exactly 120 proposed Radboud image/mask paths were stat-checked: none present. Shared available storage was 4,031,141,281,792 bytes, not a reservation. The existing Kaggle and PANDA CPU interpreter paths were present; credentials and live Kaggle authentication/download access were not inspected.

Source **bfd4416936d2c35d764d6fd46e1017f110ef48db** was staged at `/u/mhoda/floater-finder/releases/panda-fresh-baseline-v1-20261021T023142Z/source`; all **226 source files** and the default metadata/model preflight verified with no prediction. The [preparation receipt](../reports/panda_fresh_baseline_preparation_v1.json) records the archive hash, exact pending acquisition and CPU tiling commands, observation records and resource bounds. [Protocol and approval scope](panda_fresh_baseline_v1.md).

No new job, image/mask acquisition, WSI processing, GPU or fresh prediction occurred. The proposed new 60-slide download/CPU intake scope remains pending approval; future GPU and fresh scoring have separate gates. Reader/mask usability, actual tissue yield, patient independence and fresh predictive results remain unknown. The original 24 final-test slides remain sealed.

## Paired-placement CPU audit — October 20

Local Darwin and shared SSH identity `mhoda` / `dt-login03.delta.ncsa.illinois.edu` were verified for this continuation. Site inspection reported 5,447 rounded CPU hours and 8 rounded GPU hours, shared snapshots rather than reservations; `cpu-interactive` was up and the user's queue was empty before submission. The prepared runtime imports NumPy2.0.2 and Pillow12.3.0.

CPU **23069409 completed 0:0** on `cn034`, two CPUs /8 GB /20-minute cap, `bfqi-delta-cpu` account/QoS and `cpu-interactive`. Actual elapsed 271 seconds, Python MaxRSS 1,319,304 KiB, 0.15056 allocated CPU-hours. Source `bbc2845875c8ff980a20d2c7bf9123ed801afc99` was staged separately at `/u/mhoda/floater-finder/releases/panda-placement-v1-20261021T015213Z/source`, verifying all 207 files. Verified immutable results are at `/work/nvme/bfqi/mhoda/floater-finder/panda-review/placement-v1-20261021T015213Z`; the sealed registry has 1,657 checkpoints /1,660 events. [Exact command, runtime paths, archives and every output hash](../reports/panda_detector_placement_v1/execution.json).

This training-only audit uses existing embeddings/PNG exports and cached foreground, with no WSI processing, downloads, GPU, calibration or final-test predictions. Primary detection is 0/607 foreign instances; no useful policy or final readiness is established. [Measured report and read-only next command](../reports/panda_detector_placement_v1.md). The rejected final protocol and all prior artifacts remain preserved; fresh acquisition/encoding still needs explicit scope/resource approval.

## Research CPU checkpoint — October 20

The local Mac execution environment was verified as Darwin. Shared SSH confirmed `mhoda` on `dt-login03.delta.ncsa.illinois.edu`. The prepared PANDA CPU runtime reports NumPy2.0.2, SciPy1.16.1, scikit-learn1.7.2 and Torch2.8.0+cu128 by package metadata; no Torch/CUDA inference was needed for this stage. Site allocations initially showed 5,467 rounded CPU hours and 8 GPU hours. These are shared snapshots, not reservations. CPU QoS permits one submitted job per user, so the research jobs were serialized.

Detector v3 **23068965** and nested-CV predictors **23068979** completed 0:0 in 23 seconds each. Exact-score adapter verification **23069033** completed 0:0 in 13 seconds, matching 480 historical zero-shot vectors and 80 saved linear predictions. The first shared-engine job **23069018** failed an unhandled dose-specific placement eligibility check in 25 seconds; its five trial / one geometry checkpoints and failure record are preserved. Corrected **23069070** completed 0:0 in 116 seconds, using a new output and fixed predictor/geometry rules. There was no oracle failure or duplicate submission.

These jobs used `bfqi-delta-cpu` / `cpu-interactive`, 2 CPUs and 4–8 GB each, with separate hash-verified source snapshots. No GPU, dataset/weight acquisition or final-test job was launched. The [research checkpoint](../reports/panda_research_checkpoint_v1.md) links exact commands, source revisions, inputs, outputs, measured denominators and remaining gates. The original 120-slide artifacts, frozen rejected final protocol and submission materials are preserved.

Metadata-only fresh-cohort proposals exclude all 129 exposed pilot/study IDs. The proposed Radboud60 inputs total 1,348,184,402 catalog TIFF bytes; optional Karolinska60 inputs total 3,512,683,208 bytes. Exactly 240 candidate paths were stat-checked and none was present. Catalog masks are not verified usable masks, and patient IDs remain unavailable. [Versioned manifests and acquisition/resource gates](panda_fresh_validation_v1.md). PathGen remains unverified: the prepared runtime has no `open_clip_torch` distribution, and the bounded existing model-root check found only CONCH. [Interface/checkpoint audit](panda_encoder_readiness_v1.md).

## Submission, S2 and ranked detector v2 — October 20

Shared SSH identity reverified `mhoda` on `dt-login03.delta.ncsa.illinois.edu` from the local Mac. Site `accounts` reported 5,488 rounded CPU hours and 8 rounded GPU hours at the setup inspection; these are shared-allocation observations, not future guarantees. `cpu-interactive` was available with a one-hour partition limit. Both new jobs used the verified `bfqi-delta-cpu` account/QoS, 2 CPUs, 4 GB and a ten-minute cap, with no GPUs.

- S2 job **23067396 completed 0:0 in 19 seconds**. Runtime source `35e0a8dae57e22808420b45ae040fc2f8c3710a5`; verified separate snapshot `/u/mhoda/floater-finder/releases/panda-s2-dev-20261021T003007Z/source` (361 files). New output `/work/nvme/bfqi/mhoda/floater-finder/panda-stress/s2-dev-v1-20261021T003007Z`. All 760 oracles passed; mean primary has no calibration low-to-high errors across the tested doses. [Exact job and input/output hashes](../reports/panda_s2_submission_v1.json).
- Ranked detector v2 job **23067454 completed 0:0 in 23 seconds**. Source `668d9b8c4e3e8aa300bda6ff15e416c601c2e024`; verified snapshot `/u/mhoda/floater-finder/releases/panda-review-v2-20261021T003112Z/source` (367 files). New output `/work/nvme/bfqi/mhoda/floater-finder/panda-review/detector-v2-20261021T003112Z`. The selected point remains unsupported: 0/40 calibration fragment hits. [Exact job and result hashes](../reports/panda_review_v2_job_23067454.json).

No existing acquisition, WSI/tiling, GPU encoding, S1 draw, counterfactual or final-preflight job was repeated. The completed 23066843 preflight and rejected v1 frozen protocol remain unchanged. All 24 final-test predictions remain sealed; no final job or new GPU workload is authorized. [Submission/scientific handoff](../reports/submission_execution_checkpoint_20261020.md).

## Latest PANDA review-policy checkpoint — October 20

Shared SSH verified `mhoda` on `dt-login03.delta.ncsa.illinois.edu`. CPU-only measurement job 23066481 preserved 96 topology / 256 review-case records before a selection-report JSON serialization failure; corrected selection-only job 23066553 completed `0:0` in 17 seconds from those exact measurement hashes. The selected combined policy has no supported operating point; all 24 final-test slides remain unscored. No acquisition, tiling or GPU inference was repeated.

Read-only preflight 23066843 completed `0:0` in 31 seconds on `bfqi-delta-cpu` / `cpu-interactive` (2 CPUs, 4 GB, ten-minute cap). It verified 10,988 files across 24 test slides, all pinned source files and prepared package versions, without decoding held-out labels or computing predictions. It reported readiness false. Own queue was empty and the final output directory absent at the completion inspection. [Evidence](../reports/panda_final_preflight_completed_v1.json).

- Verified final runtime source commit: `cde0e4a257898c6abe93d6a4df6ad52c744f31cc`; separate snapshot `/u/mhoda/floater-finder/releases/panda-final-prep-20261021T001051Z/source` (323 files verified; source files mode 444).
- Frozen rejected protocol: `/work/nvme/bfqi/mhoda/floater-finder/panda-review/final-preparation-v1-20261021T000114Z/panda_frozen_protocol_v1.json`, SHA256 `695e2097aa0916bdd03b9b0721fc1f58dd5fda338e9c4975c171d64d2d36c881` (mode 444).
- Blinded input contract: the same preparation root's `blinded_test_inputs_v1.json`, SHA256 `da7cc55b2c68356b31fd5692dcea9e8ac8e1734f82d2ffb5d9555e382ae9744f`; IDs/paths/hashes only.
- CPU runtime: `/work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z`; numpy 2.0.2, Pillow 12.3.0, openslide-python 1.4.6, tifffile 2025.5.10 verified by the scheduled preflight.
- Measurement output: `/work/nvme/bfqi/mhoda/floater-finder/panda-review/development-v1-20261020T235701Z`; completed reporting output adds suffix `-selection-v2`. Original failed output is preserved.

The exact prepared final command and expected outputs are [documented](panda_final_test_v1.md), **not authorized for submission under this rejected protocol**. Missing scientific inputs are a useful independently validated development policy, verified patient identities and stronger physical-boundary/clinical validation. All earlier setup and experiment history below remains preserved.

## Latest PANDA scale-up checkpoint

PANDA now has **120 slides / 50,729 verified CONCH embeddings**. The clean development baseline, **192 connected-fragment S1 trials** and **64 calibration piece counterfactuals** are executed. All 192 oracle recoveries pass. Genuine annotated cancer can also be decisive, so no foreignness or calibrated-alert claim follows. The 24 final-test slides remain unscored. [Current results, charts and remaining gates](../reports/panda_s1_and_piece_results_20261020.md).

## Verified PANDA follow-up outputs — October 20

Shared SSH after manual reconnection verified `mhoda` on `dt-login03.delta.ncsa.illinois.edu`. GPU `23054910`, verification/baseline CPU `23055022`, S1 CPU `23065666` and piece-diagnostic CPU `23065744` are all `COMPLETED 0:0`. Own queue is empty at the final check. Latest site `accounts` shows 5,516 rounded CPU hours and 8 rounded GPU hours; these are observed balances, not future availability guarantees.

- Verified cohort: `/work/nvme/bfqi/mhoda/panda/annotated_cohort_120_20261020_verified_v1.csv`.
- Verified 120-slide embeddings: `/work/nvme/bfqi/mhoda/floater-finder/panda-embeddings/cohort-120-v1-representative`.
- CPU artifact receipt: `/work/nvme/bfqi/mhoda/panda/cohort-plans/20261020-scale-v1/embeddings_verified_120_job23054910_v1.json`.
- Clean development baseline: `/work/nvme/bfqi/mhoda/floater-finder/panda-baselines/dev-zero-shot-v1-23054910`.
- S1 development outputs: `/work/nvme/bfqi/mhoda/floater-finder/panda-stress/s1-dev-v1-20261020`.
- Calibration piece outputs: `/work/nvme/bfqi/mhoda/floater-finder/panda-pieces/calibration-top5pct-v1-20261020`.
- Immutable S1 source: `/u/mhoda/floater-finder/releases/panda-s1-dev-20261020-v1/source`; piece source: `/u/mhoda/floater-finder/releases/panda-piece-dev-20261020-v1/source`.

Both new diagnostics used CPU only and existing embeddings, with no new data/weight download. Final `train.csv`, `pilot.csv` and original partial `annotated_cohort.csv` hashes still match their recorded originals. The current per-slide ledger is `reports/panda_scale_ledger_current_20261020.json`. Patient identities, complete physical-piece topology, calibrated review-alert thresholds and independent final-test validity remain unresolved. No final-test scoring or additional GPU batch was launched.

## PANDA CPU smoke completed; cancer capture failed; available cohort is partial

The user explicitly approved the prepared CPU command. It was submitted once as **`23050425`**, completed `0:0` on `cn137` in **9 seconds**, and produced **32 tiles per biopsy / 96 total**. All three CSVs, geometry, mask fractions, PNG dimensions and saved artifact hashes passed remote checks; retrieved CSV/metadata hashes and counts were independently checked locally. High-grade donor `dd1110c6430e3b1ac732be548a089886` had **0/32 tiles with nonzero Gleason 4 and 0/32 with Gleason 5**, so the cancer-positive extraction acceptance gate did not pass. Preserve this outcome; no resubmission, donor enrichment or GPU inference followed. [Observed CPU results](../reports/panda_cpu_smoke_results.md).

At inspection, acquisition `23030528` was still pending for Priority. Its expected log did not exist, and its batch script invokes `/work/nvme/bfqi/mhoda/panda/collect_annotated.py`, which was absent. No larger manifest was generated in the checked locations. The job and script were left unchanged. [Inspection facts](../reports/ncsa_panda_acquisition_inspection_23030528.json).

Under the user's explicit metadata-selection request, created `/work/nvme/bfqi/mhoda/panda/annotated_cohort.csv` with **three verified available Radboud biopsies**, one per requested group, using seed **20261020** and valid-mask-first deterministic selection. All three are training-only; calibration/test are empty. Mask coverage is **2/3**. There is a shortfall of 19 cases per group. The original `pilot.csv` hash is unchanged. The adjacent `.selection_provenance.json` records source metadata hash, selection recipe hash, seed, actual counts and partial status. No patient IDs are supplied, and no 60-slide readiness or patient-disjoint evaluation is claimed. [Selection provenance](../reports/panda_cohort_selection_20261020.json).

## Real PANDA CPU smoke: staged and preflighted; submission awaits approval

After manual reconnection, shared SSH verified `mhoda` on `dt-login04`. Exact pushed commit `1598f9b08e625112be7d5bf91a25f82335c962f9` is staged read-only at `/u/mhoda/floater-finder/releases/panda-1598f9b-20261020T040441Z/source`; all 172 source hashes match before and after preflight. The existing CONCH runtime was preserved. A new CPU runtime at `/work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z` imports NumPy 2.0.2, Pillow 12.3.0, PyYAML 6.0.2, OpenSlide Python 1.4.6/binary 4.0.1.2 and tifffile 2025.5.10. Only the new runtime received dependency overrides, installed offline from two staged wheels.

All three real images and both available masks passed the exact reader's header/alignment/calibration checks and five bounded one-pixel decoder probes. Native compressed tiles are 512×512; no complete slide plane or tile collection was processed on the login node. Measured MPP is 0.4861876369654638 in both axes for all three. The GG1 mask remains absent. [Observed reader/runtime facts](../reports/ncsa_panda_reader_preflight_1598f9b_20261020.json), [source hashes](../reports/ncsa_panda_source_manifest_1598f9b_20261020.json).

Acquisition job `23030528` remains pending for Priority at the latest check and was left unchanged; no duplicate was submitted. The site's `accounts` snapshot showed 6,765 rounded CPU hours and 9 GPU hours; `cpu-interactive` was up. A scheduler `--test-only` check accepted the separate two-CPU, 4 GB, ten-minute tiling request without submitting it. The user's explicit step-5 approval is still required. [Exact paths, command, outputs and acceptance checks](../reports/panda_cpu_smoke_preparation.md). No GPU inference was launched. Tile counts and cancer-positive donor counts remain unknown until the actual CPU job runs.

The observed `train.csv` has 10,616 rows and `pilot.csv` still has 12. A local software fixture confirms compatibility with a 60-row Radboud membership CSV, but the actual new cohort manifest has not yet been located; its path was requested. No original manifest was overwritten. The three-slide smoke cap remains in force.

## PANDA pilot supplied by the user: adapter prepared, real run pending

The user has now verified `/work/nvme/bfqi/mhoda/panda/` containing original `train.csv`, a 12-Radboud-biopsy `pilot.csv`, `train_images/` and `train_label_masks/`. This personal root was outside the earlier bounded shared-root search. [The implementation status](../reports/panda_implementation_status.md) records the three exact user-verified slide IDs, scale/mask facts, local tests and unsubmitted CPU/GPU resource drafts. These facts came from the user; the new adapter has not independently executed on those Delta files.

The adapter reads physical scale from level-0 TIFF resolution tags and checks it against the user's approximate `.486` microns/pixel within 1%; it does not replace measured scale with an assumed value. Mask absence remains unknown, and original ISUP/Gleason grades are never copied into tile labels. The original checkpoint and verified CONCH runtime paths below remain unchanged. The new optional TIFF dependency must be checked/prepared in an isolated Delta runtime before the CPU stage; no runtime was modified remotely.

No PANDA job, new GPU inference or bulk download was performed for this request. Real TIFF decoder compatibility, spatial QC of extracted tiles and approval of the bounded new scope remain gates. A local uncompressed RGB tiled-TIFF decoder failure is documented in the status report; compressed fixture success is not a real-Delta compatibility claim.

## Prostate-biopsy pivot: read-only availability check

On October 19 (observation timestamp October 20 UTC), the local Mac's shared SSH connection verified `mhoda` on `dt-login04.delta.ncsa.illinois.edu` via `ncsa-floater`. A bounded name/metadata search checked the two documented shared dataset roots, at most two directory levels, 200 entries per directory, 2,000 total entries and 30 seconds. It examined 48 entries, without truncation or reported directory errors, and found no PANDA/prostate/biopsy candidate names. This historical check excluded the personal PANDA root subsequently supplied above. [Exact scope and observed names](../reports/ncsa_panda_availability_20261019.json).

`accounts` returned 6,881 rounded CPU hours on `bfqi-delta-cpu` and 9 rounded GPU hours on the `bfqi-delta-gpu` sub-allocation `mhoda`. Both allocations were previously confirmed for the hackathon. The user's queue was empty; the queried `cpu-interactive` and `gpuA100x4-interactive` partitions were up with one-hour limits. These are snapshots, not guarantees, and this was not a new GPU-access test.

No dataset/weight downloads, image/feature body reads, inference or jobs were started for this pivot. PANDA slide, mask, provider/label metadata and access/license locations remain unverified; no PANDA destination or new Slurm request has been selected. Phase 2 also needs a validated benign/cancer scorer and new-scope execution authorization. [Integration gates and artifact reuse](panda_integration.md) supersede the older “next command” recommendations below for current work. Historical experiment paths, jobs and evidence remain preserved.

## Historical CONCH/TCGA setup and execution

Initial setup verified on 2026-10-17; latest acquisition verification on 2026-10-19 (America/Chicago). First milestone: CONCH only.
Initial connection setup performed no Slurm job, inference, whole-slide processing, or dataset/model download. The later approved scheduled GPU smoke and hosted two-tile CONCH image-encoding test succeeded. Self-hosted CONCH v1 encoding and patient-separated detector smoke are verified below. The expanded development cohort is now encoded, but its cutoff-retention gate did not pass; expanded held-out and clinical performance remain untested.

## Development cohort encoded; cutoff gate did not pass

The user requested committing the results and moving to development embedding/calibration work. Commits `f0f19a4` and `a6d826d` preserve the prior evidence and implement the development-only runner. After one failed shared-SSH test, remote attempts stopped until the user manually reconnected; the next single BatchMode test confirmed `mhoda` on `dt-login04`. `accounts` then reported 6,915 rounded CPU hours and 9 rounded GPU hours; the queue was empty. These balances are snapshots.

GPU job **`23028013` completed `0:0` on `gpua038` in 10 minutes 5 seconds**, with one A100, four CPUs, 16 GB and a 30-minute cap, account `bfqi-delta-gpu`, QoS `bfqi-delta-gpu-mhoda`, partition `gpuA100x4-interactive`. The documented short queue provided an earlier slot than the normal queue; no duplicate GPU job was submitted. All **ten development patients, 3,840 image embeddings of 512 dimensions**, passed exact frozen geometry, checkpoint, prompt, runtime and normalization checks. All 61 retrieved hashes match. No evaluation patient was encoded or dataset/weight downloaded.

CPU job **`23028265` completed `0:0` on `cn137` in 15 seconds**, with two CPUs, 8 GB and a 30-minute cap under `bfqi-delta-cpu`/`cpu-interactive`. All ten clean leave-one-patient-out folds and 150 patient/quantile/variant rows completed. Native score counts, omitted-patient isolation and every budget decision were independently checked; all 32 retrieved hashes match. **No candidate met the fixed 1% original-host removal budget on every patient and variant.** Even `q=0.995` removed 19/384 tiles (4.95%) on one omitted development patient under the combined score, exceeding the allowed three.

No final numerical calibration was created, and held-out evaluation remains stopped. No patient, budget, prompt, sampling rule or scoring weight was changed in response. The queue was empty after selection. The local suite passes **105 tests**. [Complete results, per-patient controls and next diagnosis](../reports/conch_development_results.md).

Source snapshot: `/u/mhoda/floater-finder/releases/20261020T020759Z`. Remote encoding/selection: `/work/nvme/bfqi/mhoda/floater-finder/pilot-development/20261020T020759Z/{encoding,selection}`. Retrieved embeddings/native fold scores remain ignored locally under `results/development/cohort_encoding_23028013/` and `results/development/cohort_selection_23028265/`. Frozen base source hashes were preserved. Report linkage, normalized institutions, native floater labels and project storage quota remain unresolved.

## Expanded-pilot technical gates: passed; study design frozen

On October 19, a single BatchMode identity check confirmed `mhoda` on `dt-login02`. `accounts` reported 7,233 rounded CPU hours and 9 rounded GPU hours; both hackathon allocations remain verified. The user's queue was empty and `cpu-interactive` was up with a one-hour limit. These are snapshots, not quota guarantees.

CPU preflight `23005189` verified all 18 slide checksums/headers, but correctly exited `2:0` when development patient `TCGA-HC-7230` could not provide the fourth 128-tile window at the required spacing. Before any new embeddings or held-out outcomes, changed the candidate uniformly to four windows of 96 tiles per patient. No patient, spacing, prompt or detector setting changed. The failed candidate and immutable source snapshot remain preserved.

Revised CPU job **`23005299` completed `0:0` on `cn137` in 2 minutes 34 seconds**, with two CPUs, 4 GB and a 15-minute cap under account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`. All **18 headers/coordinate sources and 384-tile selections passed**. Only shared coordinates were used, never v1.5 features. The two predeclared development patients exported 768 QC tiles, with no model load, GPU or new embedding. All 45 retrieved artifact hashes match; independent checks confirmed unique in-bounds cells, connected windows, matching manifests and minimum inter-window spacing of 1,024 microns. Contact sheets received technical visual QC only; background/edge artifacts remain and no pathology labels were assigned. The final queue was empty.

Remote output: `/work/nvme/bfqi/mhoda/floater-finder/preflights/expanded-20261019T052935Z`; source snapshot: `/u/mhoda/floater-finder/releases/20261019T052935Z`. Small artifacts remain locally under ignored `results/preflight/23005299/`; full exported tile PNGs remain on Delta. [Observed results and failed-candidate history](../reports/conch_pilot_preflight_results.md), [verified accounting/hashes](../reports/ncsa_pilot_preflight_verification_20261019.json), [frozen study design](expanded_pilot_protocol.md).

The design freezes patient splits, prompts, broader sampling, scoring, development-only cutoff-selection rules, controls and denominators. The cohort runner is not yet implemented, and final numerical thresholds are not fitted/frozen. No expanded GPU encoding or held-out evaluation was submitted. Clinical annotations, normalized institutions, report linkage and allocation/project storage quota remain unresolved.

## Approved expanded-pilot acquisition: completed and verified

The user explicitly approved the exact 16-slide, 21,243,276,685-byte acquisition on 2026-10-18. Recorded the download-only scope in the acquisition manifest and AGENTS.md. Regular CPU job `22995881` stayed pending with reason `Reservation` as the CPU event reservation ended at 6:00 pm Central. After a scheduler dry-run verified an available short slot, the pending job was cancelled and replaced by `22995933` on the documented `cpu-interactive` partition, with the same CPU account/QoS, one CPU, 2 GB and 30-minute cap. No GPU or expanded pilot was requested.

After the user manually reconnected, the single BatchMode identity test confirmed `mhoda` on `dt-login02.delta.ncsa.illinois.edu`. Job `22995933` completed `0:0` on `cn096` in **4 minutes 42 seconds**, ending October 18 at 6:08:44 pm Central. All **16/16 approved slides, 21,243,276,685 bytes**, passed exact size and streaming MD5 verification; zero files failed. The retrieved report exactly matches the approved file IDs, destinations and checksums. Report/log hashes and immutable source hashes match their remote copies/submission record. All final slides are regular files owned by `mhoda`, mode `600`, with owner-only input directories. The user's queue was empty at verification.

Evidence: [per-file download report](../reports/pilot_downloads_22995933.json), [accounting, storage metadata and integrity verification](../reports/ncsa_pilot_download_verification_20261019.json), and [execution/scope](expanded_pilot_plan.md). The earlier [partial observation and SSH interruption](../reports/ncsa_pilot_download_status_20261018.json) remain preserved as history. Only small reports and file metadata were read on the login node; no repeated whole-file hashing was performed there. No new weights, image embeddings, expanded pilot or GPU job were run in this acquisition. Headers, coordinates, broader sampling and study-design freezing were later completed in the technical stage recorded above.

## Patched image runtime: verified on a scheduled A100

New image processing now pins Pillow **12.3.0**; local optional tests pin pytest **9.0.3**. The dependency updates address all 19 unique advisories in the recorded 37-entry inventory by installed version. Focused upstream regression probes reject the previously accepted CMS mode mismatches and pytest temporary-root symlink while preserving normal controls. Specific application exploitation of every advisory was not demonstrated, and GitHub alert closure has not been checked after a push. The current local suite passes **91 tests**.

CPU job `22995419` completed `0:0` on `cn004` in 49 seconds, preparing a **new** private environment at `/work/nvme/bfqi/mhoda/floater-finder/envs/conch-v1-pillow123-20261018T223113Z`. It uses the same verified Torch/CONCH/OpenSlide versions with the patched Pillow override. Input checksums, headers and tokenizer passed. The legacy environment and all earlier outputs remain preserved for historical reproduction.

GPU compatibility job `22995434` completed `0:0` on `gpua029` in 85 seconds with one A100, four CPUs, 16 GB and a five-minute cap, using account `bfqi-delta-gpu`, QoS `bfqi-delta-gpu-mhoda`, partition `gpuA100x4`. It regenerated only the two existing development subsets. All **256 decoded tiles, image vectors and frozen-text vectors matched the legacy copies exactly**, maximum difference zero; geometry was unchanged. New model/extraction provenance records Pillow 12.3.0, so these artifacts stay distinct from legacy artifacts even with equal vectors. Fourteen retrieved file hashes matched; local loading independently confirmed matching arrays and patient identities. This is bounded compatibility evidence, not new detector or full-slide performance.

Remote output: `/work/nvme/bfqi/mhoda/floater-finder/runtime-checks/pillow123-20261018T223310Z`. Immutable source snapshot: `/u/mhoda/floater-finder/releases/20261018T223113Z`. Logs, arrays, checksums, submission resources and the remediation report are retained in the managed Codex Security artifact collection outside this repository. New raw-image calls reject a mismatched Pillow version before image processing; array-only analysis of old artifacts remains available. The queue was empty after these two jobs.

The [expanded feasibility-pilot proposal](expanded_pilot_plan.md) identifies 16 new metadata-verified slides totaling 21,243,276,685 bytes, with separate development/evaluation patients and source-site prefixes. The user explicitly approved those exact downloads on 2026-10-18. At that proposal stage, the broader sampler and cohort runner were unimplemented; the sampler and study-design freeze subsequently passed the technical stage recorded above. The cohort runner remains a later gate, and no expanded encoding/evaluation job has been submitted.

Storage inspection reported about 3.8 TiB free on the shared NVMe filesystem. `lfs quota -u mhoda` returned zero user soft/hard block and inode limits, meaning no explicit user limits were reported by that command. Allocation/project quota and future headroom remain unverified; filesystem free space is not a personal quota guarantee.

## Latest development cutoff diagnostic: completed

The shared connection was confirmed as `mhoda` on `dt-login04.delta.ncsa.illinois.edu`. The queue was empty before submission; `accounts` listed 7,327 rounded CPU hours and 9 rounded GPU hours, and `cpu` was up. These are snapshots, not guarantees.

Under the existing continuing authorization, CPU job `22995268` reused only the two development patients' existing CONCH v1 embeddings. It completed `0:0` on `cn004` in 12 seconds, with two CPUs, 4 GB and a five-minute limit under account/QoS `bfqi-delta-cpu`. No model inference, evaluation artifact, GPU or new data download was used. All 60 oracle checks and 900 quantile/variant metric rows completed. The final queue was empty. Source snapshot, exact hashes and request: [submission record](../reports/ncsa_threshold_submission_20261018T222409Z.json).

The diagnostic compares five clean-development cutoffs without selecting one. It reuses calibration patients for synthetic trials, so it is explicitly resubstitution rather than independent evaluation. [Observed results](../reports/conch_threshold_results.md) record detection/removal tradeoffs, per-patient controls and cross-version rounding limits. All 127 retrieved artifacts match remote hashes, and all saved metrics were independently reproduced. At that stage, 85 local tests passed. Output: `/work/nvme/bfqi/mhoda/floater-finder/diagnostics/threshold-20261018T222409Z`; local arrays remain ignored under `results/development/conch_threshold_22995268/`.

## Latest patient-separated detector smoke: completed

Following the user's instruction to continue the plan without repeated permission requests, two additional public diagnostic WSIs were GDC-verified and staged as development-only patients. They total 5,188,681,471 bytes and match GDC MD5 checksums: `TCGA-2A-A8VO`, `2c1a5ce93579b5e1d48ff8b3f85d222f`; `TCGA-2F-A9KO`, `eb843ea75b45382b88f24b616444915b`. Exact sources and destinations are in [the calibration input plan](../configs/ncsa_calibration_download_plan.json) and [download report](../reports/calibration_downloads_20261018.json). Their files are mode `600`; the existing owner-only input directories remain in use. This bounded extension supports patient-separated calibration, not bulk cohort collection.

GPU calibration-encoding job `22994850` completed `0:0` in 71 seconds on `gpua029`. It produced two `[128,512]` development artifacts from the same original checkpoint and physical tiling protocol. Measured development MPP values are 0.2527 for prostate and 0.2277 for bladder, both isotropic. Retrieved 15 artifacts and independently checked hashes, normalization, frozen-text/model compatibility and patient separation. [Encoding evidence](../reports/conch_calibration_encoding_22994850.json).

CPU detector job `22994885` completed `0:0` in 14 seconds on `cn004`, using two CPUs and 4 GB memory. It fitted normalization and 99th-percentile thresholds only on 256 unmodified development tiles, with 1 mm exclusion, 0.1 mm smoothing and equal organ/visual weighting frozen before evaluation. The two evaluation patients are excluded from calibration, including their reciprocal donor identities. All 60 oracle checks passed and all 180 organ-only/visual-only/combined rows completed without exclusion. Full no-filter, oracle and matched random-removal controls are saved.

The combined threshold detected only 3.85% of injected tiles on average in the 10%-requested stratum (two evaluation hosts × five seeds), despite mean AUROC 0.949; original-host removal was zero in that stratum. The original-host negatives in this synthetic study are not pathologist-confirmed floater-free tissue. These results show a conservative threshold in a tiny subset smoke, not clinical sensitivity or a population estimate. See the [result report and map](../reports/conch_detector_results.md) and [validated machine-readable evidence](../reports/conch_detector_smoke_22994885.json).

Retrieved all 184 detector files and verified their hashes; independently recomputed every oracle trial, variant flag and count metric. Maximum standardized-score difference across recorded NumPy versions was 1.47e-6. All six new jobs completed `0:0`; the final queue was empty. [Accounting evidence](../reports/ncsa_jobs_20261018.json). The current local suite passes 82 tests.

Raw arrays remain under ignored local `results/smoke/conch_detector_22994885/`. The remote detector output is `/work/nvme/bfqi/mhoda/floater-finder/smoke/detector-20261018T215641Z`; development encoding is `/work/nvme/bfqi/mhoda/floater-finder/smoke/calibration-20261018T215432Z`. Total verified inputs now occupy 9,990,121,727 bytes. Per-user quota and larger-cohort behavior remain unverified.

## Latest scheduled CONCH v1 smoke: completed and independently validated

GPU job `22994635` completed `0:0` in 61 seconds on `gpua029`, using one NVIDIA A100-SXM4-40GB with CUDA 12.8. It extracted and resampled 128 tiles from each verified diagnostic WSI into a common 256-micron physical field, then generated normalized projected 512-dimensional image vectors and frozen-prompt text vectors from the pinned original CONCH checkpoint. No hosted-service key or Hugging Face authentication was used.

The six requested contamination levels were 0, 0.5, 1, 2, 5 and 10 percent of original host tile count, seed 0. Actual foreign counts were 0, 1, 2, 3, 7 and 13; corresponding realized percentages were 0, 0.78125, 1.5625, 2.34375, 5.46875 and 10.15625. All six oracle checks passed, producing 18 pooled-score rows with zero excluded trials. The original prostate and bladder subsets received their expected organ labels under all three pooling rules. There were zero prostate-host prediction changes in this one-direction run; this small result is not evidence of general robustness.

Retrieved 22 artifact files and verified each SHA-256 against the remote copy. Independently loaded both `[128,512]` slide arrays and text arrays, checked model/physical compatibility, and recomputed every injection, oracle restoration and all 18 pooled scores locally. Contact sheets were visually checked for successful tissue extraction; this is technical image QC, not pathologist review. Evidence: [validated canonical smoke](../reports/conch_one_pair_smoke_22994635.json). Artifacts remain under ignored `results/smoke/conch_one_pair_22994635/` locally and `/work/nvme/bfqi/mhoda/floater-finder/smoke/one-pair-20261018T214721Z` on Delta.

Initial real smoke `22994469` also passed (`0:0`, 68 seconds). Inspection found a model-provenance defect: Python's transform representation included a process memory address. The adapter now removes only transient addresses and hashes the installed transform/tokenizer source files. The corrected run's image/text vectors match the initial run exactly; the initial artifacts are preserved separately and must not be mixed with the canonical-provenance artifacts. The current local suite passes **80 tests**, including this regression and login-node rejection.

Actual capped image-read/preprocessing/encoding/transfer times were 3.1934 seconds for 128 host tiles and 2.9457 seconds for 128 donor tiles, approximately 40.08 and 43.45 tiles/second. Model load took 4.7096 and 3.9772 seconds separately. These are observed subset measurements; they exclude WSI extraction, model load and text encoding and are not a whole-slide performance estimate.

A CPU-only bidirectional follow-up is submitted as `22994703`, reusing the canonical vectors, with two host directions, five seeds, six percentages and mandatory oracle recovery. It loads no model for inference and requests no GPU. Its completed outcome is recorded separately below.

## Ongoing execution authorization and runtime preparation

On October 18 the user explicitly authorized continued Delta job submissions for this plan without repeated permission requests. `AGENTS.md` records this authorization while retaining verified-account, one-GPU, credential and scientific-integrity safeguards. A subsequent bounded extension to two public development slides is recorded above; no bulk cohort or additional model was acquired.

A fresh shared-connection check succeeded on the local Mac as remote user `mhoda` on `dt-login04`. `accounts` returned `bfqi-delta-cpu` with 7,388 rounded hours and the GPU sub-allocation with 9 rounded hours; the user's queue was empty. These are snapshots. Both allocations were previously confirmed for the hackathon.

CPU preparation job `22994404` completed on `cn004` with exit `0:0`. It requested two CPUs, 8 GB memory and ten minutes from account/QoS `bfqi-delta-cpu`, partition `cpu`. It installed a private environment inheriting the site's PyTorch 2.8 module, using pinned CONCH source revision `141cc09c7d4ff33d8eda562bd75169b457f71a62`, OpenSlide Python `1.4.6`, OpenSlide binary `4.0.1.2` and ftfy `6.3.1`. Only approximately 2.9 MB of dependency wheels and 1.27 MB of official source were fetched; no new WSI or weights were downloaded. All three existing inputs were independently rehashed on the scheduled CPU node. The local CONCH tokenizer produced the expected `[1,128]` tokens offline. No model was loaded by this CPU job.

The measured WSI MPP values are 0.2527 in both axes for the prostate host and 0.2277 in both axes for the bladder donor. Their dimensions match the existing coordinate HDF5 attributes. Because these physical scales differ, the tiler uses fractional source boxes to export a common 256-micron field at 512 pixels. Original measured values remain in provenance; they are never overwritten to pretend the scanners match. Only the source `coords` datasets are read, never v1.5 feature values.

Environment: `/work/nvme/bfqi/mhoda/floater-finder/envs/conch-v1-20261018T214122Z`. Preparation output: `/work/nvme/bfqi/mhoda/floater-finder/runtime-preflight-20261018T214122Z`. Exact staged sources and resource requests are in [the CPU submission record](../reports/ncsa_runtime_submission_20261018T214122Z.json); verified headers/packages/checksums are in [the preflight report](../reports/ncsa_runtime_preflight_22994404.json).

The capped GPU smoke is submitted as job `22994469`: one A100, four CPUs, 16 GB memory and ten minutes on account `bfqi-delta-gpu`, QoS `bfqi-delta-gpu-mhoda`, partition `gpuA100x4`. It uses a separate immutable source snapshot and output directory. Submission does not establish successful inference; the completed result will be recorded separately. See [the submission record](../reports/ncsa_one_pair_submission_20261018T214407Z.json).

## Latest data discovery: complete cohorts, different encoder version

A further bounded inspection on October 18 found `/work/nvme/bfqi/shared/datasets/tcga_conch_v1.5`, containing 401 PRAD HDF5 files and 457 BLCA HDF5 files (401 and 386 distinct patient barcode prefixes respectively). Four sampled headers identify 768-dimensional `conch_v15` features with spatial coordinates and extraction settings. Public GDC metadata verified those four sampled slides' patient/project/organ mappings and diagnostic-slide status. No feature arrays or raw slides were read during this inspection.

This resolves the earlier absence of a shared bladder cohort **for CONCH v1.5**. It does not provide compatible inputs for the current CONCH v1/512-dimensional image–text experiment. The version mismatch, verified inventory, unsent organizer request and an exact **4.80 GB** original-v1 download alternative are recorded in [the next-experiment plan](next_experiment.md). The user subsequently approved the downloads, and all three inputs are now verified as recorded below. No new job was submitted.

## Approved input downloads: completed October 18

Execution was reconfirmed on the local Mac (`Darwin`, user `muneebhoda`). One successful shared-connection check identified `mhoda` on `dt-login04.delta.ncsa.illinois.edu`. The user explicitly authorized the 4.80 GB downloads and did not authorize a new job.

All three inputs were written beneath `/work/nvme/bfqi/mhoda/floater-finder/inputs/`, preserving existing work:

| Input | Verified destination relative to input root | Bytes | Integrity check |
| --- | --- | ---: | --- |
| Prostate host `TCGA-2A-A8VL` | `TCGA-PRAD/TCGA-2A-A8VL-01Z-00-DX1.2C2BD6EF-EC17-4117-AE89-A22B67AFB233.svs` | 1,713,266,379 | GDC MD5 matched |
| Bladder donor `TCGA-2F-A9KP` | `TCGA-BLCA/TCGA-2F-A9KP-01Z-00-DX1.3CDF534E-958F-4467-AA7E-FD3C5A86AAAA.svs` | 2,285,938,440 | GDC MD5 matched |
| Original CONCH v1 checkpoint | `models/conch_v1/pytorch_model.bin` | 802,235,437 | Pinned source SHA-256 matched locally and on Delta |

Total unique input bytes: **4,801,440,256**. The checkpoint revision is `f9ca9f877171a28ade80228fb195ac5d79003357`; SHA-256 is `40a9644b9ba0e83a74576e0a5e5f7313599fa9c9cdaf3c20f8a3e271b0e9ae7c`. It was downloaded through an already authenticated, access-approved Safari session and copied from the Mac to Delta. No token, cookie or credential file was extracted. The local download remains in `~/Downloads/pytorch_model.bin`; it is outside the repository.

Evidence: [approved plan and full checksums](../configs/ncsa_conch_v1_download_plan.json), [WSI download report](../reports/gdc_downloads_20261018.json), and [checkpoint transfer report](../reports/conch_v1_checkpoint_download_20261018.json). Final [storage verification](../reports/ncsa_inputs_verified_20261018.json) confirms mode `600` input files and owner-only access on new input directories (inherited setgid retained). Delta inherited group permissions were explicitly restricted after transfer. User quota remains unverified; these writes succeeded.

No WSI processing, model load, GPU inference or new Slurm job occurred. Physical calibration, WSI tiling and compatible runtime preparation remain necessary before requesting approval for a concrete one-pair scheduled smoke test.

## Latest GPU smoke test: completed

After the user authorized GPU testing and reconnected manually, one batch-mode check succeeded as `mhoda` on `dt-login01.delta.ncsa.illinois.edu`. The preflight queue was empty and the personal NVMe directory was writable. The prepared script was submitted once via stdin to `sbatch --parsable`; no remote repository clone or package installation was needed.

Job `22957101` used `bfqi-delta-gpu`, QoS `bfqi-delta-gpu-mhoda`, partition `gpuA100x4`, one GPU, one CPU, 2 GB memory and a two-minute limit. Slurm automatically assigned reservation `sup-30434-17`. An initial pending reservation reason cleared without intervention. The job and both `srun` steps completed with exit code `0:0` on `gpua038`; job elapsed time was five seconds. The driver query reported `NVIDIA A100-SXM4-40GB`, driver `595.71.05`.

Evidence: [`reports/gpu_smoke_22957101.json`](../reports/gpu_smoke_22957101.json) and the copied [stdout log](../reports/gpu_smoke_22957101.log). The original stdout is `/work/nvme/bfqi/mhoda/floater-smoke-22957101.out`. This also verifies a small log write in that directory. It does not establish model checkpoint availability, CUDA tensor execution, CONCH inference, or dataset access.

## Next stage: CONCH service preflight

**Latest result: hosted CONCH smoke passed again, and both runs' artifacts are retrieved.** On October 18 the user restored shared SSH and explicitly requested another run using the service credential. Identity verified as `mhoda` on `dt-login04.delta.ncsa.illinois.edu`. The previous October 17 report/vectors were retrieved and independently validated first. One fresh authenticated two-tile run then returned `passed`, saving `/work/nvme/bfqi/mhoda/conch-service-smoke-20261018T205624Z/smoke.json` and `embeddings.json`.

Both fresh artifacts were copied to the ignored local directory `results/smoke/conch_service_20261018T205624Z/` and independently checked: two rows, 512 dimensions, all finite values, norms `0.9999999680936702` and `1.0000000028404457`. The vectors exactly match the previous run on the same inputs. The fresh request took `0.14031214600254316` seconds for the HTTP round trip; this is not GPU throughput. The credential was used only at the hidden prompt and was not saved in repository files or reports. No new Slurm job or model/dataset download was needed.

The live unauthenticated OpenAPI schema confirmed only `/health`, `/embed`, and `/classify`, with image and prompt request fields. It exposes no text-embedding or checkpoint-provenance endpoint. These results verify hosted image encoding, not a scientific contamination result or independent model checkpoint identity. See the [latest evidence](../reports/conch_service_smoke_20261018T205624Z.json) and [retrieved earlier result](../reports/conch_service_smoke_20261017T223436Z.json).

The earlier `Permission denied` during artifact retrieval is resolved. To review the latest evidence from the local checkout:

```sh
cat reports/conch_service_smoke_20261018T205624Z.json
```

The remaining paragraphs record preflight and troubleshooting history, followed by instructions for any future rerun.

The user confirmed individual Hugging Face CONCH access. The supplied host and port respond over **HTTP**, at `http://gpub055.delta.ncsa.illinois.edu:8000`; an HTTPS handshake failed. An unauthenticated `/health` request from Delta returned `status=ok`, `model=conch`, `device=cuda`. One capped `/embed` request without an API key returned **401**. It was not retried. This verifies service reachability and its reported identity, not successful inference or independent model/checkpoint provenance.

`module load pytorch-conda/2.8` succeeded. Package metadata reports Python 3.11.13, PyTorch 2.8.0+cu128, NumPy 2.2.6, Pillow 11.3.0 and PyYAML 6.0.2. CONCH, OpenCLIP and TRIDENT distributions were absent from this inspected environment. PyTorch was not imported or executed on the login node.

The existing PathGen metadata at `/projects/bfqi/shared/datasets/pathgen_dataset/PathGen-2k_samples.json` contains 2,141 tile records from ten slides. Public GDC file-metadata lookup matched all ten file IDs to their slide names, patients and projects. The image directory contains 2,141 PNG files. One case is TCGA-PRAD (`TCGA-H9-A6BY`, file ID `b8c468ef-48ae-4abd-8590-2c25233c08a7`) with **208** PNG tiles; no TCGA-BLCA case occurs in this ten-slide sample. This does not establish that BLCA data are absent elsewhere. Physical coordinate units, scale, magnification, report linkage and independent diagnostic-slide status remain unverified. No captions or clinical reports were copied.

Evidence: [preflight report](../reports/ncsa_preflight_20261017.json), [public metadata inventory](../reports/ncsa_pathgen_inventory_20261017.csv), and [GDC API documentation](https://docs.gdc.cancer.gov/API/Users_Guide/Search_and_Retrieval/).

The standard-library [two-tile smoke client](../scripts/conch_service_smoke.py) and [verified image manifest](../configs/ncsa_prad_service_smoke.csv) were copied, with matching SHA-256 hashes and owner-only permissions, to `/u/mhoda/floater-finder/scripts/conch_service_smoke.py` and `/u/mhoda/floater-finder/configs/ncsa_prad_service_smoke.csv`. These are two staged files, not a full Git checkout or project installation. The deployed `--help` check succeeded. All 64 local tests passed, including capped input, invalid-vector rejection, failure without authentication retries, preservation of existing output, and exclusion of the API key from saved artifacts.

If already logged into **Delta**, run the launcher below and enter the **organizer's CONCH service API key** from `#compute-issues` at the hidden prompt. The launcher supplies the verified plain URL and chooses a new timestamped output directory:

```sh
bash /u/mhoda/floater-finder/scripts/run_ncsa_service_smoke.sh
```

From a **Mac Terminal** that is not already logged into Delta, use:

```sh
ssh -t ncsa-floater 'bash /u/mhoda/floater-finder/scripts/run_ncsa_service_smoke.sh'
```

Follow-up diagnosis found Markdown link syntax in the pasted `--endpoint` argument. The original generic startup message also hid a second condition: the fixed output directory already existed, with a saved user-run report recording `authentication_required`, HTTP 401. The client now reports endpoint, existing-output and tile-input errors separately before requesting a key. The [launcher](../scripts/run_ncsa_service_smoke.sh) avoids manual URL formatting and fixed-directory reuse. Thirteen targeted script tests passed. The deployed client was backed up and updated only after its previous source hash matched; no user modifications were overwritten. The launcher does not resolve service-key authentication failures, and no new inference was attempted during this repair.

The key is held in memory for the request and is not passed as a command argument or saved. The script refuses noninteractive input so a hidden prompt cannot fall back to echoing the key. It makes a lightweight HTTP request to the organizers' compute-node service; it does not instantiate a model on the login node or submit a new Slurm job. It expects two finite, unit-normalized 512-dimensional image vectors and writes a separate connectivity report. The successful authenticated run is recorded at the start of this section.

The published service interface exposes image vectors and winning-label classification responses, but no text vectors, full per-class scores, checkpoint hash or exact preprocessing provenance. A successful smoke test therefore remains separate from research artifacts. Full contamination/detector experiments still require those verified inputs, a suitable bladder donor and independent development/evaluation patients.

## Earlier implementation-session status

The single new connection check used `ssh -o BatchMode=yes -o ConnectTimeout=8 ncsa-floater 'whoami && hostname'`, bounded by a 15-second local process timeout. It timed out with no identity output. NCSA is temporarily unavailable for this implementation session; no authentication retry or SSH configuration edit was made. The successful identity/allocation/storage observations below are from the earlier setup session and were not reverified after this timeout.

Local development proceeded independently. A second, unsubmitted draft at [`scripts/slurm/conch_encode.sbatch`](../scripts/slurm/conch_encode.sbatch) requests account `bfqi-delta-gpu`, QoS `bfqi-delta-gpu-mhoda`, partition `gpuA100x4`, one GPU, four CPUs, 16 GB memory and five minutes for at most 128 already-tiled images. It needs a verified remote checkout, checkpoint, tile manifest, slide metadata and new output path. The module was unverified during that earlier implementation session; later checks are recorded above.

## Local execution and SSH

- Execution environment: the user's local Mac, macOS 26.6.2, local user `muneebhoda`.
- Local checkout: `/Users/muneebhoda/Documents/Masters - Fall 2026/Ashby Hackathon`.
- Repository: <https://github.com/MuneebHoda/floater-finder>.
- SSH alias: `ncsa-floater`; configured host: `login.delta.ncsa.illinois.edu`; configured user: `mhoda`.
- The user completed password/Duo authentication in their own Mac Terminal. Connection sharing subsequently succeeded with:

  ```sh
  ssh -o BatchMode=yes ncsa-floater 'whoami && hostname'
  ```

- Latest observed remote identity: `mhoda` on `dt-login04.delta.ncsa.illinois.edu` (Delta) on October 18; the October 17 GPU/service preflights used `dt-login01`. The login hostname is a service name; the observed backend may change.
- Host-key verification remains enabled (`StrictHostKeyChecking ask`); agent forwarding is disabled. The control-socket directory is `~/.ssh/cm`, mode `700`; SSH configuration is mode `600`.
- Existing SSH entries were preserved and backed up outside this repository before adding the alias.
- If a batch-mode SSH command needs authentication again, stop and have the user reconnect manually with `ssh ncsa-floater`. Never request credentials or repeatedly retry authentication.

## Allocations and Slurm

Immediately before GPU job submission, the site's `accounts` command returned these balances. The user confirmed that **both allocations belong to the hackathon**. Balances are rounded snapshots, not a guarantee of future availability.

| Slurm account | Balance (hours) | Deposited (hours) | Site description | Default QoS from Slurm association |
| --- | ---: | ---: | --- | --- |
| `bfqi-delta-cpu` | 9,333 | 11,039 | `2025 ashby prize in...` (truncated by the site command) | `bfqi-delta-cpu` |
| `bfqi-delta-gpu` | 10 | 10 | Sub-allocation `mhoda`; marked `*` by `accounts` | `bfqi-delta-gpu-mhoda` |

`sacctmgr -n -P show assoc where user=mhoda format=Cluster,Account,User,Partition,QOS,DefaultQOS` confirmed both account names on cluster `delta`. It also listed `noalloc`, which is not selected for project work. The username `mhoda` is not the Slurm account name.

The [official hackathon compute guide](https://github.com/ncsa/ashby-hackathon-2026/blob/main/HACKATHON_COMPUTE.md#5-gpu-jobs) specifies `bfqi-delta-gpu` with partition `gpuA100x4` for event GPU jobs, one GPU per team at a time, and no explicit reservation flag. The smoke-test proposal follows these instructions. The site's `gpuA100x4` partition being the default does not remove the need to specify the intended account.

`squeue --me` returned a header with no jobs. `sinfo -o "%P|%a|%l|%D|%G"` reported the following partitions as `up`:

| Partition family | Observed variants | Time limit |
| --- | --- | --- |
| `cpu` | base, `-interactive`, `-preempt` | 48 hours; interactive 1 hour |
| `gpuA100x4` | base (site default), `-interactive`, `-preempt` | 48 hours; interactive 1 hour |
| `gpuA100x8` | base, `-interactive` | 48 hours; interactive 1 hour |
| `gpuA40x4` | base, `-interactive`, `-preempt` | 48 hours; interactive 1 hour |
| `gpuH200x8` | base, `-interactive` | 48 hours; interactive 1 hour |
| `gpuMI100x8` | base, `-interactive` | 48 hours; interactive 1 hour |
| `full` | base | 24 hours |

Listed partitions and account associations do not establish that a particular job can be scheduled, that a GPU has been allocated, or that CUDA/CONCH works.

## Verified directories and documentation

Initial directory checks were limited to the user's home, the hackathon allocation roots, and relevant shared directories. No filesystem-wide search or model-file read was performed. The later bounded metadata and two-tile service checks are recorded above.

| Location | What was verified |
| --- | --- |
| `/u/mhoda` | Remote home and initial working directory; no non-hidden entries at inspection time. |
| `/projects/bfqi` | Exists and is a directory; relevant top-level entries inspected. |
| `/projects/bfqi/shared` | Exists; its only non-hidden entry was `datasets`. |
| `/projects/bfqi/shared/datasets` | Exists; its non-hidden entries were the three directories listed below. The listing was slow but completed; no cancellation signal was sent. |
| `/projects/bfqi/shared/datasets/NCT-CRC-HE-100K` | Directory listed; contents, provenance, and suitability for this milestone were not checked. |
| `/projects/bfqi/shared/datasets/pathgen_dataset` | Directory listed; contents, provenance, and suitability for this milestone were not checked. |
| `/projects/bfqi/shared/datasets/pathmmu` | Directory listed; contents, provenance, and suitability for this milestone were not checked. |
| `/projects/bfqi/shared/datasets/NCT-CRC-HE-100K/data-samples` | Exists and is a directory; permission checks report readable and not writable. Tile contents were not opened. |
| `/projects/bfqi/mhoda` | Exists; no non-hidden entries at inspection time. |
| `/work/nvme/bfqi` | Exists; permission checks report readable and writable. |
| `/work/nvme/bfqi/mhoda` | Initially empty and readable/writable. The approved driver smoke job subsequently wrote its stdout log successfully here. The event guide designates this personal NVMe area for data and outputs. |
| `/work/hdd/bfqi` | Exists and is a directory; relevant top-level entries inspected. |
| `/work/hdd/bfqi/mhoda` | Exists; no non-hidden entries at inspection time. |
| `/projects/bfqi/data_test_simple` | Exists and is a directory; contents and intended use were not checked. |
| `/projects/bfqi/data_test_difficult` | Exists and is a directory; contents and intended use were not checked. |

`WORK`, `SCRATCH`, `PROJECT`, and `PROJECTS` were unset in the initially inspected remote shell. The smoke job used the verified personal NVMe directory for its working directory and small log. Persistent Floater Finder output organization and any shared team directory remain undecided. Bulk output/quota behavior has not been tested.

The local `2026_Ashby_Hackathon_Welcome.pdf` was checked, including pages 21-24. It states that pretrained weights and datasets are preloaded but supplies no concrete shared-repository, CONCH-weight, or output paths. Its Box resources link could not be accessed by the web tool. The user subsequently clarified that no compute README was available and requested a search.

That search located the **official toolkit repository**, <https://github.com/ncsa/ashby-hackathon-2026>. Its [README](https://github.com/ncsa/ashby-hackathon-2026/blob/main/README.md) points students to [HACKATHON_COMPUTE.md](https://github.com/ncsa/ashby-hackathon-2026/blob/main/HACKATHON_COMPUTE.md). The inspected compute-guide blob SHA was `97d44f539c379b4591e8f93fec85dd91b6cba693`.

Verified from that guide and kept distinct from execution checks:

- Use the existing shared datasets in place; use `/work/nvme/bfqi/mhoda` for personal data and outputs. The guide reports filesystem problems with `/work/hdd` this weekend; its existence above is not a recommendation to use it.
- The documented environment is `pytorch-conda/2.8`, with `open_clip_torch` and CONCH packages for self-hosted inference. Module/package availability was not tested, and nothing was installed.
- The guide documents individual gated CONCH access and first-use weight downloads. It does not identify a concrete preloaded CONCH checkpoint path. This setup did not inspect credential files, authenticate to Hugging Face, load a model, or download weights.
- Hosted pathology services are described, but no credentials or connection files were read and no service inference request was made.

Follow-up checks on 2026-10-17 confirmed the distinction between individual access approval and obtaining another checkpoint copy. The current compute guide requires each person to obtain their own Hugging Face CONCH approval even when using the organizers' hosted service. The [student guide](https://github.com/ncsa/ashby-hackathon-2026/blob/main/STUDENT_GUIDE.md) documents a hosted CONCH endpoint on Delta through Sunday 6:00pm, with connection information supplied in `#compute-issues`. This route would not require a personal checkpoint download. The endpoint's current availability, model provenance and compatibility with Floater Finder remain unverified; the current project adapter accepts an existing checkpoint and is not connected to this service.

The shared SSH connection was reverified as `mhoda` on `dt-login01.delta.ncsa.illinois.edu`. A bounded, metadata-only inspection found only `datasets` under each of `/projects/bfqi/shared` and `/work/nvme/bfqi/shared`. The user's home had no non-hidden entries, and `/work/nvme/bfqi/mhoda` contained only the completed smoke-test log. The explicit CONCH cache-directory candidates under `/u/mhoda/.cache/huggingface/hub` and `/work/nvme/bfqi/mhoda/hf/hub`, checking both repository-name capitalizations, did not exist; `HF_HOME` and `HF_HUB_CACHE` were unset. No checkpoint was found in these checked locations. This does not establish that no staged checkpoint exists elsewhere. No credential files, other users' caches, model contents or dataset contents were read; no downloads, inference or job submissions occurred during this follow-up.

A bounded, filename-only README search under `/projects/bfqi` stopped at depth three and excluded datasets, model directories, environments, and hidden directories. Some directories were inaccessible; other teams' documents were not opened. No official toolkit checkout or Floater Finder deployment path has been designated for this user, and no remote clone was created.

Official references checked:

- [Delta job and partition documentation](https://docs.ncsa.illinois.edu/systems/delta/en/latest/user_guide/running_jobs.html).
- [Delta storage documentation](https://docs.ncsa.illinois.edu/systems/delta/en/latest/user_guide/data_mgmt.html), which documents allocation-specific storage under `/projects` and `/work/hdd`.

## Driver smoke script: completed

Review [`scripts/ncsa_smoke.sbatch`](../scripts/ncsa_smoke.sbatch). It proposes one NVIDIA GPU on the event's documented `gpuA100x4` partition, one CPU, 2 GB memory, and a two-minute limit, charged to the verified GPU account and QoS. It prints a compute-node hostname and queries GPU identity/driver information through `srun`. It loads no models and reads no datasets.

The working directory was `/work/nvme/bfqi/mhoda`; the completed log is `floater-smoke-22957101.out` there. The user approved the run. Bash syntax, actual Slurm scheduling and the driver query succeeded; see the evidence above. Future submissions still require authorization.

This successful scheduled run verifies Slurm GPU allocation and driver visibility only. CUDA/PyTorch execution and CONCH inference still require their own checks and verified inputs.

## Unresolved inputs

- Intended remote Floater Finder/toolkit checkout path; the official upstream repository is now identified above.
- Larger-cohort runtime and throughput behavior; pinned CONCH v1 image/text compatibility, source/checkpoint provenance and scheduled capped inference are now verified above. Python/module availability and the user's individual access are now recorded above. The hosted service requires its separate organizer API key, entered only in the user's Terminal.
- A larger representative development cohort and fresh held-out evaluation patients for a meaningful pilot. The four-patient smoke now verifies separate calibration/evaluation, matching v1 image/text artifacts and physical tiling. Shared v1.5 feature values cannot be used with v1. Report linkage and normalized institution mapping remain unavailable.
- Bulk output/quota behavior on the documented personal NVMe area, plus the persistent Floater Finder output layout and any shared team location. A small smoke-test log write succeeded.
- Transfer of detector settings to unseen patients, larger spatial samples, scanner variation and clinically annotated native floaters. Scheduled CUDA/PyTorch and original CONCH v1 image/text encoding are already verified for the capped smoke.

The exact next command from the local checkout is `cat configs/ncsa_expanded_pilot_download_plan.json` to review the concrete, approved acquisition manifest. Dependency maintenance and the bounded GPU compatibility check are verified; broader research still needs completed acquisition/integrity checks, broader sampling, a cohort runner and frozen calibration protocol. The current evaluation set must not be used for threshold tuning.

Keep `AGENTS.md` safeguards and the recorded continuing authorization in force. Bounded CONCH plan jobs and the two development inputs are covered; bulk cohorts or additional models need separate scope authorization. Preserve the user-authorized private-repository audience for setup details and project documents.


## Fresh Radboud60 CPU intake — verified October 21

Approved acquisition 23070667 and CPU tiling 23070755/23070937/23071013/23073158/23073380/23081800 completed `0:0`. Full metadata verification passed 60 slides, 25,915 tiles and 60 masks. All 20 high-grade slides have sampled GP4/5 annotation, totaling 4,209 distinct positive tiles. These are annotation observations, not predictions. Root-job accounting totals 0.7572 allocated CPU-hours.

Verified output root: `/work/nvme/bfqi/mhoda/floater-finder/panda-fresh-baseline/radboud60-v1`. The exact 60-directory encoding list is `tiling-directories.json`; complete readiness is `reports/cpu-readiness-v1.json` (SHA256 `2547519afadbb0615cd0691bf550ec4c0db117b32069ab360641bd7447654790`). All payloads and detailed artifacts remain on Delta; none were copied to the Mac. Source is `bfd4416936d2c35d764d6fd46e1017f110ef48db` in `/u/mhoda/floater-finder/releases/panda-fresh-baseline-v1-20261021T023142Z/source`. See the [execution record](../reports/panda_fresh_cpu_execution_v1.md) for provenance limits and exact unsubmitted GPU/CPU proposals. Fresh embeddings, clean predictive performance and patient independence remain unverified; the original 24 final-test predictions are sealed.

Final lightweight recheck: queue empty; both interactive partitions up with one-hour limits. `accounts` reported 5,287 rounded CPU hours and 8 GPU hours remaining in the previously selected CPU/GPU allocations (shared snapshots, not reservations). No GPU submission was made.


## Fresh GPU and frozen-baseline stage — verified October 21

The user separately approved the exact 30-minute one-A100 encoding plus 20-minute CPU verification/frozen-scoring scope. GPU 23081929 completed 0:0 in 743 seconds (one GPU, 4 CPUs, 16 GB; 0.2064 GPU-hours). CPU 23082231 completed 0:0 in 66 seconds (2 CPUs, 8 GB, no GPU). All 60 slides / 25,915 512D embeddings passed scheduled array/hash/provenance checks before scoring; original 24 final-test predictions remain sealed. Detailed outputs stay under the verified fresh root; no files were copied to the Mac. See the [result record](../reports/panda_fresh_baseline_results_v1.md) for observed performance and limits.

Remote artifact-verification SHA256: `242050b5398cc0473e641760d1aed96dbae46b871a8feebefb653de9318b4d4e`. Baseline completion SHA256: `8b6d86b01d40fd05651211de5f8faee50806e3a1dd814bb18d44cccd7f6e9248`. Independent small-result inspection SHA256: `7064d2962d983c97e0cff45d96f267aba3b9e45a081cb440ed1c43811ae527b0`. No further encoding/evaluation job is covered by this consumed scope.


## 2026-10-21 — training numeric-context/native controls

Verified local Darwin and shared SSH identity `mhoda` / `dt-login04.delta.ncsa.illinois.edu`. Site `accounts` showed bfqi-delta-cpu 4,875 hours and bfqi-delta-gpu sub-allocation mhoda 8 hours; cpu-interactive up with one-hour maximum, own queue empty. No GPU submitted. CPU **23102229 completed 0:0 in 12s**, 2 CPUs/4 GB/five-minute cap, node cn095, MaxRSS 70,576 KiB, 0.006667 allocated CPU-hours. It read only the prior sealed training audit JSON and filtered manifest IDs; no image/array/prediction work.

Source `0340d605acd6bee8ea913d09307a326750cb1a5c` at `/u/mhoda/floater-finder/releases/panda-context-safety-v1-20261021T170007Z/source`, all 253 files verified. New output `/work/nvme/bfqi/mhoda/floater-finder/panda-review/context-safety-v1` has 73 sealed checkpoints /76 events for 72 training slides. Completion receipt `/work/nvme/bfqi/mhoda/floater-finder/panda-review/context-safety-completion-v1.json`, SHA256 `7bc8726d4fc2ed8ce0bab3d920b3e8b6df0f2ef18d57892c5d2b998f255dc0a4`. Original audit receipts, legacy sources and final-test seal remain preserved. [Findings and unresolved physical-context/foreignness validity](../reports/panda_context_safety_results_v1.md). Queue empty on completion; no extra job or local data download.


## 2026-10-21 — saved-training dependence report export

Local Darwin and shared SSH `mhoda` / `dt-login04.delta.ncsa.illinois.edu` verified. Latest site account snapshot: bfqi-delta-cpu 4,860 hours, bfqi-delta-gpu sub-allocation mhoda 8 hours; cpu-interactive up with one-hour maximum, own queue empty. CPU **23102479 completed 0:0 in 16s**, node cn095, 2 CPUs/4 GB/five-minute cap, Python MaxRSS 121,300 KiB, 0.008889 allocated CPU-hours. No GPU, new predictions, images/arrays or download.

Source `1a388ef47c393afff11e73d53e05783a6a4723d5` at `/u/mhoda/floater-finder/releases/panda-dependence-export-v1-20261021T172655Z/source`, all 260 files verified. Remote report index `/work/nvme/bfqi/mhoda/floater-finder/panda-review/dependence-report-v1/index.html`; 72 HTML +72 reviewer JSON +index verify with 73 sealed checkpoints /76 events. All 145 rendered files have observed mode 0660, recorded without permission changes. Completion `/work/nvme/bfqi/mhoda/floater-finder/panda-review/dependence-export-completion-v1.json`, SHA256 `7ae084249f6516e181b44a04c0695f976405a4c165baecd0d8ba8788acf69a76`. [Results and unresolved visual/clinical validity](../reports/panda_dependence_export_results_v1.md). Original protocol/main/legacy source and final-test seal preserved; queue empty and bounded scope complete. All detailed artifacts remain remote.


## 2026-10-21 — bounded original-training PNG galleries

Darwin and shared SSH `mhoda` / `dt-login04.delta.ncsa.illinois.edu` verified. Latest account snapshot: bfqi-delta-cpu 4,850 hours and bfqi-delta-gpu sub-allocation mhoda 8 hours; cpu-interactive up with one-hour maximum. CPU **23102636 completed 0:0 in 23s**, node cn099, 2 CPUs/4 GB/five-minute cap, Python MaxRSS 316,776 KiB, 0.012778 allocated CPU-hours. No GPU, new model call or local download.

Source `ec5a71dde4b566393ddfa4b53b5e1b6a8eec3d6d` at `/u/mhoda/floater-finder/releases/panda-preview-export-v1-20261021T174522Z/source`, all 267 files verified. New index `/work/nvme/bfqi/mhoda/floater-finder/panda-review/dependence-previews-v1/index.html`: 72 training slide galleries /389 components, 1,638 original PNG byte copies /2,605 references, 101,466,949 bytes. All 1,783 output files and 72 source receipt groups verify; output mode 0660 preserved, own queue empty. Completion `/work/nvme/bfqi/mhoda/floater-finder/panda-review/preview-export-completion-v1.json`, SHA256 `05c148adb417d907673d5fd8d099960690a5e78a9a00e9ef05deb20246344c02`. [Preservation proof and unresolved visual/clinical validity](../reports/panda_preview_export_results_v1.md). No old report or data overwritten; all images/detailed outputs stay remote and original test seal remains closed. Bounded scope complete.


## 2026-10-21 — saved native/synthetic training controls

Local Darwin and shared SSH identity `mhoda` / `dt-login04.delta.ncsa.illinois.edu` verified. Site account snapshot: bfqi-delta-cpu 4,833 hours and bfqi-delta-gpu sub-allocation mhoda 8 hours, the previously selected allocations; cpu-interactive up with one-hour maximum. CPU **23104084 completed 0:0 in 21s**, node cn137, 2 CPUs/4 GB/five-minute cap, Python MaxRSS 244,700 KiB, 0.011667 allocated CPU-hours. No GPU or new predictions.

Source `24364b4946de211ae8b608f7bf7d710408aca112` at `/u/mhoda/floater-finder/releases/panda-paired-controls-v1-20261021T181828Z/source`, all 273 files /ten input receipts verified. New index `/work/nvme/bfqi/mhoda/floater-finder/panda-review/paired-control-audit-v1/index.html`: 24 known-provenance training pairs /16 reused donors, 250 unchanged PNG assets /384 references, 16,981,004 bytes, 299 files verified. Completion `/work/nvme/bfqi/mhoda/floater-finder/panda-review/paired-controls-completion-v1.json`, SHA256 `44a79eddff734526a00194e88b9c328cc5351d8874545bbc2dca68315e1a2eb1`. Previous galleries/reports, all source identities and original test seal are preserved; own queue empty, no duplicate/retry or local data download. First incomplete source archive was retained after pre-submission metadata failure. [Observed audit findings and unresolved visual/foreignness validity](../reports/panda_paired_control_audit_results_v1.md). This bounded scope is complete; all pixels/detailed artifacts remain remote.


## 2026-10-21 — blank qualitative-review metadata packet

Darwin and the shared SSH identity `mhoda` / `dt-login04.delta.ncsa.illinois.edu` verified once before remote work. Pushed source `e29a7a3fa56179451d6d2f123fa6add9ba66f619` was staged at `/u/mhoda/floater-finder/releases/panda-expert-review-v1-20261021T184909Z/source`; all 258 files and frozen source preflight verified. Metadata-only preparation used the existing CPU runtime, without Slurm/GPU submission or image/array/model reads.

Verified new packet `/work/nvme/bfqi/mhoda/floater-finder/panda-review/expert-review-worksheet-v1` has exactly `worksheet.blank.json`, `review_guide.md` and `preparation.json`. It contains 24 original training case references /16 reused donors, all human answers null and **0/24 reviewed**. Preparation SHA256 `cd3dc7edd023b4a26e08ecf4c27f654c0b066575e7be1f249fdcba96e32203af`. Independent administrative verification `/work/nvme/bfqi/mhoda/floater-finder/panda-review/expert-review-worksheet-verification-v1.json`, SHA256 `e741fd742ee7d59499753c6e5114a33559569ed344ad556ed1490c6a988850e4`. Old audit receipts and 48 public case files match; original final output absent. No local data/result file download, expert assessment, reviewer contact or model operation. [Commands, provenance and unresolved human/visual/foreignness validity](../reports/panda_expert_review_preparation_v1.md). Blank preparation is complete; detailed response copies remain remote and must preserve the original packet.


## 2026-10-21 — fixed-support training candidate executed

After the user confirmed manual reconnection, local Darwin and shared identity `mhoda` / `dt-login04.delta.ncsa.illinois.edu` verified once. Site snapshot: bfqi-delta-cpu 4,714 hours and GPU sub-allocation mhoda 8 hours; CPU interactive up with one-hour maximum, own queue empty. Runtime source `204c194524943e75813e966f300e39dbb5e63bcb` was staged read-only at `/u/mhoda/floater-finder/releases/panda-stable-context-v1-20261021T214940Z/source`, all 265 files /seven input receipts match.

CPU **23108680 completed 0:0 in 21s**, node cn137, 2 CPUs/8 GB/ten-minute cap, Python MaxRSS 365,672 KiB, 0.011667 allocated CPU-hours, zero GPU. New verified output `/work/nvme/bfqi/mhoda/floater-finder/panda-review/stable-context-v1`: 96 case checkpoints +summary /100 events. Primary detects 3/24, source-exact hypothetical recovery 1/12, clean alerts 8/72; both frozen candidate/comparator fail utility. [Denominators, uncertainty, source and exact command](../reports/panda_stable_context_results_v1.md). Completion `/work/nvme/bfqi/mhoda/floater-finder/panda-review/stable-context-completion-v1.json`, SHA256 `c5eeca3dd295128edff570333973f6f8d79776fdec3118e56e51d7817d9e3abe`.

No new model/encoder inference, GPU, download, draw, fitting of a disease model, duplicate/retry or held-out/fresh prediction. All raw data/metrics remain remote; source/input receipts, historical evidence and final-test seal intact, own queue empty. User confirmed no reviewer available; blank worksheet unchanged at 0/24 reviewed, expert review stays pending. This bounded stage is complete and does not authorize another job or opening final predictions.


## Expanded-program resource audit — October 21, 18:43 CDT

Verified identity `mhoda` / `dt-login04.delta.ncsa.illinois.edu`. Own QoS `bfqi-delta-gpu-mhoda` exposes 600,000 billing-TRES minutes deposited, 95,500 used, 504,500 remaining = 8.4083333 batch A100-hour equivalents. Root-job accounting and raw QoS usage reconcile exactly; `accounts` rounds to 8 and `jobcharge` displays rounded rows. Live `gpuA100x4` maximum 48h / GPU weight 1000; interactive maximum 1h / GPU weight 2000. CPU/memory weights and MAX_TRES billing mean the planned one-A100/4-CPU/16-GiB batch is GPU dominated. Association has no partition restriction and historical normal A100 batch jobs succeeded. New test-only admission and current checkpoint hash are still pending; connection expired before admission testing. No authentication retries. No new GPU or data download. [Verified charge ledger](../reports/panda_gpu_program_metadata_audit_v1.json), [prepared scope and exact paths](../reports/panda_gpu_research_program_preparation_v1.md).


### Reconnected submission — October 21, 19:07 CDT

One shared test verified `mhoda` on `dt-login03.delta.ncsa.illinois.edu`. Normal A100 batch scheduler admission now passes for one A100/4 CPUs/16 GiB/15 min under `bfqi-delta-gpu` / `bfqi-delta-gpu-mhoda`; no GPU job was submitted. Test-only advisory A100 start was October 29 and CPU start October 26, both beyond the deadline. Actual new CPU **23109667** is PENDING (Priority) with no start estimate at submission. Its 4-CPU/16-GiB/30-minute source snapshot and exact command are verified; existing pilot jobs remain queued unchanged. All 73 source files match the frozen manifest. Current model rehash and real dedup counts are still pending scheduled execution. [Submission status and paths](../reports/panda_gpu_program_cpu_execution_v1.md).


### Approved Stage B profile queued — October 21, 19:39 CDT

GPU profile **23109849** is PENDING (Dependency) behind successful CPU23109667 and terminal pilot GPU23109340. Verified normal A100 account/QoS/partition, one GPU/4 CPUs/16 GiB/15 min, GPU-dominated billing1000, unchanged73-file scientific source and five-file launcher. User approval covers this frozen benchmark’s profile plus conditional remaining ranges within45 total batch minutes/0.75 billed equivalents; other GPU stages remain gated. Balance at19:38 remains8.4083333 equivalents. Actual input receipt hash/count and profile measurements await scheduled execution. [Exact command and all source/authorization receipts](../reports/panda_pixel_program_gpu_submission_v1.md).


### CPU capacity and node-health diagnosis — October 21, 23:56–23:57 CDT

Read-only Slurm inspection found the normal CPU pool had 136 nodes: 76 draining, 55 allocated, four completing and one reserved; no idle node group was listed. Draining-node reasons included 45 `/sw` filesystem node-health-check timeouts and 14 terminated node-health checks. The interactive CPU pool was similarly constrained (77 draining, 55 allocated, four completing, one reserved). These are observed scheduler/node-health readings, not an official outage announcement or a confirmed repair timeline. Current CPU jobs23109277/23109667 still report Priority; their GPU dependents23109340/23109849 have not started. Allocation balance is not reserved hardware capacity. Old failed CPU23109222 remains COMPLETING on cn018, whose state includes DRAIN and whose recorded reason is a terminated health check; direct causality for other jobs is not established. Latest advisory pilot CPU start at this inspection was October22 16:53 CDT, not a guarantee; the10k CPU had no estimate. No job settings, scripts, priorities, dependencies, resources or submissions were changed.
