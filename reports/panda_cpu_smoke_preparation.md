# Real PANDA CPU smoke: prepared, awaiting approval

Commit `1598f9b08e625112be7d5bf91a25f82335c962f9` is staged separately on Delta. All 172 source files match the pushed commit archive and are read-only. Existing main, TCGA outputs and the original CONCH runtime are preserved.

The new isolated CPU runtime imports the pinned NumPy 2.0.2, Pillow 12.3.0, PyYAML 6.0.2, OpenSlide Python 1.4.6/binary 4.0.1.2 and tifffile 2025.5.10. The original runtime lacked tifffile and inherited NumPy 2.2.6; only the new runtime received overrides. Dependency wheels were installed offline on Delta; no dataset/model downloads or GPU imports/inference occurred.

All three images and both available masks passed the exact pushed reader's header, pyramid, orientation and physical-scale checks. Five one-pixel decoder probes passed (one per existing TIFF), each bounded to a native 512×512 compressed tile; no slide plane or training array was decoded. All measured MPP values are 0.4861876369654638 in both axes. The requested 112-micron field becomes a 230-pixel native footprint, realizing 111.82315650205668 microns per side. Missing GG1 mask labels remain unknown.

Evidence: [reader/runtime preflight](ncsa_panda_reader_preflight_1598f9b_20261020.json), [source hashes](ncsa_panda_source_manifest_1598f9b_20261020.json), [preparation and test-only scheduler record](ncsa_panda_cpu_preparation_1598f9b_20261020.json).

## Exact proposed submission from the Mac

```sh
ssh -o BatchMode=yes ncsa-floater 'sbatch --parsable \
  /u/mhoda/floater-finder/releases/panda-1598f9b-20261020T040441Z/source/scripts/slurm/panda_tile_smoke.sbatch \
  /u/mhoda/floater-finder/releases/panda-1598f9b-20261020T040441Z/source \
  /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z \
  /work/nvme/bfqi/mhoda/floater-finder/panda-smoke/cpu-1598f9b-20261020T040441Z'
```

The command above has **not** been executed. The scheduler accepted the same script/arguments with `--test-only`; that command did not submit a job. Actual submission awaits the explicit approval requested in the user's step 5.

Allocation/account and QoS: `bfqi-delta-cpu`. Partition: `cpu-interactive`. One node/task, two CPUs, 4 GB, ten minutes, no GPU. The existing script requests a stdout log at `/work/nvme/bfqi/mhoda/floater-panda-tiles-%j.out`. Runtime and output paths are shown literally in the command; the fresh output leaf does not yet exist.

## Expected outputs and acceptance

For each of `afe7eb15c8438861ca43f2b20dccf260`, `55d91c32710982de78a975ed0f45395c` and `dd1110c6430e3b1ac732be548a089886`, the output directory should contain `<image_id>/tiles.csv`, `<image_id>/metadata.json` and up to 32 PNGs at 224×224 pixels. A successful job also writes top-level `tiling.json` with config/source and PNG/manifest/metadata hashes. No embeddings or model scores are produced.

After completion, validate all three CSV counts, IDs/coordinates/areas, finite fractions summing to one for annotated masks, absent fractions for GG1, actual image/metadata provenance, and file hashes. Report separately the donor counts with nonzero Gleason 4, nonzero Gleason 5, and either fraction positive, with total donor tiles as denominator. Acceptance is not claimed until at least one such positive donor tile is observed.

The frozen sampler stops at the first 32 RGB-tissue-positive cells; it can miss the small annotated cancer focus and is not unbiased whole-slide evaluation. If it misses, preserve this run and propose a separate mask-guided **donor-only engineering extraction** with its selection rule/area/provenance explicitly tagged. Clean model evaluation must use separate complete or outcome-blind representative biopsy sampling, never mask-enriched donor tiles. No mask-guided mode or additional job is authorized by this preparation alone.

## Cohort acquisition and future ingestion

Acquisition `23030528` remains pending for Priority at the last observation; no cancellation, dependency change or duplicate was submitted. Its working directory is `/u/mhoda`. The checked personal PANDA root contains `train.csv` (10,616 rows) and `pilot.csv` (12 rows); the actual new 60-slide manifest has not been located within the bounded checked directories and its path has been requested.

A local software fixture verified that the current reader can select row 60 from a 60-row Radboud `pilot.csv`; its membership guard allows at most 100 rows. This does not validate the unavailable actual manifest. Eventually use an explicit manifest-path adapter or a separate data-view root exposing the approved 60-row CSV as `pilot.csv`, without overwriting the current pilot. Original `train.csv` labels, IDs, uniqueness and provider semantics must be cross-checked first. The current smoke runner deliberately refuses more than three slides; a separate bounded cohort runner/scope would be needed for sixty. Karolinska masks are not supported by the Radboud adapter.
