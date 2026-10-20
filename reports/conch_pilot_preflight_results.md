# Expanded-pilot technical validation

This stage checks raw inputs and spatial sampling through CPU Slurm jobs. It creates no embeddings, loads no model, uses no GPU and makes no scientific performance claim. All previous outputs and failed candidates remain preserved.

## Initial candidate: 4 × 128 tiles

Job `23005189` ran on `cn137` for 1 minute 37 seconds and exited `2:0`, correctly failing the sampling gate. All **18/18 raw slide checksums, measured isotropic MPP values and coordinate-header/identity checks passed**. Only the shared coordinate datasets were read; no CONCH v1.5 feature values were used.

Seventeen patients supported the requested four disjoint 128-tile windows with at least 1 mm between windows. Development patient `TCGA-HC-7230` has 770 in-bounds physical candidate cells but cannot provide the fourth connected 128-tile window under this deterministic selection and spacing rule. This is a capacity failure under the sampler, not evidence of corrupt input or a proof that no other geometric arrangement could fit. No patients were excluded or replaced. Pixel QC was skipped because the cohort sampling gate failed.

Evidence: [complete failed-candidate report](ncsa_pilot_preflight_23005189.json), [log](ncsa_pilot_preflight_job_23005189.log), [immutable-source submission](ncsa_pilot_preflight_submission_20261019T052625Z.json). The exact candidate configuration remains in its remote immutable release; the local protocol records the subsequent amendment.

## Revised candidate: 4 × 96 tiles

Before any new embeddings or held-out outcomes, reduced the window size uniformly to 96 tiles for every patient, retaining all 18 patients, four windows and the 1 mm gap. This requests 384 tiles per patient and remains within the original proposal's four windows of at most 128. Prompt, scoring, threshold-selection and patient-split policies are unchanged.

Job **`23005299` completed `0:0` on `cn137` in 2 minutes 34 seconds**, with two CPUs, 4 GB and a 15-minute bound under `bfqi-delta-cpu`/`cpu-interactive`. All **18/18** checksums, raw headers, coordinate sources and four-window selections passed. The two predeclared development patients each exported **384 tiles**, 768 total, with opaque bounded reads and matching physical geometry. No evaluation pixels were decoded for contact-sheet review.

Retrieved 45 small artifacts (16,995,784 bytes), including coordinate arrays and development contact sheets; every hash matches Delta. Independently checked all 6,912 selected physical cells: unique within each patient, members of the recorded candidate set, in bounds, connected within each of four windows, and separated across windows by at least **1,024 microns**. The two saved tile manifests match those selections. Visual technical QC showed decoded stained imagery with white background areas, dark edge markings and red areas; no native floater/pathology review or outcome-based exclusion occurred. Full raw tile PNGs remain on Delta, and the user's queue was empty after the job.

Evidence: [final scheduled report](ncsa_pilot_preflight_23005299.json), [accounting, hashes and independent verification](ncsa_pilot_preflight_verification_20261019.json), [submission/source snapshot](ncsa_pilot_preflight_submission_20261019T052935Z.json), [log](ncsa_pilot_preflight_job_23005299.log). The revised [study design is frozen](conch_pilot_protocol_freeze_20261019.json). The failed first candidate remains separate and is not presented as a successful run.

The [protocol](../docs/expanded_pilot_protocol.md) fixes a development-only leave-one-patient-out selection rule and a 1% original-host removal budget. The cohort runner and final numerical calibration remain later gates; no held-out scoring is authorized by a passing technical preflight alone.

Software validation: **97 tests passed with warnings as errors**, including deterministic separated sampling, insufficient-capacity rejection, raw-pixel extraction through the new sampler, input corruption/symlink rejection, login-node guards and patient/control denominators. Shell syntax and diff checks passed. No GPU, model download, new embedding or held-out detector experiment was run in this stage.
