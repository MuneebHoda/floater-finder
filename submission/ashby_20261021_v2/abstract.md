# Floater Finder

## Submission abstract

Floater Finder investigates whether a pathology model’s prediction depends on a suspicious tissue fragment and whether that evidence can support focused pathologist review while preserving genuine cancer.

We built a reproducible PANDA-to-CONCH v1 pipeline on NCSA Delta using 120 real Radboud prostate biopsies and 50,729 spatially indexed embeddings. Slides split into 72 training, 24 calibration and 24 untouched test cases. Our frozen zero-shot benign/cancer engineering scorer achieves 20/24 calibration accuracy and 78.1% balanced accuracy.

S1 inserts connected, natively annotated cancer features into benign hosts at controlled doses. All 192 exact oracle restorations pass. At 2–10% requested dose, the primary scorer develops new cancer predictions in 2/5 originally correct calibration hosts. This endpoint compares with the original host label, although the synthetic mixture genuinely contains cancer. Repeated doses and reused donors are correlated.

Genuine annotated cancer can also change predictions under exclusion. Influence therefore cannot establish foreignness. The combined v1 review policy detects 0/40 calibration fragments. A separately versioned ranked v2 policy also detects 0/40 on known calibration. An unbudgeted ranking reaches 21/40 hits but alerts on every clean slide, exceeding review targets.

S2 completes 760 exact oracle checks. Its preselected mean low/high scorer shows 0/8 new calibration errors at all tested primary doses, alongside limited clean high-grade sensitivity. Secondary scorers are unstable and poorly specific.

The contribution is a verified experimental platform, measured model sensitivity and transparent negative review-policy findings. Natural-floater detection, patient independence and clinical usefulness remain unverified. No tissue is automatically removed, and the held-out test remains unscored.

## Scope and form adaptation

All numbers are observed training/calibration results. Known calibration in v2 is iterative development, not independent validation. S2/v2 results were incorporated only after successful bounded CPU execution and validation. No clinical Grade Group upgrade is claimed. Adapt length only after the organizers’ form limit is known.

Evidence: `reports/panda_review_results_v1.md`, `reports/panda_s2_results_v1.md`, `reports/panda_review_v2_results.md` and the package’s `evidence_manifest.json`.
