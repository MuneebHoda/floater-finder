# CONCH v1: completed smoke and next study

The raw-pixel CONCH v1 workflow now runs through Slurm end to end: physical tiling, matched image/text encoding, connected synthetic contamination, exact oracle recovery, separate-patient calibration and detector controls. This is a **four-patient, 128-tile-subset smoke**, not a population benchmark.

## Verified execution

- Six new Delta jobs completed successfully; [accounting and queue evidence](../reports/ncsa_jobs_20261018.json) records actual resources and exit codes.
- [Scheduled canonical GPU smoke](../reports/conch_one_pair_smoke_22994635.json): two evaluation slides, 128 tiles each, normalized 512-dimensional vectors and six oracle passes. A repeat fixes cross-process transform provenance and exactly reproduces the initial vectors.
- [Bidirectional contamination smoke](../reports/conch_smoke_results.md): two directions, five seeds, six levels, 60 oracle passes and 180 pooled-score rows. Original mean-pooled predictions did not change; top-K predictions sometimes changed in these subsets.
- [Patient-separated detector smoke](../reports/conch_detector_results.md): two additional development patients, two evaluation patients, 60 oracle passes, 180 variant rows, zero exclusions and complete oracle/no-filter/random-removal controls.
- The fixed combined threshold is conservative: at 10% requested contamination, mean AUROC is 0.949 but injected-tile detection is only 3.85% across the two evaluation hosts and five seeds. This is a limitation, not validated clinical performance.

The four measured scanner calibrations are retained. Source spatial coordinates are reused only as tissue-region candidates; incompatible shared CONCH v1.5 feature values are never read. A common 256-micron field is exported at 512 pixels using fractional physical crops. Exact masks, geometry, raw scores, exclusions, metric denominators, source/input hashes and frozen prompts/settings are saved.

## Inputs and authorization

The initial [4.80 GB input plan](../configs/ncsa_conch_v1_download_plan.json) supplied the evaluation pair and pinned original checkpoint. Under the subsequent instruction to continue this plan without repeated permission requests, two further public, GDC-verified diagnostic slides were staged for development-only calibration: [5.19 GB calibration input plan](../configs/ncsa_calibration_download_plan.json). Total unique inputs are 9,990,121,727 bytes, all checksum-verified on Delta; no new model checkpoint was needed. This was a bounded calibration extension, not a bulk cohort download.

Inputs live under `/work/nvme/bfqi/mhoda/floater-finder/inputs/`. Development patients are `TCGA-2A-A8VO` and `TCGA-2F-A9KO`; evaluation patients are `TCGA-2A-A8VL` and `TCGA-2F-A9KP`. These sets are disjoint. Clean means unmodified/no synthetic injection; native contamination has not been reviewed. No clinical reports or normalized institution mapping are available.

## Next study

The current frozen-threshold smoke and **development-only cutoff diagnostic** are complete. CPU job `22995268` reused the already-created `[128,512]` artifacts from each of `TCGA-2A-A8VO` and `TCGA-2F-A9KO`, completing `0:0` in 12 seconds. No new image embeddings, raw slides, checkpoint downloads or GPU allocation were needed. [Observed cutoff tradeoff and validation](../reports/conch_threshold_results.md).

The [frozen diagnostic configuration](../configs/ncsa_threshold_diagnostic.json) compares clean-development quantiles 0.90, 0.95, 0.975, 0.99 and 0.995, retaining the same prompts, 1 mm spatial exclusion, 0.1 mm smoothing and equal organ/visual weights. It uses both development host/donor directions, six contamination levels and five seeds. Every trial must pass exact oracle recovery. Record per-patient clean removal counts, raw tile scores, injection metadata and denominator-bearing metrics. The scheduled request is two CPUs, 4 GB, five minutes and no GPU.

This is **resubstitution**: the two development patients supply both clean calibration and synthetic diagnostic trials. Its estimates are optimistic, and the repeated seeds are not independent patients. The script cannot load evaluation artifacts; neither the current evaluation patients nor their donor identities may influence cutoff selection. No cutoff is automatically selected, and the existing nominal 1% clean-tile budget remains the reference rather than a promise about unseen data.

At the 97.5th-percentile combined cutoff, mean development donor detection at 10% requested contamination was 89.23%, with 2.34% original-host removal. The unmodified prostate subset alone loses 4.69%, illustrating why a pooled clean-removal rate is insufficient. These observations do not establish transfer to unseen patients, and no revised cutoff was selected.

The dependency maintenance step is complete locally and for the new Delta image runtime. Pillow 12.3.0 and optional-test pytest 9.0.3 fall outside every vulnerable range in the [recorded 37-alert/19-advisory inventory](../reports/dependency_alerts_20261018.json). Focused regression probes and 91 local tests pass. CPU preparation `22995419` and A100 compatibility `22995434` completed `0:0`; all 256 development tiles and image/text vectors matched the preserved baseline exactly. New artifacts record Pillow version and are kept distinct from historical artifacts. GitHub alert closure has not been checked after a push, and this is not a whole-dependency audit. [Verified runtime and evidence locations](ncsa_setup.md#patched-image-runtime-verified-on-a-scheduled-a100).

The [expanded-pilot plan](expanded_pilot_plan.md) contains 16 new public diagnostic slides, **21.24 GB**, with verified GDC metadata/checksums and matching shared-coordinate filenames. Eight new development patients and eight fresh evaluation patients are separate by patient and TCGA source-site prefix; prefixes are not verified institutions. The user approved the exact acquisition on 2026-10-18. CPU download job `22995933` completed `0:0` in 4 minutes 42 seconds; all 16 files passed size/streaming MD5 checks with no failures. [Accounting, manifest comparison and storage checks](../reports/ncsa_pilot_download_verification_20261019.json). Raw-header and protocol validation remain separate gates. It is a feasibility sample rather than a representative population cohort.

Raw-header/MPP/coordinate checks and broader sampling now pass for all 18 planned patients. CPU job `23005299` validated four × 96-tile windows per patient after preserving the failed 128-tile-window candidate; 768 development QC tiles decoded successfully. The [study design is frozen](expanded_pilot_protocol.md), including a development-only leave-one-patient-out cutoff-selection rule and 1% original-host removal budget. [Technical evidence](../reports/conch_pilot_preflight_results.md).

The development encoder/selection runner is now implemented and tested. GPU job `23028013` produced **3,840 development embeddings**; CPU job `23028265` completed the ten declared clean-development folds. **No candidate met the fixed 1% original-host removal budget**, so no final numerical calibration was frozen and held-out scoring remains stopped. At the most conservative quantile, the worst combined-score control removed 19/384 original-host tiles (4.95%), compared with the allowed three. All patients/settings were retained; this outcome does not establish clinical false-positive performance. [Complete results and verification](../reports/conch_development_results.md).

Next, inspect development-only score distributions by patient/organ and normalization shifts across folds using the existing artifacts. Do not raise the budget, add quantiles, drop patients or alter the frozen rule to manufacture a pass. Any proposed method revision needs a recorded protocol amendment before numerical calibration and held-out evaluation. Selected windows remain subsets rather than full slides; institution/report metadata, native pathology review and project storage quota remain unresolved in [NCSA setup](ncsa_setup.md).

The first milestone remains CONCH only. No bulk cohort acquisition or additional model is implied by these results.

Exact next command from this checkout to review the verified detector evidence:

```sh
cat reports/conch_development_results.md
```
