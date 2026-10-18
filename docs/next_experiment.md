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

The current frozen-threshold smoke is complete. Before claiming a useful detector, use a larger, representative development cohort and a fresh held-out evaluation cohort. The existing evaluation patients must not drive threshold tuning. Preserve calibration-only threshold selection, fixed prompts, patient separation and exact oracle stopping rules. Broader sampling across each WSI is needed before full-slide robustness or throughput claims. Unknown cohort paths, quota and institution/report metadata remain explicit in [NCSA setup](ncsa_setup.md).

The first milestone remains CONCH only. No bulk cohort acquisition or additional model is implied by these results.

Exact next command from this checkout to review the verified detector evidence:

```sh
cat reports/conch_detector_smoke_22994885.json
```
