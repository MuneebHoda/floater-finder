# Predictor research evidence

Start with [the measured report](report.md). The training-only selection chose
`linear_mean_max_topk` for both tasks. This is an exploratory engineering choice:
paired slide-bootstrap intervals include zero improvement, and the benign/cancer
model performs worse than historical top-5% on repeatedly inspected calibration.
No independent validation or final-test success is claimed.

- `run/`: all 57 original completion-hashed outputs from CPU job **23068979**,
  source **0f2fc5fa3413ac3c7c5d1cd81181fd9c57017140**. Selection was persisted
  before opening calibration arrays. Final training-only C values are BC mean
  0.01, BC concatenated 0.1, grade mean 1, grade concatenated 0.01.
- `adapter_acceptance/`: exact-hash outputs from correction-only CPU job
  **23069033**, source **22f44d9af6191df283ffe9d9f0b1243ac8ec2d02**. All 480
  historical zero-shot score vectors and 80 frozen linear calibration predictions
  recover exactly. No retraining or primary-selection changes occurred. The initial
  run's 158 tiny zero-shot roundoff differences remain preserved in `run/`.
- `cached_native_annotations.json`: bounded, read-only join of 96 development
  IDs against prior source directories. All 92 available native audit JSON hashes
  match their original tiling completion; three profile audits are absent and one
  mask is corrupt. No WSI, image, embedding or final-test artifact was opened.
- `margin_distributions.json`, `native_annotation_case_studies.json`,
  `native_annotation_correlations.json`, `paired_model_comparisons.json`: posthoc
  descriptive diagnostics, using corrected zero-shot margins. They did not select
  predictors. Missing annotation values remain unknown.
- Execution receipts record exact resource requests, commands, versioned Delta
  source/output paths, source/archive hashes, scheduler outcomes and the initial
  QoS rejection. Original scientific artifacts and protocols are unchanged.

Both jobs used two CPU cores and zero GPUs. The CV job requested 8 GB/30 minutes
and completed in 23 seconds (task 14 seconds, peak 426,492 KiB). Adapter acceptance
requested 4 GB/10 minutes and completed in 13 seconds (task 5 seconds, peak
318,144 KiB). Together this is 0.020 allocated CPU-hours by elapsed wall time.

Portable, pickle-free primary files are in
`run/models/{benign_cancer,low_high}/linear_mean_max_topk/`. The corresponding Delta
root is `/work/nvme/bfqi/mhoda/floater-finder/panda-predictors/v1-20261021T011509Z/models`.
Load with `floater_finder.predictors.load_predictor(directory)` and use
`score_slide(slide)` to enforce full embedding-model, preprocessing, source-kind
and dimension compatibility. Scalar scores from different model types have
different scales; balanced logistic outputs are not calibrated probabilities.

Reproduce the report without scoring slides or opening held-out data:

```bash
PYTHONPATH=src python scripts/summarize_panda_predictors.py \
  --input reports/panda_predictors_v1/run \
  --output results/panda/predictor_report_reproduction_v1 \
  --coverage-receipt reports/panda_cohort_cpu_verified_120_20261020.json \
  --adapter-verification reports/panda_predictors_v1/adapter_acceptance \
  --cached-native-annotations reports/panda_predictors_v1/cached_native_annotations.json
```

The report output must be fresh. Input completion hashes permit byte verification
of the two original runs. All 24 final-test predictions remain sealed, historical
S1/S2/detector findings are unchanged, and no submission materials were edited.
