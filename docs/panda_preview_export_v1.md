# Bounded saved-PNG galleries v1

This version adds image examples to the completed original-training dependence
reports without changing their saved predictions, component memberships, context
gates or tissue decisions. It consumes **72 training slides /389 RGB components**
from the sealed report export. No fresh60, calibration or original test artifact
is evaluated. Every original report/output is preserved.

## Fixed display contract

For every component, select up to **four component tiles** and **four outside tiles**.
Sort each available index set by recorded physical x, then y, then original index;
choose equally spaced order positions including both endpoints (integer floor).
This selection reads no labels, annotation fractions, scores, influence, image
features or decision-change outcomes. All 389 components remain in original order.
No detector ranking or foreignness policy is introduced.

The galleries contain separate saved tile examples. They are **not spatial
reconstructions, verified physical piece boundaries, whole-slide coverage, or a
new sample for calculating NN5 context scores**. Outside previews can be unmapped
in the RGB proxy; those assignments stay unknown and are labeled as such. Empty
outside context gets text and no invented image. Decision dependence and numeric
abstention remain visible together. Review/foreignness stay null; tissue action
none. Native annotation controls remain separate from reviewer JSON/HTML.

PNG bytes are copied unchanged into a new remote `tiles/` directory, deduplicated
within each slide. No contrast/color edit, crop, synthetic pixels or normalization
is performed. HTML may display a smaller image; physical captions use the recorded
field and coordinates, not screen size or an assumed exactly-112-µm field. PNG
format, RGB mode, dimensions and checksums must match the verified encoding inputs.
Each PNG is bounded at 1 MiB and at most 512x512 recorded pixels before decoding.

The embedding completion is hash-bound to the original verification receipt;
it binds `tiles.csv`, metadata and all source PNG hashes. Only training paths are
opened. The CSV order and count, unique IDs, original membership/footprint and
physical geometry are checked. Source/destination path escape, symlinks leaving
the slide directory, missing/corrupt images, changed metadata or byte overruns stop
the run and preserve partial output. Sources and all output hashes are rechecked
before sealing. No NPZ, WSI, mask, model checkpoint or network download is opened.

## Scope, freeze and artifacts

Protocol `configs/panda_preview_export_v1.json`, SHA256:
`5024779111434c188f6a2d486acff1203db4969f337c1875dfb9481bfd61859c`.

One bounded CPU Slurm job: account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`,
**2 CPUs, 4 GB, five-minute cap, zero GPUs** (at most 0.167 allocated CPU-hours).
At most **3,112 gallery tile references** and **512 MiB copied PNG bytes**. These
are display references, not distinct slides, patients or independent observations.
The latest user “next” advances the explicitly proposed existing-tile preview
integration; resource values are agent-selected within that new scope. Exact
pushed source and command are shown before submission. No consumed job approval,
retry, duplicate, acquisition, new inference, fitting or final-test execution.

Verified output, created by job 23102636:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review/dependence-previews-v1`

Expected: a new index, 72 reviewer JSON/HTML reports, selected unchanged PNG assets,
72 registry slide checkpoints containing source/asset receipts and separate old
controls, aggregate summary, event chain and seal. The summary binds hashes of
all copied PNGs and rendered files and carries original dependence counts unchanged.
All images and detailed artifacts remain on Delta; none are copied to the Mac.

Thirteen new artificial colored-PNG tests pass, including a 72-slide software
fixture. An initial fixture reference-count assertion was corrected (576 rather
than 1,152); no production logic changed for that correction. All **363 tests pass** with warnings as errors (33.36s) before source
freeze/submission. Static HTML checks validate local asset
links and captions. Browser visual preview remains unverified under the previously
observed local-file URL policy; no retry/workaround is planned. Fixtures are never
scientific evidence or a clinical interpretation of the tissue images.

Metadata-only preflight:

```sh
python scripts/panda_preview_export.py --config configs/panda_preview_export_v1.json \
  --config-sha256 5024779111434c188f6a2d486acff1203db4969f337c1875dfb9481bfd61859c
```

`--check-inputs` adds remote metadata/destination checks without decoding images.
Execution requires the bounded CPU wrapper and `--execute`. Exact staging and
observed output/byte counts will be appended after verification, not inferred.


## Verified staging and exact submission

Source `ec5a71dde4b566393ddfa4b53b5e1b6a8eec3d6d` was pushed and separately staged read-only at:

`/u/mhoda/floater-finder/releases/panda-preview-export-v1-20261021T174522Z/source`

All 267 source files and six input receipts verified; own queue empty and intended
output absent before submission. Archive SHA256 `643bdb1fa64cd9845905f567b3e2a80ee13402f79652c06ef0d1973564dba1d3`;
source-manifest SHA256 `44990c614f128132714a4b9f7f315f669f97d15447769405e8dde553225fade1`.

Submitted once as **23102636** with the exact command:

```sh
sbatch --parsable /u/mhoda/floater-finder/releases/panda-preview-export-v1-20261021T174522Z/source/scripts/slurm/panda_preview_export.sbatch /u/mhoda/floater-finder/releases/panda-preview-export-v1-20261021T174522Z/source /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z 5024779111434c188f6a2d486acff1203db4969f337c1875dfb9481bfd61859c /work/nvme/bfqi/mhoda/floater-finder/panda-review/dependence-previews-v1 ec5a71dde4b566393ddfa4b53b5e1b6a8eec3d6d
```

Authorization receipt SHA256 `604b7b9931374f7555f7417c0d88cd4274bae8300461d33757fb43d582b877bc`.
The latest user “next” advances this bounded gallery integration; resource values
are agent-selected within that scope, not expressly user-selected. No consumed
approval reused. Job **23102636 completed 0:0 in 23 seconds**. Source PNGs/metadata and all
1,783 output files verify: 1,638 PNG copies /2,605 references, 101,466,949 bytes,
73 checkpoints /76 events. [Observed counts, preservation checks and limitations](../reports/panda_preview_export_results_v1.md).
This bounded scope is complete; no additional job or retry was submitted.
