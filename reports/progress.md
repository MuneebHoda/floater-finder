# Floater Finder progress

## Fresh baseline preparation — October 20

The fixed 60-slide Radboud proposal now has a legacy-compatible execution manifest, exact 120-file acquisition plan, four frozen predictor hashes, default metadata-only preflight and CPU-only clean prediction runner. Original training-selected linear primaries remain primary for both tasks; corrected historical cancer top-5% and grade mean are fixed comparators. The fresh cohort is slide-disjoint from 129 exposed IDs; patient independence is unknown. Cancer uses all 60, low/high excludes benign and uses 40. No detector or final-readiness claim is inferred.

Source **bfd4416** was separately staged and all **226 files verified**. The Delta preflight verified 60 IDs/four models/129 exclusions without predicting. **284 tests pass**, after rebuilding the installed package to match source. Bounded read-only Delta checks found zero of the 120 image/mask files present, existing acquisition/CPU runtimes, and an empty user queue. No WSI, new embedding, download or job was launched. Main, the 33 frozen historical files, final protocol and submission files remain unchanged.

The concrete pending request covers **1,348,184,402 catalog TIFF bytes** plus acquisition and six serialized CPU input/tiling chunks (at most five requested CPU-hours total, first-chunk profiling gate). It includes no GPU or prediction job. Future encoding needs actual input/tile verification and separate approval. [Frozen protocol, resource table and strict data gates](../docs/panda_fresh_baseline_v1.md); [exact staged commands, hashes and site observations](panda_fresh_baseline_preparation_v1.json). No fresh scientific outcomes are claimed.

## Paired-placement checkpoint — October 20

Frozen source `bbc2845`, CPU **23069409 completed 0:0 in 271 seconds**, using 0.15056 allocated CPU-hours and no GPU. A separate hash-verified snapshot and sealed 1,657-checkpoint registry preserve 825 saved positive-dose interventions, four clean anchors, all 327 previous exclusions and 1,499 verified PNG exports. Geometry/pair definitions precede detector scoring. The numeric overlap validator fix has isolated regression evidence and does not admit old exclusions.

The primary finds **0/607 foreign instances /0/10,610 foreign-tile observations** and recovers **0/39 induced errors**. The 88 complete triplets contain 59 foreign groups and 29 shams; all seven methods find 0/59 in each paired foreign mode. A secondary component-neighbor rule finds three all-case instances outside common addition triplets or in replacement carriers; distant-NN5's five sham alerts cause three hypothetical prediction errors on one host. There is no useful policy or outcome-guided retuning. Only two hosts per task, repeated doses/donors and three clean native-cancer components limit interpretation. [Full results, denominators, topology, all methods and exact verification command](panda_detector_placement_v1.md).

**272 tests pass** with warnings treated as errors. All 33 frozen historical files, rejected final protocol, main and submission/presentation artifacts are preserved. No downloads, new encodings, calibration/test predictions or duplicate job were launched. Fresh-validation inputs remain a separately gated metadata proposal.

## Research acceleration checkpoint — October 20

Three isolated workstreams produced training-only nested-CV CONCH linear probes, versioned shared S1/S2 interventions/registry and seven detector-v3 context hypotheses. Selected grade training OOF BA is 85.42% with 13/16 reused-calibration slides correct; selected cancer reused-calibration BA falls to 71.88%, and paired uncertainty includes no improvement for both tasks. Detector v3's fixed robust-NN5 primary finds 1/120 fragments with 7/72 clean alerts, five native-cancer component flags and 3/61 hypothetical clean-prediction damage. No useful review policy is established. [Eight-part measured research checkpoint](panda_research_checkpoint_v1.md).

CPU-only runs preserve the original zero-shot models and all previous scientific outcomes. Strict adapter acceptance matches 480 historical score vectors and 80 saved linear predictions exactly, without rerunning CV. The shared-engine geometry failure is retained; corrected job **23069070** completes 1,017 exact recoveries, 252 legacy comparisons and 345 coordinate-invariance checks, with 327 explicit exclusions. Its S2 v2 engineering smoke uses two training hosts and same-grade controls, not independent validation. Fresh Radboud/Karolinska cohorts are metadata-only proposals, with no acquisitions. The existing test set and submission package remain unchanged; no new GPU inference occurred. Full regression passes **258 tests** with warnings treated as errors. Detailed job/provenance/test/status records are linked from the checkpoint.

## Submission and S2/ranked-v2 checkpoint — October 20

The [finished submission package](../submission/ashby_20261021_v2/) contains a 19-slide PPTX/PDF, abstract, 480-second presentation script, four-minute Q&A and checklist. The exact organizer upload URL, deadline hour/timezone, team details and availability remain unresolved as requested; nothing was uploaded. [Integrated handoff](submission_execution_checkpoint_20261020.md).

S2 CPU **23067396 completed 0:0 in 19 seconds**: 760 records (632 positive, 128 repeated zero references), 32 host / 37 donor slides, **760/760 exact oracles**. Mean pooling was selected before outcomes from clean 35/48 training and 12/16 calibration accuracy. It produces **0/8 new calibration low-to-high errors at every primary dose**, versus tiny secondary correct-host denominators of two/three and same-grade-control instability. Eight GP5-positive calibration 10% trials are excluded for capacity. Genuine GP4/5 native exclusion changes six training / two calibration predictions. These are valid nonclinical engineering observations, not clinical Grade Group upgrades or a foreignness detector. [S2 evidence](panda_s2_results_v1.md).

Ranked detector v2 CPU **23067454 completed 0:0 in 23 seconds**, reusing saved measurements. Its primary improves training fragment hits 5/120→22/120 but fails utility targets; calibration remains **0/40 hits, 1/24 clean alerts**. Unbudgeted visual/relevance top-one review hits 21/40 while alerting on all 24 clean slides and flagging 14 native-cancer components. This does not establish useful improvement over v1. Known calibration is iterative development. [Full v2 report](panda_review_v2_results.md).

Full regression **204 passed** with warnings treated as errors. No new GPU/model/download, repeat S1/WSI/encoding/preflight, main merge or final test occurred. All rejected v1 evidence and 120-slide artifacts remain preserved. The PathGen-CLIP branch was reviewed read-only for [future research gates](../docs/panda_research_tracks_after_submission.md). All 24 test slides remain sealed; final detector evaluation remains blocked.

Latest status: **2026-10-20, America/Chicago**. PANDA development review-policy v1 is frozen and rejected. The combined rule meets the user-confirmed ≤10% clean-slide alert / ≤0.5 components-per-slide budgets but detects 0/40 calibration fragments and recovers 0/8 induced-error instances. Decision-only recovers 8/8 instances across two hosts but alerts on 4/24 clean slides and hypothetically damages 3/20 originally correct clean predictions. No useful rule among the 81 preregistered candidates; no threshold relaxation or final-test launch. [Scientific audit and measured policy results](panda_review_results_v1.md).

The preserved 120 slides and 50,729 CONCH embeddings support all current analysis. New RGB topology separates four of six formerly single-component calibration cases; boundaries remain approximate and sensitivity-limited. The new CPU measurement completed its records before a JSON serialization failure; checksum-pinned reporting resumed successfully without reprocessing. Read-only CPU preflight 23066843 completed 0:0 and verified 10,988 files / 24 held-out slides without label decoding or predictions. Frozen runtime source cde0e4a, blocked final command, uncertainty plan and output contract are [documented](../docs/panda_final_test_v1.md). All 24 test slides remain unscored. **192 software tests pass**; software fixtures do not count as real test evidence. [Reproducible figures and presentation outline](panda_presentation_v1.md).

The sections below preserve the dated experiment history, including earlier TCGA smoke counts; they do not supersede the current PANDA status above. Initial implementation was 2026-10-17.

## Current state

Real CONCH v1 image embeddings exist for **512 distinct tiles from four patients**, 128 per patient, each with 512 projected, unit-normalized features. Matching fixed prostate/bladder text prototypes are saved. Two patients are development-only; two separate patients supplied the completed evaluation smoke. GPU encoding, physical tiling and exact oracle recovery are verified; a larger cohort and clinical floater detection remain unvalidated.

Development cutoff diagnostic job `22995268` completed successfully in 12 seconds, reusing only the existing development vectors. Five quantiles, three variants, two reciprocal development hosts, six contamination levels and five seeds yield 60 oracle passes and 900 rows. The lower-cutoff sensitivity/removal tradeoff is documented in [the result report](conch_threshold_results.md); no new cutoff was selected. All 127 retrieved file hashes and all saved metrics were verified. Local software checks: **85 passed**. No new GPU inference or raw-data download was needed for this step.

Dependency maintenance is now verified: local Pillow 12.3.0 and optional pytest 9.0.3 are outside all recorded vulnerable ranges. Bounded upstream regression probes reject the old failures while normal controls still pass. A new private Delta runtime passed CPU preparation `22995419` (49 seconds) and A100 compatibility `22995434` (85 seconds), both `0:0`. All 256 regenerated development tiles and image/text vectors exactly matched the old copies. New provenance includes Pillow version; historical artifacts/environment were preserved. Current software suite: **91 passed**. GitHub alert closure after publishing remains unverified, and specific exploitation of every advisory was not demonstrated. Full evidence is retained by the Codex Security managed artifact collection outside this checkout; [NCSA facts](../docs/ncsa_setup.md).

Prepared [an expanded feasibility-pilot plan](../docs/expanded_pilot_plan.md): 16 new metadata-verified public slides totaling 21.24 GB, eight development and eight fresh evaluation patients. The user explicitly approved the acquisition on 2026-10-18; all 16 files are now size/MD5 verified. Header/coordinate preflight, broader sampling/cohort-runner implementation and protocol freezing remain before expanded pilot submission. The sections below retain the earlier execution history.

## Development cohort and cutoff-selection gate

Committed the preceding results/protocol as `f0f19a4` and implemented the frozen development-only runner as `a6d826d`. GPU job `23028013` completed `0:0` in 10 minutes 5 seconds on `gpua038`, producing **3,840 normalized 512-dimensional image embeddings** across all ten development patients, with unchanged prompts/checkpoint and exact preflight geometry. All 61 retrieved hashes match. These are the new broader-sampling artifacts; earlier 128-tile smoke artifacts remain separate.

CPU job `23028265` completed `0:0` in 15 seconds on `cn137`. Ten clean leave-one-patient-out folds yielded 150 patient/quantile/variant controls. All 32 retrieved hashes, patient exclusions from fitting, raw-score removal counts and cutoff decisions were independently verified. **No candidate met the frozen 1% original-host removal budget**. At `q=0.995`, the worst combined-score control removed 19/384 tiles (4.95%) versus the allowed three; `selected_quantile` remains null. No final calibration or held-out experiment was created, and the budget/settings were not relaxed. The final queue was empty.

[Full observed results and per-patient counts](conch_development_results.md). Native embeddings/fold scores remain ignored under `results/development/`; their checksums and remote paths are recorded. The local suite passes **105 tests**. The next work is development-only diagnosis of score/fold-normalization shifts before proposing a protocol amendment; eight evaluation patients remain untouched.

## Expanded-pilot preflight and design freeze

CPU job `23005299` completed `0:0` on `cn137` in 2 minutes 34 seconds. All 18 raw slide checksums, measured headers, coordinate sources and four × 96-tile selections passed. The first four × 128-tile candidate failed capacity on one development slide; that failure is preserved, and the uniform size was amended using geometry only before new embeddings or held-out outcomes. No patients or spacing requirements were changed.

The two predeclared development patients exported 768 QC tiles. All 45 retrieved hashes match Delta; independent checks confirmed all 6,912 selected physical cells are unique within patient, in bounds, in the saved candidate set and connected within each window, with at least 1,024 microns across windows. Contact sheets were checked for technical extraction only; no pathology labels or image-based exclusions were made. The queue was empty. [Full evidence and limitations](conch_pilot_preflight_results.md).

The [study design is frozen](../docs/expanded_pilot_protocol.md), including the development-only cutoff-selection rule and 1% original-host removal budget. **97 software tests passed** with warnings as errors. The cohort runner and final learned calibration remain unimplemented/unfitted. No new embeddings, GPU job or held-out performance evaluation was run in this stage.

## Approved acquisition execution

After the user manually reconnected, the single shared-connection test confirmed `mhoda` on `dt-login02`. Job `22995933` completed `0:0` on `cn096` in **4 minutes 42 seconds**, ending October 18 at 6:08:44 pm Central. All **16 slides, 21,243,276,685 bytes**, passed exact size/streaming MD5 verification, with zero failures. The report matches the approved manifest exactly; retrieved report/log hashes and staged source hashes match. Final file ownership/mode `600` and owner-only input directories were confirmed with metadata-only checks. The queue was empty. [Per-file evidence](pilot_downloads_22995933.json), [accounting and verification](ncsa_pilot_download_verification_20261019.json).

The untouched reservation-blocked request was cancelled before this replacement. The earlier [4/16 observation and SSH interruption](ncsa_pilot_download_status_20261018.json) remain preserved. No new weights, expanded pilot, GPU job or inference on these new patients was run during acquisition. Headers and coordinates were then unverified and subsequently passed the preflight recorded above. The acquisition update changed status/documentation only; its earlier 91 passing software tests were not rerun at that point.

## Environment and sources

- Local Mac confirmed: macOS 26.6.2. System Python 3.9.6; isolated project environment uses Python 3.11.15.
- Preserved the existing MIT license, SSH setup notes, AGENTS.md, smoke-job draft, and supplied PDF.
- Read the 30-page welcome PDF and the current master instruction. The separate October 16 updated proposal was not found in this checkout or the supplied attachment (the attachment is the master instruction).
- No local slides/embeddings or cached CONCH model directory were found. PyTorch, CONCH, and TRIDENT were absent from the inspected system environment.
- One requested SSH test used `BatchMode=yes`, `ConnectTimeout=8` and a 15-second total process timeout. It timed out; no retry or SSH configuration edit was made. Prior NCSA observations remain historical facts in `docs/ncsa_setup.md`.
- Created `.venv` with NumPy 2.0.2, PyYAML 6.0.2, Pillow 11.3.0, pytest 8.3.5. No system-wide package changes or model downloads.

## Milestones

| Milestone | Status | Evidence |
| --- | --- | --- |
| Validated image/text NPZ artifacts | COMPLETE | Normalization, dimensions, IDs, provenance, source-kind and projection checks; pickle-free loading. |
| Pooling and zero-shot scoring | COMPLETE | Hand-computed tests, per-class top 1%/5%, ceil K, deterministic ties. |
| Connected contamination and oracle recovery | COMPLETE | Repeatability, integer rounding, patient separation, spatial validity and exact host restoration tests. |
| Data inventory and stress runner | COMPLETE | Bounded discovery, provenance/missing-data report, patient-split checks, raw scores, exclusions, source/input hashes and eligibility metrics; CLI exercised. |
| Real CONCH inference / PRAD-BLCA pilot | SMOKE COMPLETE; PILOT PENDING | Scheduled original v1 image/text encoding, verified scale and four separate development/evaluation patients. Larger independent cohort not yet run. |
| Detector and calibration software | COMPLETE | Organ-only, distant-neighbor visual, combined, oracle, no-filter and matched random-removal comparisons; separate-patient real-data smoke and development cutoff diagnostic. |
| Real detector evaluation and scientific charts | SMOKE COMPLETE | Four real patients, separate development/evaluation, 60 oracle trials and verified descriptive figures. Conservative threshold detects few donor tiles; no population or clinical validation. |
| Raw WSI tiling integration | COMPLETE FOR CAPPED SMOKE | Scheduled raw-pixel extraction using verified spatial masks, measured MPP, common physical resampling and exact provenance. Full-slide segmentation/sampling is separate work. |
| Additional models and secondary cohorts | NOT STARTED | CONCH-first scope. |

## Implemented files

- `src/floater_finder/artifacts.py`: validated image/text artifacts, stable IDs, masks, metadata and pickle-free NPZ I/O.
- `scoring.py`, `injection.py`, `experiments.py`: fixed prompt ensembling, mean/top-K, deterministic connected fragments, exact oracle recovery, reproducible runs and explicit eligible/raw metrics.
- `inventory.py`: bounded candidate discovery, TCGA participant/source-site parsing, missingness, report provenance, verified institution mapping and cohort pairing.
- `conch.py`: lazy optional official-model adapter, installed API checks, encoder-weight coverage, shared-space projection, local-checkpoint-only scheduled CUDA encoding and actual timing hooks. Exercised successfully with the pinned original CONCH checkpoint on A100.
- `detection.py`: physical-distance-aware double-blocked reference scoring, clean-development calibration, leakage checks and held-out control evaluation.
- `cli.py`, `fixtures.py`, `reporting.py`: 13 discoverable commands, isolated fixture generation and a real-observation-gated Matplotlib chart command.
- `configs/`: fixed four-phrase organ ensembles, incomplete real smoke/pilot templates, empty manifest headers and explicit null metadata template.
- `tests/`: 91 tests; `scripts/run_fixture_checks.sh`: repeatable installed-CLI integration check; `scripts/inspect_environment.py`: local inventory wrapper.
- `scripts/slurm/conch_encode.sbatch`: new unsubmitted five-minute CONCH draft; earlier driver-only smoke draft preserved.
- `pyproject.toml`, `.python-version`, `uv.lock`, `.gitignore`: isolated locked environment, Python 3.11/3.12 scope, artifact/build/credential-file exclusions.
- README, methodology and NCSA setup notes updated; existing AGENTS guidance preserved and extended with scientific safeguards. MIT license and supplied PDF preserved. No commit or push made.

## Commands and checks executed

```sh
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python numpy==2.0.2 PyYAML==6.0.2 Pillow==11.3.0 pytest==8.3.5
.venv/bin/python -m pytest -q
uv pip install --python .venv/bin/python --no-deps -e .
uv pip install --python .venv/bin/python --reinstall --no-deps --config-settings editable_mode=compat -e .
uv pip install --python .venv/bin/python --reinstall --no-deps .
uv lock --python .venv/bin/python
uv sync --locked --no-editable --reinstall-package floater-finder --extra test
.venv/bin/python -m pytest -q -W error
bash -n scripts/ncsa_smoke.sbatch scripts/slurm/conch_encode.sbatch scripts/run_fixture_checks.sh
.venv/bin/floater-finder inspect --output reports/environment.json
.venv/bin/floater-finder inventory --root . --manifest configs/cohort_manifest.example.csv --output results/inventory/local
bash scripts/run_fixture_checks.sh results/fixtures/final_validation
```

The fixture script contains the exact validated `fixture`, `validate`, `score`, `stress`, `inject`, `oracle`, `calibrate`, `detect` and `summarize` commands. Earlier manual CLI runs under `results/fixtures/` and `results/fixtures/validated/` were retained; `final_validation/` uses the final installed source. Reproduction must choose a new output directory, such as `results/fixtures/reproduce`.

Test history: 29 core checks first passed. One interface-error test then failed (AttributeError versus the intended validation error); fixed, followed by 37 passing checks. The first 46-test run exposed numerical warnings in finite-array matrix operations. Explicit blocked/einsum operations removed those warnings, and all subsequent suites passed with warnings treated as errors. An editable installation imported inconsistently across shell commands; a normal installation plus explicit package reinstall and isolated-interpreter source-freshness tests resolved the executable workflow.

**Final result: 54 passed, zero failed, zero warnings** (`pytest -q -W error`, observed final run 0.58 seconds). Both Slurm drafts and the fixture script pass Bash syntax checking. Syntax checking is not a Slurm scheduling test. An attempted patch context mismatch was corrected before any final source validation.

## Actual outputs

| Output | Observed result |
| --- | --- |
| `reports/environment.json` | Local Python/package snapshot; project has no PyTorch, CONCH or TRIDENT installation. |
| `results/inventory/local/cohort_inventory.csv` | Header-only: zero local candidate slides found. |
| `results/inventory/local/missing_data.json` | Zero candidates, bounded scan and missing-data accounting; not evidence that target TCGA data exists. |
| `results/fixtures/final_validation/inputs/` | Artificial 100-tile host/donor/development/clean-control NPZs, fixture text and reproducible YAML. No real images/model. |
| `results/fixtures/final_validation/stress/results.csv` | 36 **fixture** rows: one host/donor pair, six requested percentages, two seeds, three pooling rules. All successful rows have oracle verification. |
| `results/fixtures/final_validation/stress/` | `summary.json`, `failures.json` (empty) and `experiment.json` with config/prompts/model/input/source hashes. |
| `results/fixtures/final_validation/mixed.npz`, `restored.npz` | Five synthetically injected rows and verified exact host recovery. |
| `results/fixtures/final_validation/calibration.json` | Clean development-fixture calibration with stored parameters, provenance and patient exclusions. |
| `results/fixtures/final_validation/detection/` | Fixture-only tile scores/flags, detection/control metrics and recovery comparisons. |
| `results/fixtures/final_validation/clean_control/` | Separate held-out fixture clean-control evaluation. |
| `results/fixtures/final_validation/recomputed_summary.json` | Recomputed eligibility and raw-change summary. |

These are software checks only. There are **no real-data smoke, pilot or benchmark results**, no measured CONCH inference throughput, no real-tile montage, and no scientific contamination-versus-flip plot. Do not quote fixture AUROC or flip rates as research findings.

## Remaining inputs and approvals

1. Manual NCSA access has now been restored and the approved infrastructure smoke job completed; see the latest session below. CUDA computation, installed CONCH dependencies and target data availability still need verification.
2. Identify patient-attributed PRAD/BLCA diagnostic slides or existing tile manifests, including project/label/report provenance, split and spatial metadata. The separate updated proposal remains unavailable; the master specification was sufficient for this implementation.
3. Identify an already-local authorized CONCH checkpoint and verify the installed module/model interface. The upstream source was inspected at CONCH commit `141cc09c7d4ff33d8eda562bd75169b457f71a62` and TRIDENT commit `bdeeb74b7eaad8d48bda232bde7de66cae980918`; those are not claims about a remote installation.
4. Explicitly approve any Slurm execution before submission. Driver smoke: `bfqi-delta-gpu`, QoS `bfqi-delta-gpu-mhoda`, `gpuA100x4`, 1 GPU, 1 CPU, 2 GB, 2 minutes. Separate CONCH draft: same account/QoS/partition, 1 GPU, 4 CPUs, 16 GB, 5 minutes, at most 128 existing tiles. No reservation name invented.

At the end of local implementation, no credentials were requested, no SSH config was changed, and no job, model/dataset download, remote copy, remote package installation or actual inference had been performed. The later approved GPU test is recorded separately below.

## Latest session: approved GPU infrastructure smoke

Status: **COMPLETE**. The user authorized GPU testing and manually restored shared SSH. A single connection check succeeded as `mhoda` on `dt-login01`. Preflight showed an empty queue and the expected GPU allocation. Submitted `scripts/ncsa_smoke.sbatch` once via `ssh -o BatchMode=yes -o ConnectTimeout=8 ncsa-floater 'sbatch --parsable'`, passing the script on stdin.

Job `22957101`: account `bfqi-delta-gpu`, QoS `bfqi-delta-gpu-mhoda`, partition `gpuA100x4`, 1 GPU, 1 CPU, 2 GB memory, two-minute limit. It initially waited for reservation routing, then ran automatically under reservation `sup-30434-17`. Slurm reports **COMPLETED**, exit `0:0`, elapsed **five seconds**, node `gpua038`. Both `srun` steps completed successfully. Output reported **NVIDIA A100-SXM4-40GB**, driver **595.71.05**.

Exact monitoring queries included:

```sh
ssh -o BatchMode=yes -o ConnectTimeout=8 ncsa-floater 'whoami && hostname'
ssh -o BatchMode=yes ncsa-floater 'squeue -j 22957101 -h -o "%i|%j|%P|%T|%R"'
ssh -o BatchMode=yes ncsa-floater 'sacct -j 22957101 -n -P --format=JobID,State,ExitCode,Elapsed,ElapsedRaw,Start,End,NodeList,AllocTRES'
```

Monitoring was performed through bounded remote Python subprocesses using those Slurm arguments. No job was resubmitted. Evidence is in `reports/gpu_smoke_22957101.json` and `reports/gpu_smoke_22957101.log`; remote stdout is `/work/nvme/bfqi/mhoda/floater-smoke-22957101.out`.

This verifies scheduled GPU allocation, NVIDIA driver visibility and a small log write. It is an infrastructure test, not a real-data research result. CUDA tensor computation, PyTorch/CONCH execution and model throughput remain untested. No model/data download or inference was launched. The CONCH draft remains unsubmitted pending verified inputs.

## Next stage: real CONCH service preflight

The user requested the next stage, confirmed individual Hugging Face CONCH access, and supplied the organizer's host/port. Shared SSH again verified `mhoda` on `dt-login01`. The documented `pytorch-conda/2.8` module loaded successfully; package metadata reports Python 3.11.13, torch 2.8.0+cu128, NumPy 2.2.6, Pillow 11.3.0, PyYAML 6.0.2. CONCH/OpenCLIP/TRIDENT distributions were absent. No login-node torch import, computation, package installation or new Slurm submission occurred.

Verified existing shared data without a WSI download: PathGen metadata has 2,141 records from ten slides, matched by public GDC file IDs to project and patient metadata. The bounded image-directory listing found 2,141 PNG files. One TCGA-PRAD patient has 208 tiles; no TCGA-BLCA case occurs in this small sample. Source position fields are numeric strings; physical units/scale were not inferred. Captions and clinical reports were not copied. Recorded the verified inventory in `reports/ncsa_pathgen_inventory_20261017.csv` and the preflight in `reports/ncsa_preflight_20261017.json`; raw non-secret metadata snapshots remain under ignored `results/inventory/ncsa_20261017T221233Z/`.

The supplied HTTPS URL failed its handshake. The documented HTTP protocol at the same host/port returned health `ok`, model `conch`, device `cuda`. One two-tile `/embed` request without credentials returned 401 and was not retried. No actual embedding result was obtained. The failed attempt's non-secret report is `/work/nvme/bfqi/mhoda/floater-conch-service-smoke-20261017T221526Z/smoke.json`.

Added `scripts/conch_service_smoke.py`, `configs/ncsa_prad_service_smoke.csv`, and ten tests. The standalone standard-library client uses exactly two capped, existing prostate images; checks model/device, response count/dimensions/finiteness/normalization; refuses redirects and existing output; and reports authentication failure once without logging response bodies or exception messages. It prompts for the organizer's service API key only in the user's interactive Terminal and never saves it or accepts it on the command line. The key has not been provided to the agent.

Staged that script and manifest under `/u/mhoda/floater-finder/` with owner-only file permissions, verified matching source hashes, and executed the deployed `--help` successfully. This is not a full remote checkout. `.venv/bin/python -m pytest -q -W error`: **64 passed**. The user's exact next command is in `docs/ncsa_setup.md`, using a hidden API-key prompt and a new output directory. Successful authenticated CONCH inference remains pending that manual authentication step.

The published hosted API does not provide text embeddings, all per-class scores or checkpoint/preprocessing provenance. A successful connectivity smoke must not be promoted into a full scientific artifact. Full PRAD/BLCA experiments also still require a bladder donor, independent development/evaluation patients, verified physical scale and remaining diagnostic/report provenance. No scientific results, model/WSI downloads, or throughput claims were produced.

## Follow-up: pasted-command startup failure

The user's pasted command included a Markdown link in `--endpoint`. A read-only check also found the fixed output directory already present, with a user-run `smoke.json` reporting HTTP 401. The old generic startup message obscured these distinct failures. Added specific pre-key endpoint/output/tile checks and `scripts/run_ncsa_service_smoke.sh`, which supplies the verified plain URL and a timestamped output directory. The user can run one short command from their existing Delta shell, with no URL or line continuations to copy.

`tests/test_service_smoke.py`: **13 passed**, including new regression checks for Markdown URLs, existing-output errors before key entry, and launcher argument construction without contacting the service. Bash syntax passed. Verified the previous deployed source hash, preserved a backup, and staged the corrected client and launcher. No API key was read, no authentication retry or inference request was made, no job was submitted, and existing result directories were preserved. Successful authenticated CONCH inference remains pending the organizer's service key in the user's Terminal.

## Hosted CONCH image-encoding smoke: passed

The user explicitly supplied and authorized use of the organizer's service credential. After one successful shared-connection identity check, ran the existing launcher in an interactive SSH Terminal and supplied the credential only at its hidden prompt. The process exited zero and returned `status=passed`, report `/work/nvme/bfqi/mhoda/conch-service-smoke-20261017T223436Z/smoke.json`, `research_result=false`. No credential value was written to repository files, scripts, command arguments or reports. No new Slurm job, model download or dataset download was performed.

The known deployed client requires two finite, unit-normalized 512-dimensional vectors before returning `passed`. This verifies the authenticated hosted image-encoding request, using two existing TCGA-PRAD images. It does not verify checkpoint hashes, text embeddings, full per-class scores or scientific contamination/detection behavior. Recorded execution evidence and its limits in `reports/conch_service_smoke_20261017T223436Z.json` and updated the preflight status.

The shared SSH session closed after the interactive run. The next attempt to retrieve the exact report/vector files failed with `Permission denied (gssapi-with-mic,password)`; authentication was not retried. Raw artifacts, exact norms and latency are still remote, and the intended live OpenAPI inspection did not execute. Manual `ssh ncsa-floater` plus password/Duo is the next step before retrieving the existing outputs. No code changed after the prior 13 targeted tests, so tests were not repeated for these evidence/documentation updates.

## October 18: retrieved results and fresh authenticated smoke

The user confirmed manual reconnection and explicitly requested another CONCH run. The shared connection verified `mhoda` on `dt-login04.delta.ncsa.illinois.edu`; the deployed client SHA-256 matched the local tested source. Retrieved the previous run's report and vectors first, independently validating two finite 512-dimensional rows and unit norms. Updated `reports/conch_service_smoke_20261017T223436Z.json` to mark retrieval complete; its artifacts are under ignored `results/smoke/conch_service_20261017T223436Z/`.

Ran exactly one fresh two-image request through the hosted CONCH service, entering the authorized credential only at the hidden interactive prompt. The client returned `passed`. Kept the test Terminal open while copying the artifacts, then closed it normally. Fresh remote output is `/work/nvme/bfqi/mhoda/conch-service-smoke-20261018T205624Z/`; local vectors/report are under ignored `results/smoke/conch_service_20261018T205624Z/`, with non-secret evidence in `reports/conch_service_smoke_20261018T205624Z.json`.

Independent validation: two rows, 512 dimensions, finite values, norms `0.9999999680936702` and `1.0000000028404457`; vectors match the previous run exactly on identical inputs. Remote embedding-file SHA-256 verified as `99302e4b4d1fe8169444ad1161ca40e2723c41b4f8bdbf343b79fc051e6bae63`. Fresh HTTP round-trip latency was `0.14031214600254316` seconds for both images, not a GPU throughput benchmark. No new Slurm job or dataset/model download occurred.

The live public OpenAPI schema confirms `/health`, `/embed`, `/classify` only. There is no published text-vector or checkpoint-provenance endpoint; full research artifact compatibility remains unresolved. The bladder donor, additional independent patients and verified physical scale remain missing. This completes the requested real CONCH smoke stage without producing scientific contamination/detector results. No code changed in this run; validation consisted of actual result/schema inspection rather than repeating unchanged software tests.

## Next experiment: cohort discovery and compatible-input plan

On the user's request to advance, a single shared-connection check verified `mhoda` on `dt-login04`. Bounded relevant-root inspection found the previously uninspected `/work/nvme/bfqi/shared/datasets/tcga_conch_v1.5`. Completed filename inventories count 401 PRAD HDF5 files (401 patient barcode prefixes) and 457 BLCA files (386 prefixes). Inspected metadata only for two files per cohort: float32 features `[N,768]`, int64 coordinates `[N,2]`, encoder `conch_v15`, target magnification 20X, patch size 512, level-0 footprint 1,024, overlap zero. No feature arrays were read or processed. Saved metadata evidence in `reports/ncsa_conch_v15_inventory_20261018.json`.

Public GDC metadata independently confirmed the four sampled filenames, patient IDs, projects, organs, open access and `Diagnostic Slide` status; saved in `reports/ncsa_conch_v15_gdc_samples_20261018.json`. This establishes real shared bladder data, but its v1.5/768-dimensional feature space is incompatible with the current v1/512-dimensional dual encoder. No artificial padding, fabricated model provenance, scoring or experimental results were introduced.

Prepared `docs/next_experiment.md`, including a local, unsent organizer request for matching v1 inputs/text/provenance. An alternative `configs/ncsa_conch_v1_download_plan.json` specifies two independent diagnostic WSIs plus the original pinned CONCH v1 checkpoint: 4,801,440,256 bytes total. GDC MD5 checksums and Hugging Face checkpoint size/SHA-256 are verified metadata; no file bodies downloaded. Proposed storage paths are clearly marked as new and uncreated. The verified personal NVMe parent is writable with sufficient filesystem-wide available space; user quota remains unverified. Download approval, observed WSI calibration/tiling work and separate concrete Slurm approval are still required before that route can execute.

No job, large download, array processing, new inference, or scientific experiment was performed during this stage. Existing CONCH v1 artifact/prompt/patient safeguards remain unchanged. Validation was source metadata cross-checking and JSON/plan consistency checks, not repeated software tests.

## Approved input downloads: completed October 18

The user explicitly approved 4,801,440,256 bytes of downloads, with no new Slurm submission. Reconfirmed execution on the local Mac and remote identity `mhoda` on `dt-login04`. Created `scripts/download_approved_inputs.py` to stream only the approved public GDC endpoints, reject oversized or checksum-mismatched responses, preserve existing files and publish validated downloads without overwriting. Four targeted tests passed, including checksum failure and preservation of existing work.

Downloaded both diagnostic WSIs into the verified personal NVMe input root. Host `TCGA-2A-A8VL`: 1,713,266,379 bytes, MD5 `3b0d857552028cb3b6ace58d8f528706`. Donor `TCGA-2F-A9KP`: 2,285,938,440 bytes, MD5 `818189a55031640f8d4effb7dbef622e`. Streaming checksum verification passed for each; evidence is `reports/gdc_downloads_20261018.json`.

The existing Safari session visibly confirmed granted CONCH access. Downloaded the pinned original checkpoint through that session, without extracting browser cookies or credential files. Verified its size and SHA-256 locally, then streamed it to Delta and checked the same size/hash before publishing the final filename: `/work/nvme/bfqi/mhoda/floater-finder/inputs/models/conch_v1/pytorch_model.bin`, 802,235,437 bytes, SHA-256 `40a9644b9ba0e83a74576e0a5e5f7313599fa9c9cdaf3c20f8a3e271b0e9ae7c`. Evidence is `reports/conch_v1_checkpoint_download_20261018.json`. Updated the input plan with actual verified destinations and the explicit download-only approval.

All three inputs are now ready in storage. No WSI processing, model load, new inference, Slurm submission or scientific experiment was performed. Physical calibration, tiling and runtime preparation remain before a concrete job can be proposed for approval. No commits or pushes were performed in this download stage.

Final storage checks found that Delta default ACLs override file-creation umask. Restricted the three new input files and their download report to mode `600`, and removed group/other access from the five new input directories while retaining inherited setgid. Updated the downloader to enforce file mode with `fchmod`, verified the behavior in its four passing tests, and backed up the deployed previous script before updating it. Final sizes, ownership, modes, plan snapshot and script hashes are recorded in `reports/ncsa_inputs_verified_20261018.json`.

## Continuous-job authorization, physical tiling and runtime preparation

The user authorized ongoing Delta jobs on October 18 without repeated approval requests; updated `AGENTS.md` to record the scope. Kept existing files and staged new timestamped remote source snapshots with per-file hashes.

Implemented `tiling.py`, `scripts/ncsa_runtime_preflight.py`, `scripts/ncsa_one_pair_smoke.py` and two Slurm scripts. The tiler validates WSI/coordinate identity, requires observed MPP, uses existing coordinates without reading v1.5 feature values, normalizes the physical field through fractional BICUBIC resampling, selects a deterministic connected subset and saves exact spatial provenance plus contact sheets. Added measured-calibration rejection, connectedness/determinism, physical resampling, Slurm-only execution and actual raster-export tests. Full local suite: **76 passed** with warnings treated as errors. Both Slurm scripts pass Bash syntax checks.

CPU job `22994404` completed `0:0` on `cn004`. It installed a private pinned CONCH/OpenSlide environment, rehashed all input bytes, checked actual WSI dimensions and observed MPP, and validated tokenizer output offline without loading a model. The two scanners differ (0.2527 versus 0.2277 microns/pixel), so forcing equal source MPP would be invalid. The common output uses 256-micron fields, 512 pixels and physical-grid coordinates; source MPP remains in provenance. Evidence: `reports/ncsa_runtime_preflight_22994404.json` and its source/resource submission record.

Submitted one GPU smoke job `22994469`, bounded to 128 tiles per slide, fixed prompts, six contamination levels, one seed and mandatory oracle recovery. No further raw input or model download occurred. The GPU outcome is recorded after completion below; submission alone is not a successful model result.

## Real GPU smoke and provenance regression: verified

Initial GPU smoke `22994469` completed `0:0` in 68 seconds on `gpua029`, producing real projected image/text vectors, 18 stress rows and six exact oracle passes. Retrieved and independently validated 22 artifacts. Found and fixed a genuine provenance bug: transform `repr` saved a process-specific function address, making otherwise identical future jobs appear incompatible. Added a regression test, stripped only transient addresses and recorded installed transform/tokenizer source hashes. Preserved the initial legacy artifacts without editing their scientific metadata.

Repeat GPU smoke `22994635` completed `0:0` in 61 seconds on the same A100 node. Both image arrays are `[128,512]`; all values satisfy the normalized real-artifact contract, and repeated text vectors have the same fingerprint within the run. Image/text values exactly reproduce the initial job. Independently recomputed six injections/oracles and all 18 pooled class-score rows. Actual foreign counts for requested 0/0.5/1/2/5/10 percent are 0/1/2/3/7/13; realized counts and raw scores are retained. Both original subsets receive their expected organ labels; the prostate-host direction has no observed prediction changes in this seed. These are one-pair subset observations, not a cohort robustness claim. Canonical evidence: `reports/conch_one_pair_smoke_22994635.json`.

Full suite now **80 passed** with warnings as errors. Added login-node guards for all scheduled scripts and corrected chart labeling to distinguish requested from realized contamination and display host/seed counts. Submitted CPU follow-up `22994703` to reuse these embeddings in both directions across five fixed seeds; no additional GPU inference or input download is involved. Outcome follows after verification.

## Independent calibration and detector smoke: completed

Under the user's instruction to continue the plan without repeated permission requests, staged two additional public, GDC-verified diagnostic WSIs (5,188,681,471 bytes) for development-only calibration. MD5 checks passed for both. The current evaluation pair remains excluded from calibration; no bulk cohort or new checkpoint was downloaded. Total verified inputs are 9,990,121,727 bytes.

GPU job `22994850` completed `0:0` in 71 seconds, producing two additional `[128,512]` clean-development artifacts with canonical v1 provenance, observed MPP and the same physical resampling protocol. Retrieved and hash-verified 15 artifacts and checked patient/model/text separation. CPU detector job `22994885` completed `0:0` in 14 seconds: 60 oracle trials, 180 variant rows, zero exclusions, complete organ/visual/combined, no-filter, oracle and matched random-removal controls. The 1 mm exclusion, 0.1 mm smoothing, equal weighting and 99th-percentile threshold were frozen before detector evaluation.

The result is an honest limitation: at 10% requested contamination, combined mean AUROC is 0.949 but mean injected-tile detection is only 3.85%, with no original-host removal in that stratum. These means describe two evaluation hosts across five seeds; they are not a population estimate. Development thresholds use two other patients. Native contamination has not been reviewed; clean means no synthetic injection. The evaluation cases have not been used to retune the threshold.

Retrieved 184 detector files and independently reproduced all 60 oracle trials, every variant flag and count metric. Standardized scores agree within 1.47e-6 across recorded NumPy versions. Saved validated reports, exact raw metric tables and two descriptive figures under `reports/`; raw tiles, arrays, WSIs and weights remain outside tracked artifacts. All six new jobs completed `0:0`, final queue empty; local **82 tests passed**. Further work needs representative development patients and fresh held-out cases, broader slide sampling, report/institution provenance and clinical review before stronger claims.


## 2026-10-20 — PANDA scale-up checkpoint

Read the expanded 60/120-slide request and preserved the original checkout/main. Kaggle catalog and selective streamed-header access passed after paced pagination; original metadata matched. Versioned balanced plans require 1,201,123,589 / 2,459,351,119 additional catalog TIFF bytes. Acquisition 23030528 remains pending with a missing collector and awaits explicit replacement approval.

Bounded CPU profile 23051244 completed 0:0 in 41 seconds / 260 MB peak task RSS: 944 representative tiles and 19 separate donor tiles. High-grade representative sampling found 26 GP4-positive tiles; exact native GP4 area is 0.020806028382116183 mm². GG1 mask recovered from an existing ZIP, with no new TIFF download. All 963 tile hashes/geometry/fractions independently passed. Added checkpointable acquisition/tiling/embedding preparation, fixed candidate prompts, stage ledger and executed CPU charts. 165 local tests pass. No PANDA GPU inference, cancer baseline or contamination evaluation ran. [Full checkpoint and approval commands](panda_scale_checkpoint_20261020.md).

User explicitly approved the 120-slide selective plan and replacement, plus the separate five-minute 944-tile GPU profile. Verified original acquisition 23030528 CANCELLED; submitted replacement **23051626** and GPU profile **23051627** once each. No completion/embedding claim is made at submission. Larger GPU batches require the measured profile and another approval.

Acquisition 23051626 completed 0:0 in 3:42; all 240 files (2,490,697,994 bytes total, 234 new files) match catalog sizes with individual SHA256 receipts. Initial GPU profile 23051627 failed before inference because CONCH is a namespace package; corrected and regression-tested before bounded retry 23051673 (4:48 cap after the 12-second failure). Retry completed 0:0 in 54 seconds with 944 validated 512-dimensional image embeddings and matched four-class text prototypes. Retrieved artifacts independently pass hashes, unit normalization, IDs, coordinates, checkpoint/model identity and non-mask-enriched sampling checks. Total profile GPU elapsed including failure: 66 seconds.

First ten-slide cohort CPU job 23051691 completed 0:0 in 2:17, 397,448 KiB task RSS, with 3,528 representative tiles and full native-mask audits. Input SHA256 values agree with acquisition receipts. The proposed remaining 110-slide array was rejected with `QOSMaxSubmitJobPerUserLimit`; no array job was created. Site limits are being inspected before choosing a smaller supported submission. No larger GPU batch or baseline evaluation has run.

Verified the limiting partition QoS is `cpuintqos`, MaxSubmitJobsPU=1 and MaxJobsPU=1; the allocation QoS itself reports no such limit. A one-job/four-worker CPU plan passed scheduler test-only validation and was submitted once as **23051907** (4 CPUs total, 16 GB, 30 minutes). Its four disjoint worker schedules cover indices 10–119 exactly once, reusing the frozen native-audit/tiler source from the passing first ten. The rejected array produced no job and was not retried.

Local suite now passes **168 tests**, including namespace-package provenance, slide-level baseline denominators, sealed test slides and rejection of mask-guided views as clean inputs. The development-only baseline implementation is prepared but has not evaluated any real cohort scores.

Final CPU cohort gate: 120 slides / 40 per group / 50,729 tissue tiles; 119 usable native masks / 39 high-grade GP4/5-positive masks. The bulk CPU job retained 112 completed slides before one LZW annotation failed. Diagnostic/remaining job 23052637 completed the other seven; independent diagnostic 23052704 confirmed OpenSlide and Pillow decode errors without modifying inputs. Explicit SHA-bound annotation exclusion preserved the bad mask; RGB-only case job 23052852 completed 0:0 with 512 tiles and unknown annotation fractions. Original slide labels/splits remain intact. GG1 training case 3c685ed0f92e30f6ffeb5cea7cef5994 has no cancer annotations in its full native mask; all 100 tissue cells were sampled, so this is annotation/label disagreement rather than sampling miss.

Created verified 120-slide manifest and exact GPU input mapping. Reused the three matching 944-embedding profile artifacts after data/geometry/model/prompt checks. Remaining 117 slides / 49,785 tiles require a separately approved 45-minute single-A100 batch, expected 25–30 minutes. Scheduler test-only passed; no batch submitted. Latest complete local suite: 171 passed. [Current checkpoint](panda_120_ready_20261020.md).


## 2026-10-20 — Approved full PANDA embedding batch submitted

The user explicitly approved 117 new slides / 49,785 tiles plus reuse of 944 existing embeddings, one A100 / 4 CPUs / 16 GB / 45 minutes. Verified shared SSH identity, empty own queue and no recorded duplicate, then submitted once as **23054910**, running on gpua018. CPU follow-up **23055022** depends on GPU success and verifies all current input/output hashes and artifact contracts before scoring only 72 training + 24 calibration slides. The 24 test slides remain sealed. No batch completion or disease-performance result is claimed yet. Added CPU artifact-verification checks; full local suite **172 passed**. [Current run](panda_120_embeddings_23054910.md).

Shared SSH subsequently failed with broken control-master connection and permission denied. Stopped remote attempts immediately; requested manual Mac Terminal reconnection without credentials. Last verified progress: GPU 23054910 RUNNING on gpua018 at 9:27, 54 completed slides including reuse / 20,687 new features; CPU 23055022 PENDING (Dependency). No jobs cancelled/resubmitted. Completion and baseline metrics remain unverified pending reconnection. Baseline protocol was recorded before real prediction inspection.


## 2026-10-20 — 120-slide GPU batch and clean baseline completed

After manual reconnection verified mhoda on dt-login03. GPU 23054910 COMPLETED 0:0 in 21:46 (0.3628 GPU-hour), 117 new slides / 49,785 embeddings plus 944 reused. CPU 23055022 COMPLETED 0:0 in 3:04, verifying all 120 / 50,729 normalized 512D artifacts before scoring 96 development slides. All 24 final-test slides remain unscored. Top-5% benign/cancer calibration accuracy 83.3%, balanced accuracy 78.1%, confusion [[5,3],[1,15]]; this is descriptive development evidence, not clinical or final-test validation. All 480 raw rows and 12 metric groups independently checked locally; executed confusion plots saved. Patient independence remains unknown. [Complete results](panda_120_embeddings_23054910.md).


## 2026-10-20 — Connected S1 stress and real piece counterfactuals

CPU 23065666 completed 0:0 in 14 seconds: 192 S1 trials, 32 benign hosts, 21 donor slides, all six doses, zero capacity exclusions, 192 exact oracle passes. Donor subsets have >=10% native cancer annotation per tile and four-connected occupied geometry. Independently checked every trial against bounded donor coordinate/annotation metadata. No new GPU/downloads or final-test scoring. CPU 23065744 completed 0:0 in 11 seconds: 24 unmodified calibration cases and 40 mixtures analyzed with top-5% LOPO. Unmodified dependence is 7/18 evaluable; six single-component cases are explicitly unevaluable. Eight mixtures have a decisive pure-foreign component, matching S1 flips; genuine annotated cancer can also be decisive. No alert policy supplied, so review-alert rate is null and no foreignness/clinical claim is made. All 64 raw reports checked; representative JSON and verified spatial plots saved. [Current checkpoint](panda_s1_and_piece_results_20261020.md).

Final checkpoint: 178 tests passed with warnings as errors; relevant Slurm scripts pass Bash syntax checks; whitespace checks pass. All four jobs completed successfully and own queue is empty. Protected original metadata/pilot/partial-manifest hashes match. Current per-slide ledger updated; no commit, push, merge, final-test scoring, calibrated alert-rate claim or clinical-validity claim. Latest rounded allocation balances: 5,516 CPU hours / 8 GPU hours.


## 2026-10-21 — fresh Radboud60 approved CPU scope completed

Acquisition 23070667 and all six serialized tiling jobs completed `0:0`. Full metadata checks passed 60 slides / 25,915 tiles / 60 masks. Group tile counts are 8,733 benign, 8,583 GG1 and 8,599 high-grade; all 40 nonbenign slides contain sampled annotated cancer, and all 20 high-grade slides contain GP4/5-positive tiles (4,209 distinct tiles). These are intake/annotation observations, not predictive results. Acquisition plus tiling used 0.7572 allocated CPU-hours under the five-hour cap. Shared-SSH interruptions were resolved through private manual authentication; completed jobs were inspected, not duplicated.

All payloads and detailed reports remain on Delta. The frozen exact 60-directory encoding list and CPU-readiness receipt exist there. See [execution evidence and exact next commands](panda_fresh_cpu_execution_v1.md). No GPU/fresh prediction job was submitted. Existing models/protocols, original 120-slide artifacts, 33 legacy source hashes, main and 24 sealed final-test predictions remain preserved. Only documentation changes in this checkpoint; the unchanged prior suite passed 284 tests with warnings as errors. Next scope requires separate approval for one A100/30 minutes plus bounded CPU verification and frozen fresh-baseline scoring, without downloads, refitting or retuning.


## 2026-10-21 — approved fresh CONCH encoding and frozen baseline completed

GPU 23081929 completed 0:0 in 743 seconds using one GPU, 4 CPUs, 16 GB; CPU 23082231 completed 0:0 in 66 seconds using 2 CPUs, 8 GB, no GPU. All 60 slides / 25,915 real 512D embeddings and frozen source/model/text/sampling provenance verified before scoring. Primary benign/cancer BA 80.0% (95% slide-bootstrap 70.0–88.8%, supports 20 benign/40 cancer; recall 28/40 cancer); primary low/high BA 72.5% (60.0–85.0%, 20 low/20 high; recall 11/20 high). Frozen historical comparators are 75.0% and 65.0% BA. No refit, retuning, outcome-guided primary switch, repeated acquisition/tiling, extra jobs or original 24 final-test predictions.

All payloads, raw predictions and detailed reports remain on Delta; local notes contain bounded aggregates only. [Full results, confusion matrices, per-class Wilson intervals, uncalibrated probability diagnostics, provenance and limitations](panda_fresh_baseline_results_v1.md). Patient independence and clinical/floater-policy validity remain unverified. These 60 slides are now evaluated, not fresh/unscored for future work. Source/protocol/main/legacy guards and whitespace checks pass; production code is unchanged and the prior software suite passed 284 tests.


## 2026-10-21 — next S1 follow-up implemented, tested and staged

Architecture 104dd31 adds immutable manifest/identity-bound follow-up membership without retagging engineering artifacts or weakening default development/test guards; legacy S1/S2 checks retain exact behavior. Preparation source `3a3faf199bf2a334648227281a685a999a60f7c9` adds the fixed S1 runner/protocol, existing shared append/replacement/oracle operations, native editing controls and genuine positive-region counterfactual diagnostics. All 297 tests passed in a clean offline environment; an initial worktree-venv run had 295 passes/two isolated import failures, with six CLI checks subsequently passing there. No application code changed for the transient install issue. All 33 frozen legacy hashes, the original protocol and main remain unchanged.

Verified 233 staged source files and metadata/model preflight on Delta. Existing 60-slide / 25,915-vector receipts match; no slide-array processing or new prediction during staging, target output absent, own queue empty and CPU partition up. [Frozen design and exact command](../docs/panda_fresh_s1_v1.md), [bounded preparation receipt](panda_fresh_s1_preparation_v1.json). Source archive `510f6957213316167a3b1e8433a6215a655521de2b8760e08ca3f7388a5ecbe3`; protocol `d42332cc7950bb89d9ab779912f54e28a6b91114e2a6663ee34ccd15165c9594`. The proposed 2-CPU/8-GB/20-minute job is unsubmitted pending approval. No GPU, new acquisition, downloads, model fitting, detector thresholds, or original 24 test predictions. Raw artifacts remain on Delta.


## 2026-10-21 — approved frozen S1 follow-up completed

After the explicit “Approve CPU follow-up” response, source/input verification and an empty-queue check, CPU **23083320** was submitted once from `3a3faf1` on bfqi-delta-cpu/cpu-interactive (2 CPUs, 8 GB, 20-minute cap). It completed 0:0 in 148s /0.08222 allocated CPU-hours, with **1191 interventions, 2382/2382 exact restoration checks, nine retained capacity exclusions, 140 counterfactual bags /280 model reports**. The sealed registry has 1481 checkpoints /1484 verified events; no retry, GPU, download, fitting or alert-threshold selection. All raw artifacts stay on Delta.

At 5% requested cancer editing, primary induced original-host-label errors are 9/54 initially correct repeated instances per mode (4/18 unique hosts); historical 17/39 (8/13). Historical prediction changes differ from new-error counts: 18 append and 19 replacement changes across all 60 eligible instances. Native replacement is an exact null; native append gives two historical changes on one host. Seventeen unmodified slides are unevaluable single components. Genuine cancer-containing component exclusion changes primary cancer to benign in 14 tests across 13 slides; dependence is not foreignness or a calibrated alert. [Results, exact denominators, uncertainty, safety controls and remote receipts](panda_fresh_s1_results_v1.md).

The exact approval is consumed. Existing 120-slide/TCGA evidence, all fresh artifacts, original final-test seal, frozen source/protocol hashes and main are preserved. No final-test prediction was computed. Only documentation changed after the prior 297 passing software tests; further policy development or execution requires a separately concrete scope.


## 2026-10-21 — S3 conservative review-transfer prepared

Pushed prior S1 results through `3c8ad47`. The new S3 module reuses exactly 140 saved S1 bags, the old five training-clean robust-NN5 thresholds (strict unanimous score >9.32818765238456), unchanged cancer scorers and cached counterfactuals. Fixed comparisons are visual, dependence, combined and 32 random draws matched to combined component count per bag. No threshold search/fitting, hidden annotations, new topology, repeated contamination draws or extra encoding. Native-cancer flags, empty exclusions, hypothetical filtering damage and unique-slide versus repeated-control denominators remain explicit. The old RGB-to-current sampled-cell topology shift prevents assuming transferred burden calibration.

All 306 tests pass with warnings as errors after the final code change; nine new fixture tests check truth separation, genuine-cancer harm, known-foreign recovery, initially incorrect denominators, strict thresholds, random-control units, empty exclusions and execution gates. No dependency added; original source/protocol/main guards preserved. [Protocol, limitations and bounded CPU scope](../docs/panda_fresh_review_transfer_v1.md). Latest user request to push and move forward supplies new-stage development authorization; planned resources 2 CPUs/8 GB/20 minutes on the verified CPU account/partition are chosen within the bounded research plan and will be shown with the staged command before submission. New real S3 outcomes remain pending.


## 2026-10-21 — S3 transfer executed, frozen policy remains unsupported

CPU **23101320 completed 0:0 in 35s** on bfqi-delta-cpu/cpu-interactive (2 CPUs, 8 GB, 20-minute cap, no GPU; 0.01944 allocated CPU-hours), from pushed immutable source `a5d819c`. All 140 saved S1 bags /9800 model-policy records and 141 checkpoints /144 events pass independent JSON/hash inspection. The 32 random controls per bag match combined component counts and retain unique-slide denominators. No repeated contamination draw, new encoding, threshold fitting, classifier fitting, download or original final-test prediction.

Primary combined finds 0/20 foreign fragments in either mode, flags 4/60 unmodified slides, flags 4/90 genuine cancer-containing sampled components and hypothetically damages 4/46 initially correct predictions. Its one append label return deletes 507 native representations, deletes zero foreign tiles and retains all 26 foreign tiles; it is not decontamination evidence. The four genuine native carriers occupy 98.44–99.61% of their bags, leaving 2–8 tiles. Burden point estimates alone do not validate the rule. [Full comparisons, matched random controls, uncertainty, physical-context diagnosis and remote receipts](panda_fresh_review_transfer_results_v1.md).

All 306 software tests passed before execution. Source/protocol/main/33 legacy guards and old S1 artifacts remain unchanged; original 24 tests stay sealed. The exact bounded next-stage scope is complete. A future truth-blind topology/context feasibility audit needs a new frozen development scope; do not retune the evaluated 60 and call it independent validation.


## 2026-10-21 — original-training topology/context audit prepared

New frozen diagnostic uses only the original 72 training slides, cached RGB membership/feature checkpoints and existing CONCH vectors. Compare memberships with the unchanged 8-neighbor/no-gap sample graph; retain unmapped RGB tiles and separate occupied versus observed areas. Fixed reference-support categories follow the existing algorithm: six remaining tiles are needed for both NN5 calculations to have five neighbors. Geometry-only largest-candidate selection and nested 2/5/6/16/32-tile references under three fixed seeds yield at most 2160 records, with exclusions and duplicate subsets explicit. No classifier call, WSI/PNG read, threshold/policy selection, fresh 60/calibration/test array or download.

All 315 tests pass with warnings as errors, including nine new fixture checks for topology crosswalks, context support, cached-score reuse, physical area, nested/duplicate references, truth separation and execution guards. The protocol, original 33 legacy source files and main remain unchanged. [Fixed plan and bounded 2-CPU/8-GB/20-minute scope](../docs/panda_topology_context_v1.md). Latest “next” supplies ongoing-development direction; resource values are agent-selected and the exact staged command will be shown before submission. Scientific outcomes remain pending.


## 2026-10-21 — training topology/context audit completed

CPU **23101968 completed 0:0 in 27s** on bfqi-delta-cpu/cpu-interactive, node cn061, 2 CPUs/8 GB/20-minute cap, zero GPUs; 0.015 allocated CPU-hours. Source `a159769` was pushed and verified in a separate 246-file snapshot. All 72 training slides, 73 checkpoints /76 events and 2160 planned context records verify: 1347 reduced-context records, 24 cached full-context reuses, 789 explicit unavailable-size exclusions. No classifier prediction, WSI/PNG read, fresh 60/calibration/test arrays, model/threshold fitting, download, new review rule or retry. All 315 tests passed before execution.

Sampled components span multiple cached RGB pieces on 60/72 slides and fragment a cached RGB piece on 21/72; groups overlap. Whole-bag sampled exclusions occur on 28 slides versus one RGB exclusion (unassigned RGB tiles can remain as context). Common-support comparisons on 39 RGB /31 sampled slides show mean absolute changes 10.14/12.80 with two reference tiles, versus 0.626/0.648 with 32. Common-support analysis was clarified after submission but before result inspection and is labeled secondary/descriptive. Six outside tiles supplies both NN5 neighbor counts; it does not calibrate a detector. [Findings, denominators, limitations and immutable remote receipts](panda_topology_context_results_v1.md).

Source/configuration/main/33 legacy hashes, six original input receipts, and prior S1/S3 registry receipts remain unchanged. All raw artifacts stay on Delta; original final output remains absent and own queue empty. This bounded stage is complete; a future versioned eligibility/abstention contract needs genuine-tissue controls before another policy claim.


## 2026-10-21 — numeric-context eligibility/native controls prepared

New candidate v1 gates fewer than six reference tiles and candidates occupying more than half the sampled bag. These are fixed computational/conservative engineering requirements, not fitted or validated foreignness thresholds. Structured results preserve diagnostic scores and unknown mapping; review and foreignness remain null, no tissue action. The runner reuses the old sealed 72-training-slide JSON without arrays, images, prediction calls or repeated measurements. Annotation enters afterward for positive/unknown-control counts.

All 336 tests pass with warnings as errors (30.99s), including 21 new artificial-fixture cases; original protocol/main and 33 legacy source hashes remain unchanged. The single bounded 2-CPU/4-GB/five-minute JSON-only Slurm run follows source freeze. [Frozen plan and limitations](../docs/panda_context_safety_v1.md). Latest “next” advances this new development scope; exact staged source/command will be shown before submission. New real coverage findings remain pending.


## 2026-10-21 — numeric-context/native-control accounting completed

CPU **23102229 completed 0:0 in 12s** from pushed `0340d60`, 2 CPUs/4 GB/five-minute cap on bfqi-delta-cpu/cpu-interactive, node cn095, zero GPUs (0.006667 allocated CPU-hours). All 72 original training slide records, 73 checkpoints /76 events and source/input/legacy hashes verify. No arrays/images, new scores or predictions, GPU/downloads, fitting, fresh60/calibration/test artifacts or retries. All 336 software tests passed before execution; subsequent changes are documentation only.

The fixed six-reference/majority candidate gate leaves 325/389 RGB and 316/377 sampled comparisons numerically eligible; 8/72 versus 28/72 slides have no eligible comparison. Genuine annotation-positive components remain eligible in 44/88 RGB and 75/116 sampled components, so numeric support still cannot establish foreignness. Most eligible comparisons include unknown RGB reference assignments (320/325 and 299/316). Review/foreignness outputs and alert/recall/harm metrics remain null, automatic tissue action none. [Results, denominators, preserved receipts and limitations](panda_context_safety_results_v1.md). This bounded stage is complete. A future review-only dependence report may integrate the contract without claiming foreignness; original final-test gate remains closed and evaluated fresh60 remain evaluated. All raw results stay on Delta; main/old source/experiments preserved.


## 2026-10-21 — saved-training dependence report integration prepared

New report builder/runner joins matching historical CONCH zero-shot top5pct predictions with frozen RGB topology/context gates. Every component stays in original order; decision changes remain visible even with numeric abstention. Reviewer JSON/HTML omits annotation/grade/foreign truth, includes saved physical metadata and uncertainty, and preserves all tissue with no foreignness or alert decision. Separate native-control accounting follows report construction.

All 350 tests pass with warnings as errors (40.88s), including fourteen new artificial-fixture tests; main and all 33 legacy source hashes remain unchanged. Source freezing precedes one bounded 2-CPU/4-GB/five-minute JSON-only Slurm export for original72 training slides /389 components. [Contract and immutable scope](../docs/panda_dependence_export_v1.md). Static HTML checks pass; browser policy blocked local-file visual preview, which remains unverified. No image/array/model calls, new scores, GPU/downloads, original final predictions or repeated experiment draws. New real export findings remain pending.


## 2026-10-21 — review-only saved-training export completed

CPU **23102479 completed 0:0 in 16s**, source `1a388ef`, 2 CPUs/4 GB/five-minute cap on bfqi-delta-cpu/cpu-interactive, node cn095, zero GPUs; 0.008889 allocated CPU-hours. All 72 original training slides /389 RGB components exported to 72 truth-free JSON +72 HTML +index; 145 rendered files, 73 checkpoints /76 events, 260 source files and eight pinned inputs verify. All 350 tests passed before execution; subsequent repository changes are documentation only. No new predictions/scores, images/arrays, GPU/downloads, fitting, original final/fresh/calibration predictions or job retry.

Cached dependence comprises 25 changing components /388 evaluable (23 slides /72), including ten native annotation-positive components on ten slides. Twenty of the 25 decisive comparisons numerically abstain; dependence stays visible without becoming an alert or foreignness claim. No ranking/tissue action; hidden annotations join only in separate controls. [Findings, source and preserved hashes](panda_dependence_export_results_v1.md). Static HTML checks pass; browser policy blocked local-file visual preview. Optional owner-only inspection failed on actual 0660 project-group file modes; all hashes passed and permissions preserved. This bounded stage is complete. Future existing-tile previews require a new bounded version; original final gate remains closed and all raw artifacts stay on Delta.


## 2026-10-21 — bounded saved-tile galleries prepared

New preview helper/runner adds up to four geometry-selected component tiles and four outside tiles to every original-training RGB component. Original encoding-input PNG bytes are validated and copied unchanged on Delta, with recorded physical field/coordinates and unknown RGB assignments preserved. Gallery subsets do not redefine score context or physical boundaries; all saved predictions/gates, null review/foreignness and tissue action none remain. All old reports are preserved.

Thirteen new artificial colored-PNG checks pass, including a 72-slide fixture. An initial test reference-count assertion was corrected from 1,152 to 576; no production logic changed for that correction. All 363 tests pass with warnings as errors (33.36s) before source freeze and one 2-CPU/4-GB/five-minute Slurm export, maximum 3,112 display references /512 MiB remote copies. [Frozen scope and provenance checks](../docs/panda_preview_export_v1.md). Existing three runtime freezes, main and 33 legacy source hashes remain unchanged. No local downloads, WSI/mask/NPZ/model calls, GPU, new fitting or final/fresh/calibration predictions. Scientific export counts remain pending; browser visual preview remains unverified.


## 2026-10-21 — bounded saved-PNG galleries completed

CPU **23102636 completed 0:0 in 23s**, source `ec5a71d`, 2 CPUs/4 GB/five-minute cap on bfqi-delta-cpu/cpu-interactive, node cn099, zero GPUs; 0.012778 allocated CPU-hours. Original 72 training slides /389 RGB components now have geometry-only image galleries: 1,638 unchanged PNG assets /2,605 references, 101,466,949 copied bytes under 512 MiB. All 1,783 output files /73 checkpoints /76 events and 72 source metadata groups verify. All 363 software tests passed before execution; subsequent changes are documentation only.

All saved predictions, gates, controls, original report fields and 145 old rendered hashes remain unchanged. Recorded source fields are 111.82315650205668 µm per axis; 176 preview references keep unknown RGB assignment. These are separate examples, not spatial reconstructions or new scoring references. No WSI/mask/NPZ/model call, new class score/embedding, GPU/download, final/fresh/calibration evaluation, retry or new clinical/foreignness claim. [Actual receipts, counts and remaining visual limits](panda_preview_export_results_v1.md). Browser layout remains unverified; source PNG bytes/dimensions and static HTML links/captions verify. This bounded gallery scope is complete; all pixels and detailed outputs stay on Delta, with main/legacy/source and original test seal preserved.


## 2026-10-21 — saved native/synthetic control audit prepared

A separate truth-revealed audit joins all 24 original training 5%-dose append cases /16 reused donor slides to native source PNGs and cached component counterfactuals. Same donor examples appear in native and synthetic contexts; original reviewer reports remain untouched. Validates original oracle receipts, exact score-vector/annotation append provenance, selected connected donor cells, physical/annotated areas and saved placement. Native overlapping-component exclusion is not a fragment-only oracle; null review/foreignness and no tissue action remain. Initially incorrect host predictions stay separate from newly induced errors.

All 386 tests pass with warnings as errors (33.90s), including 23 new artificial cases and a complete 24-pair fixture. No dependency added; main, 33 legacy files and four prior runtime freezes remain unchanged. One bounded CPU export follows pushed source freeze: 2 CPUs/4 GB/five minutes, no GPU; up to 384 display references /288 source PNGs /64 MiB. [Fixed provenance contract](../docs/panda_paired_control_audit_v1.md). Latest user “next” advances the proposed comparison, with resource values selected by the agent and exact command disclosed before submission. No new inference, stress draws, fitting, WSI/mask/NPZ processing, downloads or final/fresh/calibration evaluation. All pixels/detailed outputs remain on Delta. Real outcomes remain pending; browser layout remains unverified.
