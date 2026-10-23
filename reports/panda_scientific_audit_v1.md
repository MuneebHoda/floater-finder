# Scientific-results audit of commit 434b401

This audit uses committed outputs only; it generates no new predictions. All 24 final-test slides remain unscored.

- The clean benign/cancer baseline uses **72 train / 24 calibration slides** (24/48 and 8/16 benign/cancer supports). Low/high uses **48 / 16**. Top-5% calibration confusion is `[[5,3],[1,15]]`: 20/24 accuracy, 78.125% balanced accuracy, 15/16 cancer recall and 5/8 benign recall. These are development estimates, not independent test performance.
- The **192 S1 trials are 32 hosts × 6 doses**, not 192 patients. There are 24 train and 8 calibration benign hosts, 21 reused donor slides, and 53 distinct source slides in total. Source slides and splits differ; patient identities are unknown. One seed and nested fragments create correlated observations.
- A new cancer error means a **clean-correct benign host becomes predicted cancer**. Its denominator is the number of originally correct benign hosts, not all hosts, all mixtures, or cancer responses. Initial false positives that stay cancer are not newly induced errors. Reverse changes are recorded separately.
- Native-mask-positive donor embeddings with known synthetic injection labels are not evidence of actual contamination. Unmodified annotated cancer components are negative controls for foreignness; genuine tissue can legitimately control a prediction.
- All 192 oracles recover original arrays/order/metadata and scores. That validates the injection/removal plumbing, not learned detection performance.
- Piece analysis has **24 unmodified calibration cases, 18 evaluable, 6 empty-counterfactual unevaluable**. The 7/18 dependence rate is not a review-alert rate. No alert policy existed. Forty positive-dose mixtures use the same eight hosts; eight decisive foreign-component reports reflect repeated doses. Two unmodified cases lose a cancer prediction when a component containing annotated cancer is omitted.
- Representative tile-cell connectivity is not validated physical tissue topology. Sparse gaps, merging and incomplete component membership require a new development-only check before any final protocol can claim meaningful tissue pieces.

Calibration transitions, with original-correct denominators:

| Pooling | Dose | Hosts | Originally correct | New cancer errors | New error / originally correct | Initially wrong → correct |
|---|---:|---:|---:|---:|---:|---:|
| mean | 0% | 8 | 5 | 0 | 0.0% | 0 |
| mean | 0.5% | 8 | 5 | 0 | 0.0% | 0 |
| mean | 1% | 8 | 5 | 0 | 0.0% | 0 |
| mean | 2% | 8 | 5 | 0 | 0.0% | 0 |
| mean | 5% | 8 | 5 | 1 | 20.0% | 0 |
| mean | 10% | 8 | 5 | 4 | 80.0% | 0 |
| top1pct | 0% | 8 | 4 | 0 | 0.0% | 0 |
| top1pct | 0.5% | 8 | 4 | 1 | 25.0% | 0 |
| top1pct | 1% | 8 | 4 | 1 | 25.0% | 0 |
| top1pct | 2% | 8 | 4 | 1 | 25.0% | 0 |
| top1pct | 5% | 8 | 4 | 1 | 25.0% | 0 |
| top1pct | 10% | 8 | 4 | 2 | 50.0% | 0 |
| top5pct | 0% | 8 | 5 | 0 | 0.0% | 0 |
| top5pct | 0.5% | 8 | 5 | 1 | 20.0% | 0 |
| top5pct | 1% | 8 | 5 | 1 | 20.0% | 0 |
| top5pct | 2% | 8 | 5 | 2 | 40.0% | 0 |
| top5pct | 5% | 8 | 5 | 2 | 40.0% | 0 |
| top5pct | 10% | 8 | 5 | 2 | 40.0% | 0 |

The full train/calibration transition tables are in [machine-readable audit](panda_scientific_audit_v1.json). No clinical validity, calibrated alert performance, true patient independence or final-test effectiveness is established.
