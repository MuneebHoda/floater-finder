# PANDA full-cohort embeddings and development baseline — October 20, 2026

**Subsequent development results:** connected S1 and calibration counterfactual jobs completed; see the [current checkpoint](panda_s1_and_piece_results_20261020.md). The clean-stage observations below are retained.

**GPU job 23054910 completed 0:0 in 21:46 on gpua018. CPU verification/baseline job 23055022 completed 0:0 in 3:04 on cn005.** The 120-slide Radboud cohort now has **50,729 verified CONCH v1 embeddings of 512 dimensions**: 49,785 new embeddings from 117 slides, plus 944 reused embeddings from three slides. No extra input/weight download or duplicate job occurred.

GPU elapsed was 0.3628 GPU-hour within the approved 0.75-hour cap; peak task RSS was 5,941,960 KiB and Slurm maximum GPU-memory usage was 5508M. The CPU verifier rehashed current tile/preparation inputs and saved artifacts, checked normalization/shape/IDs/coordinates/labels/splits and the shared text/model fingerprint. All 120 passed. Baseline scoring then took four seconds, using 72 training + 24 calibration slides only. All 24 final-test slides remain unscored. Local checks independently reproduced every confusion matrix, support, error list and prediction argmax from all 480 raw development prediction rows, and checked all split/label assignments against the manifest.

## Observed clean baseline

The prompts were fixed before encoding. Scores are cosine similarities, not calibrated probabilities. Masks did not enter scoring or clean selection. Original slide ISUP labels are never tile truth. The two tasks have different denominators: benign/cancer has 72 train / 24 calibration slides; low/high has 48 / 16.

| Task | Pooling | Train accuracy | Train balanced accuracy | Calibration accuracy | Calibration balanced accuracy |
|---|---|---:|---:|---:|---:|
| benign_cancer | mean | 77.8% | 74.0% | 66.7% | 65.6% |
| benign_cancer | top1pct | 72.2% | 63.5% | 79.2% | 71.9% |
| benign_cancer | top5pct | 84.7% | 82.3% | 83.3% | 78.1% |
| low_high | mean | 72.9% | 72.9% | 75.0% | 75.0% |
| low_high | top1pct | 60.4% | 60.4% | 62.5% | 62.5% |
| low_high | top5pct | 62.5% | 62.5% | 68.8% | 68.8% |

Top-5% benign/cancer calibration confusion is `[[5,3],[1,15]]` (rows true benign/cancer, columns predicted benign/cancer): **15/16 cancer sensitivity and 5/8 benign specificity**. This is a nondegenerate development candidate, with three benign false positives and one cancer false negative. Its 83.3% accuracy / 78.1% balanced accuracy is a descriptive calibration observation, not independent final performance or clinical validation. Mean pooling's low/high confusion `[[8,0],[4,4]]` misses 4/8 high-grade slides; Grade Group upgrading remains exploratory. No trained head has been fit.

The planned next bounded step is a **development-only S1 embedding stress test**, using existing saved embeddings and explicitly mask-confirmed, spatially connected donor subsets from other slides in the same split. This requires no additional GPU inference or downloads. Keep final-test scoring, clinical claims and calibrated detector/alert claims behind their remaining gates. Larger dedicated donor embedding batches still require separate approval.

## Evidence and limitations

- [Executed job facts and retrieval hashes](panda_full_cohort_completed_23054910.json), [all embedding verification records](panda_embeddings_verified_23055022.json), [all metrics and error IDs](panda_clean_baseline_23055022.json), [all raw predictions](panda_clean_predictions_23055022.json).
- [Protocol fixed before prediction inspection](../docs/panda_baseline_protocol_v1.md), [calibration confusion chart](figures/panda_clean_baseline_23055022/calibration_confusion.png), [training confusion chart](figures/panda_clean_baseline_23055022/train_confusion.png).
- Dataset masks: 119 usable / 120 files; all 39 usable high-grade masks contain native GP4/5. The failed LZW annotation stays preserved/excluded and unknown, and the GG1 native annotation/slide-label disagreement stays in the slide-level baseline. See the [data checkpoint](panda_120_ready_20261020.md).
- Patient independence is unknown. Sparse representative tile coordinates do not establish complete biopsy-piece topology. Connected donor subsets represent known synthetic embedding contamination, not actual foreign tissue in a patient slide.

Prior TCGA evidence, main and the original checkout are preserved. Changes remain uncommitted on feature/panda-tiling. There is no final-test disease performance, contamination recovery result or unmodified-slide alert-rate result yet.
