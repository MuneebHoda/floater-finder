# Pixel benchmark: corrected original source paths

The October 22 inspection found a configuration error behind CPU failure
23109667. Three original profile embeddings were deliberately reused during the
120-slide encoding job. Their receipts pin the metadata in the original profile
directories, while the first 10k source manifest pointed to new cohort copies.

Read-only comparison on Delta verified that only `selection_manifest` and
`selection_manifest_sha256` differ between those copies. The original metadata
and CSV hashes exactly match the embedding receipts. The existing preparation
report already records the authoritative input directories:
[120-slide reuse provenance](../reports/panda_full_cohort_gpu_preparation_20261020.json).

The correction is configuration only:

- [Sources v2](../configs/panda_gpu_program_v2/sources.csv) changes the tile CSV
  and metadata paths for exactly the three reused profile slides. All 57 IDs,
  roles, folds, image/mask paths, grade labels and original-training membership
  are unchanged. No source is replaced.
- [Protocol v2](../configs/panda_gpu_program_v2/protocol.json) preserves the
  original pair schedule, seed, 10,000-candidate design, geometry, model,
  preprocessing, CPU/GPU resource ceilings and every existing source-code pin.
  It adds pins for the corrected manifest, historical reuse report and CPU
  launcher. It uses a new output path, not the failed v1 directory.
- [CPU launcher v2](../scripts/slurm/panda_pixel_program_prepare_v2.sbatch) uses
  the same runtime entry point and four-argument interface, selecting protocol
  v2. No provenance guard, scientific algorithm or encoder implementation changes.

Protocol SHA256:
`7c78aabd40490dbe8f72426700ed65e2b4ad599b4a5fe2628279e17eb0a9a93b`.
Sources SHA256:
`e8edbda2cb46e05362c536f7d27e681c2f1fe4e3d1b9df48b2d10db05db54896`.

A bounded metadata-only recheck passes for **57/57** corrected source paths:
metadata hash, CSV hash, representative sampling, no mask-selected clean tiles
and original-training split. It does not establish WSI integrity, per-PNG byte
identity, native-mask agreement, eligibility, rendered counts or GPU results.
Those checks remain in the unchanged scheduled preparation/encoding code.
The two new regression tests check exact three-row correction, scientific and
historical pin preservation, source-fold identity and rejection of a modified
source manifest. They use metadata only and are not scientific results.

Validation: **455 tests pass** with warnings treated as errors (30.56 seconds).
The v2 Slurm script passes `bash -n`, all72 configured source-file hashes match,
and whitespace checks pass. No dependency or scientific runtime change is needed.

## Execution remains pending

No replacement CPU or GPU job was submitted as part of the correction/publication
task. Original CPU23109667 failure and GPU23109849 cancellation remain recorded;
all v1 configuration, scripts and output directories are preserved. The new
intended output is:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-program-10k-v2-prepared`

Before execution, stage the final committed code to a separate Delta source
snapshot and verify its manifest. Set `verified_project` to that verified path;
it is deliberately not an invented release location. Then the bounded CPU
command is:

```sh
sbatch --parsable --exclude=cn018 \
  "$verified_project/scripts/slurm/panda_pixel_program_prepare_v2.sbatch" \
  "$verified_project" \
  /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z \
  7c78aabd40490dbe8f72426700ed65e2b4ad599b4a5fe2628279e17eb0a9a93b \
  /work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-program-10k-v2-prepared
```

Resources remain `bfqi-delta-cpu` account/QoS, `cpu` partition, four CPUs, 16 GiB,
30 minutes and no GPU. Recheck current queue and output absence before submitting;
never overwrite a previous run or blindly retry a failure. Review the actual CPU
feasibility receipt and billing before freezing any GPU range. The v1 dependent
GPU resolver hardcodes the v1 protocol/output and must not be reused for v2.
No new GPU execution or detector validity is implied by this path correction.

[Completed 96-image results and preserved 10k failure](../reports/panda_pixel_results_20261022.md).
