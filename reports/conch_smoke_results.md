# CONCH v1: descriptive two-patient smoke

Scheduled A100 inference (job `22994635`) and CPU analysis (`22994703`) completed successfully. Each of two diagnostic slides contributes one connected subset of 128 physically resampled tiles. Each patient is used as a host with the other as donor, across five fixed seeds and six requested contamination levels. This is synthetic embedding contamination, not confirmed real tissue floaters or a cohort benchmark.

Both original subsets receive their expected organ label for mean, top-1% and top-5% pooling. All **60 oracle trials pass**, with 180 pooled-score rows and zero excluded trials. Independent local checks reproduce all predictions, counts and denominators; maximum pooled-score difference is 5.96e-8 (float32 rounding across NumPy versions; acceptance tolerance 1e-7). The denominator is two unique host slides per percentage/seed/pooling stratum. Seeds and reciprocal directions do not add independent patients.

| Requested contamination (%) | Realized contamination (%) | Mean flip rate | Top-1% flip rate | Top-5% flip rate |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 0.00 | 0.00 | 0.00 |
| 0.5 | 0.78125 | 0.00 | 0.20 | 0.00 |
| 1 | 1.5625 | 0.00 | 0.40 | 0.00 |
| 2 | 2.34375 | 0.00 | 0.40 | 0.00 |
| 5 | 5.46875 | 0.00 | 0.40 | 0.40 |
| 10 | 10.1562 | 0.00 | 0.40 | 0.40 |

Rates are arithmetic means across five seed-specific rates, each with two eligible hosts. The actual foreign counts are 0, 1, 2, 3, 7 and 13. Raw class cosine scores, exact prompts, source/input hashes, exclusions and summary denominators remain in the retrieved experiment artifacts.

The [chart](figures/conch_contamination_smoke.png) and [raw pooled scores](metrics/conch_bidirectional_22994703.csv) are saved for review; validated JSON evidence is `reports/conch_bidirectional_smoke_22994703.json`. A subsequent [patient-separated detector smoke](conch_detector_results.md) uses two additional development patients. Larger held-out cohorts, report linkage, institution mapping and whole-slide robustness remain unverified.
