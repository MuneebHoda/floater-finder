# PANDA pipeline implementation status

Deadline: October 21, 2026. Scope: CONCH-only S1 engineering pipeline; no cancer-detector training, clinical validity claim or new experiment results.

## Isolation and preservation

Execution is on the user's local Mac (`Darwin`). New branch `feature/panda-tiling` starts at current `main`, `bdb13e5`, which is three commits ahead of fetched `origin/main`. Its separate worktree is `/Users/muneebhoda/Documents/Masters - Fall 2026/Ashby Hackathon-panda-tiling`. The original `Ashby Hackathon` checkout and its uncommitted Phase 1 work remain untouched; the nine Phase 1 files were copied forward for integration. Nothing was merged, committed or pushed for this request. Frozen TCGA modules, protocols, existing scripts and scientific results remain preserved.

## User-verified Delta inputs

The following facts were supplied by the user, not independently remeasured by this implementation. Root: `/work/nvme/bfqi/mhoda/panda/`; original labels in `train.csv`, twelve Radboud biopsies in `pilot.csv`, TIFFs in `train_images/`, masks in `train_label_masks/`.

| Image ID | Slide-level label | Mask |
| --- | --- | --- |
| `afe7eb15c8438861ca43f2b20dccf260` | ISUP 0, benign | Available |
| `55d91c32710982de78a975ed0f45395c` | ISUP 1 / GG1 | Unavailable |
| `dd1110c6430e3b1ac732be548a089886` | ISUP 4, Gleason 4+4 | Available |

The user verified three pyramid levels (1, 4, 16), matching image/mask dimensions, and Radboud channel-0 labels: 0 background, 1 stroma, 2 benign epithelium, 3/4/5 Gleason patterns. Reported TIFF-resolution-derived scale is approximately .486 microns per level-0 pixel. The donor's reported 5,501 pattern-4 pixels at level 1 correspond to approximately .021 mm²; this is a supplied mask observation, not a detector result or a claim that the bounded sampler will include that focus. Actual image/mask codec support and header values still need to pass the adapter on Delta. Patient identity/grouping and access/license details remain unverified here.

## Implemented

| Component | Behavior / boundary |
| --- | --- |
| `src/floater_finder/panda.py` | Separate adapter; existing TCGA tiler is unchanged. Resolves only a selected pilot image, cross-checks original labels/provider, inspects TIFF headers/pyramids, checks image/mask dimensions/orientation/downsamples, and requires physical TIFF resolution units. |
| Spatial tiling | Default requested field 112 µm; configurable within bounds. Uses a fixed integer level-0 footprint, records its realized X/Y field, emits level-0 and physical-micron origins, grid IDs and area in mm². Export size defaults to 224px. At the reported .486 scale, 230 native pixels would realize 111.78 µm; actual runs use their measured tags. |
| Bounded image I/O | Coarsest-level RGB tissue screening; chooses an appropriate image pyramid level for export resolution. At most 4,096 grid candidates and 32 retained tiles per slide in the smoke config. Each region read is bounded; no full-plane TIFF array decode. Partial edge tiles are excluded. |
| Tile labels | Native-resolution, small mask patches; channel 0 only, without label interpolation. All-pixel fractions for background, stroma, benign epithelium and Gleason 3/4/5. No mask means empty/unknown fractions, never guessed zeros or a broadcast slide grade. RGB screening is independent of grade/mask labels. |
| Saved metadata | `tiles.csv` includes `tile_id,path,image_id,x,y,x_level0,y_level0,grid_x,grid_y,area_mm2,tissue_fraction,mask_available` and six fractions. `metadata.json` records source file path/size/mtime, raw header tags/codec, CSV hashes, measured calibration, scale provenance, selection/caps and runtime versions. Full source-TIFF checksums are explicitly unverified. |
| CONCH handoff | CSV/JSON pass the existing `encode_tiles()` input contract. Encoding uses its unchanged canonical preprocessing and projected, normalized CONCH v1 path; no manual normalization or model download. New three-phrase benign/cancer prompt ensembles are unvalidated engineering inputs only. |
| Piece engine | Reuses the existing model-agnostic callable API; adds `analyze_saved_slide(path, scorer, scorer_id=...)` for saved NPZ. Requires explicit physical geometry and preserves provider/model/unknown-patient provenance. Mask fractions, slide grade and foreign masks never reach the scorer. Both baseline and counterfactuals are returned; no tissue is removed. |
| CPU/GPU preparation | `scripts/ncsa_panda_smoke.py` has separate `tile` and `encode` stages. CPU stage hashes each PNG/manifest/metadata file; GPU stage checks those identities, config, expected original checkpoint and shared text fingerprint. Stages require Slurm and fresh outputs. Fixtures cannot be relabelled for real encoding. |

`patient_id` is the literal `unknown`, with `patient_id_known=false`; no biopsy ID is presented as a patient ID. The existing artifact contract requires a development/evaluation field, so these engineering inputs use `split=dev` and explicitly record that no patient-separated evaluation exists. The row-major, color-screened subset cannot establish complete biopsy-piece topology, clean cancer sensitivity or an alert rate. Even genuine small cancer may drive a decision and trigger review.

## Validation and compatibility

The complete local suite passed **156 tests**: 19 PANDA adapter/runner cases, 32 fragment-dependence cases and all 105 historical checks. Both new Slurm wrappers passed `bash -n`; the runner's `--help` succeeded without Slurm or model imports. `git diff --check` passed. The installed package was rebuilt from this worktree before validation.

Local tests use tiny generated TIFF pyramids, including the actual OpenSlide reader. They cover matching/mismatched masks, orientation, label channel/fractions, white-background exclusion, absent masks, measured scale, rounding/coordinates/area, candidate and region bounds, original label/provider checks, provenance, saved-embedding handoff, no-overwrite and Slurm guards. Encoder-contract testing deliberately stops before model loading. No real CONCH output is simulated as scientific evidence.

The `panda` optional extra pins OpenSlide Python 1.4.6, OpenSlide binary 4.0.1.2 and tifffile 2025.5.10. Existing core dependencies remain unchanged. TIFF tags are read with tifffile; pixels are decoded by bounded OpenSlide region calls using its [documented level-0 coordinate convention](https://openslide.org/api/python/#openslide.OpenSlide.read_region).

One observed local runtime limit remains material: this pinned binary failed on a valid **uncompressed RGB** tiled fixture with `Invalid tile byte count ... Expected 768, got 1024`; Deflate-compressed RGB and uncompressed RGBA probes succeeded. Tests use Deflate-compressed RGB fixtures. The reader does not silently decode the full WSI or modify source files to bypass a codec failure. Actual PANDA codecs must pass the CPU stage before GPU scheduling; local compressed-fixture success does not verify Delta compatibility.

## Unsubmitted resource drafts and gates

| Stage | Draft | Verified historical account/QoS | Proposed bound |
| --- | --- | --- | --- |
| CPU tiling | `scripts/slurm/panda_tile_smoke.sbatch` | `bfqi-delta-cpu` / `bfqi-delta-cpu` | 2 CPUs, 4 GB, 10 minutes, `cpu-interactive`; three slides × at most 32 tiles |
| GPU encoding | `scripts/slurm/panda_encode_smoke.sbatch` | `bfqi-delta-gpu` / `bfqi-delta-gpu-mhoda` | One A100, 4 CPUs, 16 GB, 5 minutes, `gpuA100x4`; at most 96 existing PNG tiles |

These are prepared requests, not current availability or approval claims. No remote command, job submission, bulk dataset/weight download or new GPU inference occurred for this request. The existing verified checkpoint is read from `configs/ncsa_one_pair.json` (path, size, SHA-256 unchanged). Reuse the verified private CONCH environment only through a separate prepared runtime containing the added TIFF header reader; its remote package availability is not yet checked. A new immutable remote source snapshot and fresh output directories must be chosen/verified before submission; none is invented here.

Next gates: review/approve the exact CPU smoke scope, verify the prepared runtime and actual TIFF reads, inspect extracted spatial/label QC, then confirm GPU scope and run the bounded encoder. Only after a successful real encoding smoke should a frozen benign/cancer scorer be validated on an appropriate real cohort. These three slides cannot establish clinical validity, same-patient separation, clean performance or unmodified-slide alert rate. Cancer-fragment experiments remain pending; Grade Group, ABMIL, MUSK and larger cohorts remain stretch work.

Exact next command, run locally to review the concrete unsubmitted scope:

```sh
cat "/Users/muneebhoda/Documents/Masters - Fall 2026/Ashby Hackathon-panda-tiling/configs/panda_smoke.json"
```

Reproduce the local checks from the isolated worktree:

```sh
uv sync --locked --no-editable --reinstall-package floater-finder --extra test --extra plots --extra panda
.venv/bin/python -m pytest -q -W error
bash -n scripts/slurm/panda_tile_smoke.sbatch scripts/slurm/panda_encode_smoke.sbatch
```
