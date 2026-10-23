# Real PANDA CPU tiling and available-cohort results

CPU job **23050425** completed `0:0` on `cn137` in **9 seconds**, using the exact approved two-CPU, 4 GB, ten-minute request. It used pushed commit `1598f9b08e625112be7d5bf91a25f82335c962f9` from the verified read-only snapshot. No GPU inference, additional download, duplicate acquisition, branch merge or changes to main/TCGA results occurred.

## Observed extraction

| Biopsy | Tiles | Mask | Tiles with GP4 > 0 | Tiles with GP5 > 0 | Either > 0 |
| --- | ---: | --- | ---: | ---: | ---: |
| Benign `afe7eb15c8438861ca43f2b20dccf260` | 32 | Available | 0 | 0 | 0 |
| GG1 `55d91c32710982de78a975ed0f45395c` | 32 | Unavailable | Unknown | Unknown | Unknown |
| ISUP 4 donor `dd1110c6430e3b1ac732be548a089886` | 32 | Available | **0** | **0** | **0** |

All three CSVs passed unique-ID/count checks, finite spatial coordinates and areas, exact native-pixel/grid alignment, in-bounds footprints and expected PNG shape/mode. For annotated masks, all six per-tile fractions are finite, within [0,1] and sum to one. The absent GG1 mask remains unknown. Manifest, metadata and every PNG hash match the job's saved report. Source/config identities match the pushed snapshot. Retrieved CSVs/metadata were independently hash-checked locally and the positive-tile counts independently recomputed.

Measured scale is .4861876369654638 microns/pixel in both axes. The fixed native footprint is 230×230 pixels, realizing 111.82315650205668 microns per side and **.012504418330083459 mm² per tile**. The nominal 112-micron request was not substituted for the realized area. Tile area is occupied footprint area, not annotated cancer area.

**Technical extraction passed. Cancer-positive donor capture failed (0/32).** This is a row-major engineering subset, not a whole-slide estimate of cancer burden or a cancer-model result. No cancer detector was trained or scored, and no accepted S1 donor is claimed.

Remote outputs: `/work/nvme/bfqi/mhoda/floater-finder/panda-smoke/cpu-1598f9b-20261020T040441Z`. Small retrieved artifacts are under ignored `results/panda/cpu_smoke_23050425/`; raw WSIs and tile PNGs remain on Delta. [Submission](ncsa_panda_cpu_submission_23050425.json), [verified counts and geometry](panda_cpu_smoke_23050425.json).

## Acquisition inspection and verified cohort

Acquisition **23030528** remained pending for Priority when inspected. `/work/nvme/bfqi/mhoda/panda/logs/cohort-23030528.log` did not exist. The submitted batch script references original `train.csv` and invokes `/work/nvme/bfqi/mhoda/panda/collect_annotated.py`; that Python file was absent. No larger manifest was found/generated in the bounded checks. The acquisition and its associated files were left untouched. [Safe inspection record](ncsa_panda_acquisition_inspection_23030528.json).

The newly authorized manifest was created at the intended path:

`/work/nvme/bfqi/mhoda/panda/annotated_cohort.csv`

It is explicitly a **partial, three-row manifest**, not a 60-slide cohort. Selection used the original 10,616-row PANDA metadata and only actually present WSIs with validated TIFF headers/calibration and aligned available masks. There were no rejected eligible files, and no additional eligible WSIs existed in the inspected `train_images/` directory.

| Group | Available and selected | With mask | Train | Calibration | Test | Shortfall from 20 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Benign, ISUP 0 | 1 | 1 | 1 | 0 | 0 | 19 |
| GG1, ISUP 1 | 1 | 0 | 1 | 0 | 0 | 19 |
| High grade, ISUP 4–5 | 1 | 1 | 1 | 0 | 0 | 19 |
| Total | **3** | **2** | **3** | **0** | **0** | **57** |

Seed: **20261020**. Within each group, valid-mask cases rank first, followed by a seeded SHA-256 tie order; select at most 20. An independently salted seeded order assigns the first 12 to training, next four to calibration and last four to test when available. This deterministic rule was checked with an artificial 60-case software fixture before use; no artificial ID entered the manifest. With only one available case per group, all three go to training. No patient IDs are present in PANDA's supplied metadata, so biopsy IDs were not substituted as patient identities and patient-level separation cannot be verified. There is no held-out calibration/test cohort yet.

The original 12-row pilot was preserved, SHA-256 `91713d4f430e53c74e8dee9a7c8aeda8e25781302d05c74d020952a239564c7e`. The new manifest's SHA-256 is `9042c167c13a18da999e29a130dffb6495e32d102ade48fb79c28e53a69d00b7`. Its adjacent `annotated_cohort.csv.selection_provenance.json` records seed, actual counts, file/header inventory, original metadata hash and exact recipe hash. [Selection facts](panda_cohort_selection_20261020.json), [manifest copy](manifests/panda_available_cohort_20261020.csv), [exact recipe](provenance/panda_cohort_selection_20261020.py).

The three inputs are individually valid for tiling; they do **not** form the requested balanced study cohort. Embedding remains unrun/unapproved, and donor cancer capture is unresolved. For future larger-cohort ingestion, add an explicit manifest-path interface or a separate data view rather than replacing `pilot.csv`; also honor the new split metadata. The current smoke runner still deliberately caps three slides, and the adapter's membership file is fixed to `pilot.csv` (maximum 100 rows). Original slide grades must remain separate from per-tile mask labels.

## Proposed next extraction: separate donor-only mask guidance

Implement and review a **new mode**, then obtain approval for a separate bounded CPU job; no such mode/job has run yet. Keep the current run and exact source snapshot unchanged.

1. Use only the existing high-grade donor and its verified Radboud mask. Stream level-1 channel-0 mask blocks, each at most 512×512 pixels, locating GP4/5-positive cells; never load the native WSI plane.
2. Map candidate positive cells to the same native 230-pixel global tile grid. Rank deduplicated candidates by coarse positive coverage with deterministic tie ordering, bounded to 128 candidates and at most eight retained tiles.
3. Read each retained native mask patch without interpolation and require a nonzero measured GP4/5 fraction. Extract the aligned image patch using the same physical geometry and canonical CONCH handoff. Save explicit `mask_guided_donor_engineering` selection provenance and all candidate exclusions.
4. Use these tiles only to prepare a cancer-positive engineering donor. Keep whole-biopsy cancer-model evaluation on separate complete or outcome-blind representative sampling; never mix mask-enriched donor outputs into clean performance or alert-rate estimates. The current first-32 sampler is itself an engineering subset, not unbiased evaluation.

Proposed bounds: one existing donor, no downloads, no GPU, two CPUs, 4 GB and ten minutes. A new implementation/source identity and approval would precede submission. Acceptance remains an observed positive donor tile plus valid spatial metadata; no synthetic count or predicted success substitutes for that check.
