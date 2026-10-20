# Frozen development cohort and cutoff selection

The completed acquisition, diagnostic and preflight evidence was committed as `f0f19a4`. The development runner was committed as `a6d826d`. The original frozen protocol and its base computational sources remain unchanged. This stage uses only the ten development patients; held-out embeddings and performance outputs are not opened.

The encoder re-verifies existing inputs and checkpoint, extracts the frozen four × 96 physical tiles per patient, and encodes projected normalized 512-dimensional CONCH v1 image/text artifacts. Geometry must match the recorded preflight exactly. Repeated text artifacts must share one fingerprint, and every artifact must use the approved checkpoint and Pillow 12.3.0. No dataset or weight download is performed.

The selection runner fits each fold's normalization and thresholds on nine development patients and scores only the omitted original development patient. It never selects on synthetic mixtures or evaluation patients. It chooses the smallest frozen candidate quantile satisfying at most 1% original-host removal on all ten omitted patients and all three variants. With 384 tiles, at most three removals are allowed per patient/variant. If none qualifies, it writes `no_feasible_cutoff`, preserves all raw scores/counts, and creates no final calibration. This is selection, not independent clinical validation.

## Execution

GPU job `23028013` was submitted for ten development patients, 3,840 image embeddings, one A100, four CPUs, 16 GB and 30 minutes under account `bfqi-delta-gpu`, QoS `bfqi-delta-gpu-mhoda`. It runs on `gpuA100x4-interactive`; the normal queue's dry-runs predicted a much later slot. This documented short queue permits one running job per user and has a one-hour limit, with a higher charge factor than the normal A100 queue. [NCSA partition policy](https://docs.ncsa.illinois.edu/systems/delta/en/latest/user_guide/running_jobs.html). No duplicate GPU request was submitted.

The job **completed `0:0` on `gpua038` in 10 minutes 5 seconds**, producing all **3,840 image embeddings, ten `[384,512]` patient artifacts**, and a shared frozen text/model fingerprint. All 61 retrieved small-artifact hashes match Delta. Independent checks confirmed patient identity, split, exact preflight geometry, checkpoint, prompts, Pillow version and normalization; image norms range from 0.9999998807907104 to 1.0000001192092896. No evaluation patient was encoded. Full exported tile PNGs remain on Delta; retrieved embeddings remain ignored under `results/development/cohort_encoding_23028013/`.

[Immutable source/resource record](ncsa_development_submission_20261020T020759Z.json), [encoding report](conch_development_encoding_23028013.json), [independent verification and accounting](ncsa_development_encoding_verification_20261019.json). The output is `/work/nvme/bfqi/mhoda/floater-finder/pilot-development/20261020T020759Z/encoding`; staged source is `/u/mhoda/floater-finder/releases/20261020T020759Z`.

CPU selection follows only successful, verified development encoding. No held-out encoding or detector evaluation was submitted. Final numerical calibration requires a feasible selection under the frozen rule.

Software validation: **105 tests passed with warnings as errors**. Tests cover omitted-patient isolation, a no-feasible-cutoff stop, agreement with the frozen calibrator on varying signals, artifact/input guards, login-node rejection and unchanged protocol hashes. The frozen base implementation was reused without modification.

## Selection outcome: no feasible cutoff

CPU job **`23028265` completed `0:0` on `cn137` in 15 seconds**, with two CPUs, 8 GB and a 30-minute cap under account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`. All ten leave-one-patient-out folds and **150 patient/quantile/variant rows** completed. Each fold fitted on exactly the other nine patients (3,456 tiles). All 32 retrieved artifacts match remote hashes; independent checks reproduced every saved removal count, budget decision and the absence of a feasible quantile. The final queue was empty.

| Quantile | Worst removed count / 384 | Worst original-host removal | Feasible for every patient/variant? |
| --- | ---: | ---: | --- |
| 0.900 | 158 | 41.15% | No |
| 0.950 | 103 | 26.82% | No |
| 0.975 | 68 | 17.71% | No |
| 0.990 | 25 | 6.51% | No |
| 0.995 | 19 | 4.95% | No |

Each row's worst case was the combined score on omitted development patient `TCGA-2A-A8VO`. At the most conservative candidate, organ-only exceeded the three-tile limit on three patients, visual-only on three, and combined on two. The per-patient counts at `q=0.995` are:

| Omitted development patient | Organ-only removed | Visual-only removed | Combined removed |
| --- | ---: | ---: | ---: |
| TCGA-2A-A8VO | 11 | 5 | 19 |
| TCGA-2F-A9KO | 0 | 2 | 0 |
| TCGA-DK-A1A7 | 0 | 0 | 0 |
| TCGA-EJ-A46B | 4 | 7 | 8 |
| TCGA-FC-A5OB | 0 | 0 | 0 |
| TCGA-G9-6379 | 6 | 1 | 0 |
| TCGA-GV-A3QH | 0 | 4 | 2 |
| TCGA-HC-7230 | 1 | 0 | 0 |
| TCGA-XF-A9SW | 1 | 2 | 0 |
| TCGA-ZF-A9RN | 0 | 0 | 0 |

The scheduled computation succeeded; the **scientific retention gate did not pass**. `selected_quantile` is null. No final numerical calibration or calibration-freeze file was created, and no held-out experiment was submitted. The 1% budget, candidate list, patients, prompts, sampling and scoring weights were not changed after this outcome. These counts concern original-host tiles in unmodified inputs; native floater annotations are unavailable, so they are not clinical false-positive estimates.

Evidence: [selection and all 150 controls](conch_development_selection_23028265.json), [CSV](metrics/conch_development_selection_23028265.csv), [independent verification/accounting](ncsa_development_selection_verification_20261019.json), [submission](ncsa_selection_submission_20261020T020759Z.json), [log](ncsa_development_selection_job_23028265.log). Native fold scores, base calibrations and thresholds remain under ignored local `results/development/cohort_selection_23028265/` and remote `/work/nvme/bfqi/mhoda/floater-finder/pilot-development/20261020T020759Z/selection`.

The next work is development-only diagnosis of patient/organ score distributions and fold-normalization shifts. These observations do not identify a cause or justify a new threshold. Any proposed method revision must be recorded as a protocol amendment before a final calibration and held-out evaluation; preserve the eight untouched evaluation patients and this failed gate.
