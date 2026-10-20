# Expanded CONCH v1 pilot protocol

The study design is **frozen after passing technical preflight**. The settings and exact patient/input records are in [the protocol configuration](../configs/ncsa_expanded_pilot_protocol.json); the [freeze record](../reports/conch_pilot_protocol_freeze_20261019.json) pins configuration and source hashes. This is a technical feasibility study of synthetic embedding contamination. It cannot establish clinical floater sensitivity or a population false-positive rate. The cohort runner and final numerical calibration remain separate later gates.

## Patients and sampling

Use the two existing development patients and eight newly acquired development patients, with eight fresh evaluation patients. Never use the retired two-patient smoke evaluation to select settings. Patients are disjoint across development and evaluation. New TCGA source-site prefixes are disjoint; normalized institutions, clinical report linkage and native floater annotations remain unverified.

Each slide must provide four disjoint four-neighbor-connected windows of exactly 96 physical-grid cells, 384 tiles total. The initial 128-tile-window candidate failed technical capacity on development patient `TCGA-HC-7230` in job `23005189`, after all 18 slide checksums/headers passed. The revised size passed preflight uniformly for every patient, preserves the original patients and spacing, and was chosen before any new embedding or held-out outcome. The first seed is nearest the centroid of the largest eligible component. Subsequent seeds maximize distance to all previously selected tiles, with lexicographic coordinate tie-breaking; breadth-first growth follows the fixed neighbor order. Every tile in a later window must be at least 1,000 microns from every earlier window. Candidate coordinates come only from the shared `coords` dataset; CONCH v1.5 feature values are never used. Mapping source tissue-region centers to physical cells is a tissue-mask approximation, not pathologist-reviewed tissue selection.

Use measured, positive, isotropic OpenSlide MPP, a 256-micron field, and the existing fractional level-zero crop resized to 512 RGB pixels with Pillow 12.3.0. Preserve measured scanner metadata. No ICC conversion or stain normalization is added. Insufficient capacity, corruption, or header/coordinate mismatch stops the technical gate; preserve all patient failures and do not replace patients or silently lower the sample count.

Preflight checks all 18 slide checksums, headers and coordinate geometries through Slurm. Pixel extraction is validated on two outcome-blind, predeclared new development patients, `TCGA-G9-6379` and `TCGA-XF-A9SW`. Evaluation performance and evaluation pixels are not inspected during this stage. Bounded development contact sheets are technical image QC, not pathology review.

## Model and fixed scoring

Use only the already verified original CONCH v1 checkpoint, pinned source revision, projected normalized 512-dimensional vectors, and the unchanged four-prompt ensemble per organ embedded in the configuration. New artifacts must use the patched runtime and new sampling provenance; do not mix earlier 128-tile artifacts into this study. Re-encode the two retained development patients with the same broader sampling as the new patients.

Fix organ/visual weight to 0.5, spatial exclusion to 1 mm, smoothing to 0.1 mm and chunk size to 256. Report organ-only, visual-only and combined variants. The protocol freezes these choices; it does not claim an improved detector.

## Development-only threshold selection

Before any held-out scoring, perform ten leave-one-development-patient-out folds. Fit score normalization and each candidate quantile threshold only on the other nine original, unmodified development patients. Score the omitted development patient. Do not use synthetic mixtures to select a setting, so no donor participates in selection; if a future protocol uses synthetic development host/donor outcomes, both patients must be excluded from that fold's calibration.

Candidate quantiles are 0.9, 0.95, 0.975, 0.99 and 0.995. Choose the smallest candidate for which **every omitted development patient and every variant** has original-host removal at most 1%. For 384 tiles this permits at most three removed original-host tiles. If no candidate passes, stop before evaluation and report that no feasible setting was found. Do not relax the budget after viewing held-out results.

Fit final normalization and thresholds on all ten development patients using the selected quantile. Save patient IDs, exact thresholds, raw scores and hashes; freeze this derived calibration before held-out artifacts are scored. Leave-one-out results guide selection and are not independent validation of the chosen quantile. Original host tissue is not confirmed floater-free; the removal budget is not a clinical false-positive guarantee.

## Held-out evaluation and denominators

After the validated cohort runner and final calibration gates pass, evaluate all 32 directed cross-organ host/donor pairs from eight held-out patients. Use five nonzero contamination levels (0.5, 1, 2, 5 and 10%) and seeds 0–4, giving 800 mixed trials. Record the existing ceiling rule, requested and realized counts/percentages, donor connected-fragment indices and translation. Every selected donor must have a 96-tile connected component, exceeding the maximum 39-tile injection for a 384-tile host.

Evaluate each of the eight original held-out hosts once as its zero-contamination control. There are **808 total trials and 2,424 variant rows**, including 24 variant-specific clean-host controls. Repeated pairs, levels and seeds are not additional independent patients. Report per-host and per-organ summaries alongside trial-level data; do not count repeated clean controls as independent observations.

Every trial requires oracle restoration before detector metrics. Any oracle failure stops the experiment as a pipeline defect. Save no-filter, oracle and matched-count random-removal controls, raw class/anomaly scores, masks, flags, exact configuration and software/model hashes. Report all exclusions/failures and metric denominators; undefined metrics remain null.

No expanded encoding or detector evaluation is submitted by this protocol-preparation step. The cohort runner, development selection and final-calibration freeze remain required before held-out scoring. At most one scheduled GPU may run at once; resource caps and verified allocations remain in the machine-readable configuration.

## Technical validation evidence

CPU job `23005299` completed `0:0` on `cn137` in 2 minutes 34 seconds. All 18 slide checksums, measured headers, coordinate sources and four-window selections passed. All 768 tiles from the two predeclared development slides decoded and resampled successfully. Independent checks verified all selected cells are unique, in bounds, in the recorded candidate sets, connected within each window and separated by at least 1,024 microns across windows. Two contact sheets were visually checked for technical extraction; they include white background areas, dark edge markings and red areas. No tiles or patients were discarded based on this review, and no pathology labels were assigned.

All 45 retrieved small-artifact hashes match Delta. Full raw tile PNGs remain on Delta. [Observed technical results](../reports/conch_pilot_preflight_results.md), [final scheduled report](../reports/ncsa_pilot_preflight_23005299.json), [independent verification](../reports/ncsa_pilot_preflight_verification_20261019.json). No new image/text embeddings or held-out performance outputs were created.
