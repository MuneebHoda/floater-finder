# Fresh Radboud60 frozen clean-baseline results

The approved Delta-only stage completed successfully. GPU job **23081929** encoded
**60 slides / 25,915 tiles** into 512-dimensional CONCH v1 image vectors with
matching text artifacts. CPU job **23082231** verified all 60 per-slide artifact sets before
running the four already frozen scorers. No model was refit, threshold changed,
case replaced or excluded. No acquisition/tiling was repeated, and no dataset,
weights or output file was downloaded to the Mac. Detailed outputs remain on Delta.

## Frozen outcomes and exact denominators

| Task / predeclared role | Unique slides | Balanced accuracy | 95% stratified-slide bootstrap interval | Accuracy |
| --- | ---: | ---: | --- | ---: |
| Benign/cancer — frozen primary linear | 60 | 80.0% | 70.00–88.75% | 76.7% |
| Benign/cancer — historical top-5% | 60 | 75.0% | 63.75–86.25% | 78.3% |
| Low/high — frozen primary linear | 40 | 72.5% | 60.00–85.00% | 72.5% |
| Low/high — historical mean | 40 | 65.0% | 55.00–77.50% | 65.0% |

The benign/cancer denominator is 20 benign and 40 cancer slides. Low/high is 20 GG1
and 20 ISUP 4–5 slides; benign and absent ISUP 2/3 cases are outside that task.
Both primaries remain `linear_mean_max_topk`, selected using the earlier training-
only nested CV. The historical comparators remain corrected frozen CONCH top-5%
benign/cancer and mean low/high scoring. Primary balanced-accuracy point estimates exceed historical
comparators here; no paired superiority claim follows from these estimates.

Confusion matrices have **rows=true class, columns=predicted class**:

- Benign/cancer — frozen primary linear: `[[18, 2], [12, 28]]`; class order `['benign', 'cancer']`; supports `[20, 40]`.
- Benign/cancer — historical top-5%: `[[13, 7], [6, 34]]`; class order `['benign', 'cancer']`; supports `[20, 40]`.
- Low/high — frozen primary linear: `[[18, 2], [9, 11]]`; class order `['low_grade', 'high_grade']`; supports `[20, 20]`.
- Low/high — historical mean: `[[19, 1], [13, 7]]`; class order `['low_grade', 'high_grade']`; supports `[20, 20]`.

Per-class recall, with Wilson 95% intervals:

| Task / role | First class recall (95% interval) | Second class recall (95% interval) |
| --- | --- | --- |
| Benign/cancer — frozen primary linear | benign: 90.0% (69.9–97.2%) | cancer: 70.0% (54.6–81.9%) |
| Benign/cancer — historical top-5% | benign: 65.0% (43.3–81.9%) | cancer: 85.0% (70.9–92.9%) |
| Low/high — frozen primary linear | low_grade: 90.0% (69.9–97.2%) | high_grade: 55.0% (34.2–74.2%) |
| Low/high — historical mean | low_grade: 95.0% (76.4–99.1%) | high_grade: 35.0% (18.1–56.7%) |

The cancer primary misses **12/40 annotated cancer slides** under this capped
representative sampling; the grade primary calls **9/20 high-grade slides low**.
The historical cancer comparator has higher cancer recall (34/40) with more
benign false positives (7/20 versus 2/20 for the primary). Higher balanced accuracy
does not mean higher cancer sensitivity, higher overall accuracy, or clinical
validity. Preserve the declared primary rather than switching using fresh outcomes.

The two linear models have descriptive, uncalibrated probability diagnostics:

| Primary | Brier score | ECE, five fixed bins |
| --- | ---: | ---: |
| Benign/cancer | 0.189570 | 0.171207 |
| Low/high | 0.161521 | 0.123808 |

Balanced logistic outputs are not calibrated clinical probabilities; class
weighting changes the prior. Historical cosine similarities are not probabilities,
so Brier/ECE are not assigned. No temperature, Platt or isotonic fitting occurred.

Bootstrap intervals use 2,000 predeclared stratified resamples of unique slides,
seed 20261024, conditional on fixed models and selected cases. They do not include
training/selection uncertainty or establish patient independence. Selection is
slide-disjoint from the 129 prior documented exclusions, but patient identifiers
remain unavailable. This is Radboud-only validation with at most 512 representative
112-µm requested fields per slide, not full-slide or full-grade-range clinical
validation. Tile masks establish sampled annotation, not a diagnosis for each tile.
Unmodified means no synthetic insertion; native floaters were not clinically
adjudicated. These 60 slides have now been evaluated and must not be represented
as fresh, unscored cases in future work.

## Observed execution and provenance

| Stage | Job | Exit | Elapsed | Resources |
| --- | --- | --- | --- | --- |
| CONCH encoding | 23081929 | 0:0 | 743 seconds | One GPU, 4 CPUs, 16 GB; 30-minute cap |
| Array/input verification and four frozen scorers | 23082231 | 0:0 | 66 seconds | No GPU, 2 CPUs, 8 GB; 20-minute cap |

The GPU allocation used **0.2064 GPU-hours**, below its 0.5-hour cap. The CPU
baseline used 0.0367 allocated CPU-hours. These derive from root-job elapsed time,
not a billing reconciliation. Source/model/input gates passed, all 200 task/role
prediction records have the exact 60/40 eligible slide sets, and independent
lightweight inspection reproduced every confusion matrix from saved predictions.
Array, image and model processing stayed inside Slurm; login-node inspection read
only small JSON/CSV metadata, checked receipts, and inspected file presence/sizes.

Pipeline source: `bfd4416936d2c35d764d6fd46e1017f110ef48db` at
`/u/mhoda/floater-finder/releases/panda-fresh-baseline-v1-20261021T023142Z/source`. All 226 staged file hashes rechecked before submission.
The frozen protocol SHA256 remains
`d06827fe964cc7bb14f9cd7403759fd6c106e9f3c41707bd5855f48bb4a30da4`. The unchanged source, four model hashes,
checkpoint/preprocessing identity, prompt/text fingerprints, cohort membership and
physical sampling contract were checked. The existing checkpoint was rehashed
inside the GPU job; its SHA256 remains
`40a9644b9ba0e83a74576e0a5e5f7313599fa9c9cdaf3c20f8a3e271b0e9ae7c`.
The exact encoding-directory SHA256 is
`fd504540c7b90ff241248edb4b14dedf7478b5993c483f7766086cc2e7442bc8`.

Remote root:

`/work/nvme/bfqi/mhoda/floater-finder/panda-fresh-baseline/radboud60-v1`

Preserved artifacts there:

- `embeddings/<image_id>/` — image/text NPZs, timing and completion receipts for 60 slides.
- `embeddings-verified-v1.json` — SHA256 `242050b5398cc0473e641760d1aed96dbae46b871a8feebefb653de9318b4d4e`.
- `clean-baseline-v1/{execution,predictions,summary,completion}.json` — raw frozen decisions, all metrics and hashes; completion SHA256 `8b6d86b01d40fd05651211de5f8faee50806e3a1dd814bb18d44cccd7f6e9248`.
- `reports/encoding-baseline-authorization-v1.json` — exact approved bounds and commands; SHA256 `56fcca0c7e8d422fdae84fb33b9599f03cba81e2f448963e7694e8bbd07bff87`.
- `reports/gpu-receipts-v1.json` — GPU metadata/model inspection, SHA256 `46bb95ed1834308ba94e967b28d602e7f2dc79b50ff335902b6e8280f3d8931f`.
- `reports/baseline-output-check-v1.json` — aggregate output checks and confusion-matrix recomputation; SHA256 `7064d2962d983c97e0cff45d96f267aba3b9e45a081cb440ed1c43811ae527b0`.
- `reports/execution-completion-v1.json` — final Slurm resource ledger and empty-queue snapshot; SHA256 `3239e61936a5f6ed5cb75ebe52de915bb43aaf6bde899f4384731704bd6f49db`.

The [CPU-stage record](panda_fresh_cpu_execution_v1.md) preserves acquisition,
tiling, provenance limits and the exact subsequently approved commands. No new
GPU or CPU job is implied by this completed approval. Existing 120-slide artifacts,
TCGA evidence, failed floater-policy results, main and all 24 original final-test
predictions are preserved. No original test prediction was computed. Local notes
contain bounded aggregate facts; detailed reports, raw predictions and payloads
remain remote. The last unchanged software suite passed 284 tests; this checkpoint
changes documentation only. Frozen source/protocol/main guards and all 33 legacy
source hashes matched; whitespace checks passed. The final own-queue snapshot is empty.

This completes the end-to-end PANDA → tiling → CONCH embeddings → frozen clean
baseline stage. It does **not** validate a floater detector, component-alert
threshold, tissue removal, or contamination-error recovery. Further fragment
experiments need a separate predeclared scope; no such job was launched here.
