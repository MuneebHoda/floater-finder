# Submission and development checkpoint — October 20, 2026

Branch: **`feature/panda-tiling`**. Starting reviewed/pushed commit: `06c7b771399c26b9dbc390b7e4bd73b077878e95`. Separate experiment source commits were frozen before their outcomes: **S2 `35e0a8dae57e22808420b45ae040fc2f8c3710a5`**, **ranked detector v2 `668d9b8c4e3e8aa300bda6ff15e416c601c2e024`**. The final integrated commit is available from `git rev-parse HEAD`; no branch merge occurred.

## Finished submission package

The final package is [`submission/ashby_20261021_v2/`](../submission/ashby_20261021_v2/). It contains a **19-slide standalone PPTX and matching PDF**, project abstract, **480-second / 908-spoken-word presentation script**, four-minute Q&A preparation, checklist, native authoring source, slide content, embedded media and provenance. Use this final revision; earlier presentation drafts stay in the ignored build archive.

- [PowerPoint](../submission/ashby_20261021_v2/floater_finder_ashby_v2_final.pptx).
- [PDF](../submission/ashby_20261021_v2/floater_finder_ashby_v2_final.pdf).
- [Abstract](../submission/ashby_20261021_v2/abstract.md), [eight-minute script](../submission/ashby_20261021_v2/presentation_script_8min.md), [Q&A](../submission/ashby_20261021_v2/qa_4min.md), [submission checklist](../submission/ashby_20261021_v2/submission_checklist.md).

The deck uses actual microscopy, existing measured annotation/coordinate examples, editable evidence tables/charts, and references. It includes completed S2/v2 outcomes after validation, preserves the rejected v1 findings and distinguishes future S3/S4 work. The unavailable bundled artifact runtime required native Keynote authoring/export; no substitute presentation library or new scientific model was installed. The rendering/export checks are recorded with the package. A timed script still requires human rehearsal.

The inspected welcome PDF specifies **Wednesday, October 21, 2026**, an abstract/availability form and a standalone PPT or PDF with ≤20 main slides, plus eight minutes and four minutes of Q&A for live presentations. The exact submission hour/timezone, organizer upload URL, team roster/affiliations and live availability remain unavailable. The user requested proceeding without those details. They remain checklist items; no information is invented and nothing was uploaded or sent to organizers.

## S2: completed CPU experiment, negative primary calibration result

Slurm **23067396 completed `0:0` in 19 seconds**: 2 CPUs, 4 GB, ten-minute cap, account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`. Its exact source snapshot and acquisition/embedding identities are verified. It uses existing normalized CONCH v1 image/text embeddings only.

Before contamination, mean pooling was selected from existing clean low/high evidence: **35/48 training correct** (low 22/24, high 13/24), **12/16 calibration correct** (low 8/8, high 4/8). Its limited high-grade sensitivity makes this an engineering stress endpoint, not clinical grading. Top-1% and top-5% calibration clean low-grade supports are only **2/8 and 3/8 correctly classified**; these are their new-error denominators.

The run has **760 records: 632 positive mixtures and 128 repeated zero references**, 32 distinct low-grade hosts, 37 donor slides and 55 source slides in their union. **760/760 exact oracle recoveries** pass. Main GP4/5 donors use verified native pattern fractions, unique four-connected tiles and nested dose prefixes at 0/0.5/1/2/5/10% requested foreign/original-host tile counts. Native coordinates, translations, realized doses and all scores are retained. Slide grades are never per-tile ground truth.

Primary mean pooling has **0/8 new calibration low-to-high errors at every dose**, and **1/22 training errors at 10%**. The 0/8 per-dose Wilson 95% interval extends to 32.4%, so this does not establish immunity. At 10%, secondary top-1% and top-5% have **2/2 and 3/3** new calibration errors. Same-grade GP3 top-5% control also produces **1/3** new errors and one initial-error reversal at 10%; these effects do not establish clinical Grade Group upgrading or high-grade-specific instability.

Controls include same-grade GP3/no-GP4/5, GP4-positive/no-GP5 (GP3 allowed), and GP5-positive (GP3/4 allowed). Eight calibration GP5 10% trials lack connected capacity and remain unavailable, not negative. Genuine native annotation-defined GP4/5 exclusions change mean predictions on six training and two calibration slides. A fragment is farther from host than its original donor context in 23/24 training and 8/8 calibration 10% diagnostic comparisons, but context-size/composition confounding and overlapping distributions prevent a calibrated foreignness claim. No tissue is removed. [Complete S2 report and raw evidence](panda_s2_results_v1.md).

## Detector v2: ranked review does not meet utility targets

Slurm **23067454 completed `0:0` in 23 seconds**, with the same bounded CPU resource request. It analyzes saved v1 component measurements; no old WSI segmentation, embedding, S1 draw, individual counterfactual job or final preflight was repeated.

Five fixed rank strategies separate visual anomaly, absolute prediction-margin influence and physical geometry. Clean-training-only normalization, thresholds and caps select the primary; no test input or annotation/injection/donor-identity feature enters the detector. Known calibration is **iterative development**, not fresh independent validation.

The primary combined rank improves training fragment hits **5/120 v1 to 22/120 v2**, but fails the preregistered ≥20% recall and ≥25% recovery goals even on training (18.33% and 6/38). Calibration remains **0/40 hits and 0/8 recoveries**, with **1/24 clean alerts** and one native-cancer component flagged. Therefore it provides **no meaningfully validated useful improvement** over v1.

Unbudgeted top-one visual/relevance ranking hits **21/40 fragments**, but alerts on **24/24 clean slides**, flags **14 native-cancer components** and hypothetically damages **2/20** initially correct clean predictions. It exceeds both confirmed review-burden goals. Matched random controls, forced singleton matches, native-cancer safety and host-level uncertainty are reported rather than suppressed.

The v1 failure audit locates all five visual-pass calibration mixtures on **one host at five nested doses**. Four have zero signed influence; the last has influence 0.000558, below 0.01. All 40 mixtures place donor-bearing components beyond the observed native right edge. Five of 607 injected tiles are unmapped; no component co-maps donor and native tiles. These are tile-membership and RGB-topology proxies, not proven pixel purity. Isolation can still benefit from artificial placement even when absolute position is excluded from ranking. [Complete v2 report](panda_review_v2_results.md).

## Final test and remaining gates

**All 24 test slides remain unscored and the detector final test is scientifically blocked.** The rejected frozen v1 protocol, thresholds, failed-job evidence, 10,988-file preflight receipt and prepared command are unchanged. Preflight 23066843 was not repeated. No useful review operating point was found, so no replacement final job was prepared or submitted. The negative S2 primary outcome is valid bounded scientific evidence, not a failed detector gate or a reason to switch to a favorable secondary scorer. Any future confirmatory S2 or detector evaluation needs a separately versioned scientific scope/freeze, exact resource/command review and explicit user authorization, while preserving the planned single independent test. Do not bypass v1 or revise parameters using test outcomes.

Full local regression: **204 tests passed**, warnings treated as errors. Slurm wrappers pass Bash syntax checks. Scientific results are distinct from temporary software fixtures. Existing TCGA results, all PANDA artifacts and current main remain unchanged. The historical PathGen-CLIP branch was reviewed read-only; no model or checkpoint was imported. [Future S3/S4 gates](../docs/panda_research_tracks_after_submission.md).

No additional job, GPU allocation, model, dataset download or access authorization is needed to use the prepared package. Organizers' submission metadata and actual upload remain a human handoff. Independent patient identity, clinical validity, realistic-contaminant generalization and validated physical boundaries remain unknown.
