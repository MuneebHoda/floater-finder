# Research tracks after the October 21 submission

S2 now has a completed bounded development experiment; the S3/S4 extensions below remain future research gates. Current work uses CONCH v1, existing train/calibration embeddings and bounded CPU analysis. The rejected v1 protocol is unchanged and all 24 held-out test predictions remain sealed. No additional dataset, checkpoint or GPU inference is authorized by this document.

## S2: binary low/high model sensitivity

The [completed S2 experiment](../reports/panda_s2_results_v1.md) tests native-mask-verified GP4/5-positive donor fragments inserted into ISUP 1 hosts. Its preselected mean scorer has 0/8 new calibration errors at every tested dose; secondary pooling is sensitive with poor clean specificity and tiny correct-host denominators. All 760 exact oracle checks pass. Same-grade GP3 tissue and different high-grade pattern compositions provide controls. These binary model transitions are not clinical Grade Group upgrades. Stronger claims require a validated grading model and pathologist assessment.

## S3: useful review evidence with genuine-cancer safety

The [ranked v2 investigation](../reports/panda_review_v2_results.md) separates visual inconsistency from prediction relevance and observed geometry. Its primary still detects 0/40 calibration fragments; no useful policy is supported. The goals remain ≤10% of unmodified slides alerted and ≤0.5 flagged components per slide. Native annotated cancer and hypothetical clean-prediction damage are safety controls. A pathologist review recommendation never authorizes deletion. A detector that improves fragment recall while exceeding the burden targets remains an exploratory prioritizer.

The existing calibration set is now part of iterative development. Any future normalization, score choice or threshold selection must remain within development data and be frozen before the single explicitly authorized final evaluation. An independently acquired development-validation cohort could strengthen claims, but requires a separate dataset selection, byte/resource estimate, approval and patient-overlap audit. Do not obtain new slides merely to replace unfavorable outcomes.

Observed RGB components are approximate tissue proxies. Future boundary work needs pathologist-verified topology and controls for faint tissue, touching sections and natural contamination positions. Current artificial right-edge placement is a procedural artifact. Evaluate location changes only in a new preregistered development experiment; do not treat absolute slide position, synthetic donor identifiers or injection labels as blinded detector features.

## S4: model and institution generalization

Read-only review covered the existing local remote-tracking branch `origin/feature/pathgen-clip` at **ffec067597ab892ac9824801213a798eee7ab09a**, without checkout, merge, inference or downloads. Its `src/floater_finder/pathgen.py` SHA256 is `dd716d4b1c39ba3b1c8bf91ba34562d08d1aaa30cac8f1d247f2144199bcc506`. The branch describes a local-checkpoint, Slurm/CUDA-only PathGen-CLIP adapter using OpenCLIP, records model/checkpoint/preprocessing provenance and disables automatic Hugging Face downloads. Its smoke configuration has null artifact paths and no pairs; its five-minute GPU wrapper is an unsubmitted historical draft. Its README explicitly records no real PathGen-CLIP experiment.

That historical adapter targets the earlier TCGA organ task. It does not establish a verified PathGen checkpoint, runtime, tokenizer/architecture compatibility, PANDA adaptation, throughput or clinical performance. None of those items were tested during this read-only branch review. Keep the branch unchanged.

Before any cross-model execution:

1. Verify the official model architecture, tokenizer, preprocessing, local checkpoint identity, access terms and actual installed interface. Obtain separate approval and byte estimates for new weights/data, if needed.
2. Create isolated image/text artifacts and prompts for each model. Equal vector dimension does not imply comparable embedding spaces. Current `check_compatible()` rejects differing model, revision, checkpoint, preprocessing or dimensions; preserve that contract.
3. Propose one separately approved, bounded one-GPU compatibility smoke before estimating a full batch from measured throughput. Existing CONCH timings are not verified PathGen timings. Do not use the old draft as submission authorization.
4. Freeze independent development choices per model, use matched slide/tile membership where appropriate, and retain all failures and resource measurements. No outcome-guided model switch on the current test set.
5. Add institutions or harder contamination scenarios only with a separately approved cohort, provenance and patient-split audit. Radboud-only slides and unverified patient IDs do not establish institutional or patient generalization.

The initial submission can remain complete while these research tracks stay unexecuted. Its evidence is the verified CONCH pipeline, measured model sensitivities, genuine-cancer counterexample and honest review-policy limitations.
