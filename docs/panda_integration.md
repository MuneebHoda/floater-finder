# Prostate-biopsy fragment dependence: Phase 1

Current update: the user subsequently verified the personal PANDA root and three pilot slides. The separate `feature/panda-tiling` worktree now carries this implementation forward with a PANDA-specific tiler and `analyze_saved_slide()` handoff. [Current implementation status](../reports/panda_implementation_status.md) supersedes the historical availability blocker below; runtime/model-validity gates remain. No branch was merged and no earlier result was overwritten.

The current target is a minimal CONCH-only benign-versus-cancer S1 safety check for the October 21 submission. The user-supplied `finalplan.md` was read from the local Downloads directory before implementation. Its larger ABMIL/MUSK, Grade Group and 1,000-slide proposals remain stretch work under the user's narrower Phase 1 request.

Work is on `feature/prostate-fragment-dependence`, based on latest local `main` at `bdb13e5`, including its three commits ahead of the fetched `origin/main`. No historical experiment, frozen protocol, source snapshot or result was overwritten. Old TCGA organ-classification scores, detector calibration and failed development cutoff gate are not cancer-detection evidence. The latest [development report](../reports/conch_development_results.md) remains authoritative for that historical experiment.

## Existing artifact audit

| Existing artifact / code | Reuse for PANDA | Required boundary or missing input |
| --- | --- | --- |
| `artifacts.Slide` / `slide.npz` | Pickle-free `feats[N,D]`, `coords[N,2]`, unique `tile_ids[N]`, JSON metadata; exclusive writes and round-trip validation. Suitable for normalized projected CONCH embeddings. | Requires unit vectors and complete model provenance; not a generic unnormalized-embedding format. Add verified PANDA slide identity, provider, labels, geometry and split metadata without inventing patient IDs. The new module accepts plain saved arrays independently of this format. |
| `Slide.metadata.model` | Encoder name, revision, checkpoint SHA-256, preprocessing, projection and normalization. | Reuse only for vectors actually produced with that exact configuration. CONCH v1 (512D) and shared v1.5 (768D) cannot be mixed. |
| `coords`, `tile_step`, `microns_per_unit`, measured MPP metadata | Spatial information and scale conventions can be carried forward. New code accepts measured X/Y scale. | Explicit top-left origin and **tile footprint**, not resized model-input width, are required. Existing 256-micron TCGA fields are not the proposed 224px at approximately .5 MPP. Read real PANDA scale first. |
| Existing TCGA tile manifests / coordinates | CSV tile IDs, image paths and coordinate alignment patterns, header-validation and checksum conventions. | Four sampled 96-tile windows per patient cannot establish full biopsy-piece boundaries. Existing arrays test compatibility only, not PANDA geometry or cancer validity. |
| `foreign_mask` in NPZ and injection provenance | Historical synthetic-injection bookkeeping only. | The new module never receives or consults this mask. Actual decisive pieces have unknown foreignness; synthetic ground truth belongs in separate experiment metadata. |
| `TextEmbeddings` / `text.npz` and CONCH adapter | Frozen prompt ensembles, projected normalized image/text space, fingerprint/checkpoint validation and offline model loading. | Existing prostate-versus-bladder prompts are unsuitable for benign-versus-cancer. New prompts/scorer and clean-slide model-validity checks must precede cancer-fragment stress tests. |
| `scoring.py` | Mean/top-percent cosine pooling is available for a future validated CONCH adapter. | Old pooling outcomes and quantile cutoffs cannot be transferred. Supplied scorer must recompute pooling or attention for every remaining bag. No trained ABMIL model is available here. |
| `injection.grid_neighbors` | Existing regular-grid validation pattern informed the implementation. | It is four-connected; the new module separately implements eight-connectivity with one-tile-gap bridging. Legacy behavior and frozen source hashes remain unchanged. |
| NCSA Slurm wrappers, physical tiler, immutable releases and hash reports | Reusable scheduling, offline CONCH runtime, provenance and exclusive-output conventions. | No pivot job was submitted. Future PANDA extraction/inference must run through Slurm with verified inputs and confirmed new scope. Old oracle-removal machinery remains for historical synthetic experiments, not clinical tissue deletion. |
| Plan's HDF5 / parquet layouts | Future interchange targets only. | Existing NPZ suffices for this milestone. No HDF5/parquet dependency, PANDA mask reader or bulk runner was added. |

## Saved-array API and output

`floater_finder.fragment_dependence.analyze_fragment_dependence` accepts finite floating embeddings (normalization is not required), aligned tile top-left coordinates, an explicit regular-grid step, nonoverlapping rectangular tile footprint, coordinate units, measured microns per unit, source category and scorer identifier. Tile IDs are optional. Use the existing `Slide.load()` when working with CONCH NPZ artifacts, then pass `slide.feats`, `slide.coords` and verified geometry explicitly. No old TCGA footprint is silently used as a PANDA default.

The supplied deterministic `scorer(embeddings, coords)` returns a finite JSON mapping with a nonempty string `prediction` and any raw scores/provenance. It must use the same frozen settings for every call and be invariant to tile row order. Copies protect the saved inputs from scorer mutation. The module scores the full bag once and each nonempty piece-excluded bag once; it does not subtract an old score or fit a new model. Any prediction-label change is recorded as decision dependence, suitable for binary S1. Multi-grade semantics are not implemented.

Components use eight-neighbor grid connectivity, bridging one missing grid tile (Chebyshev distance at most two). Bridging is transitive and can merge nearby fragments. Adjacent or connected tissue is one piece: there is no scorer-driven tile-cluster fallback yet. Duplicate/off-grid coordinates, missing physical scale and overlapping footprints fail validation. Complete tissue coverage must be verified externally; sampled windows and omitted tissue tiles can split or hide real pieces.

Each piece records input row indices/IDs, occupied tile count, bounding box, physical footprint area, area fraction, nearest other-piece edge separation, counterfactual prediction/raw scores and decision-change status. Area is tile count × physical footprint width × height / 1,000,000 mm², excluding empty grid cells. For example, a 224px square at .5 microns/px is **.012544 mm²**, regardless of subsequent encoder resizing. This is occupied **tile-footprint area**, not measured histological tissue area within each tile. Isolation uses the nearest rectangular tile edges, not bounding-box centers. If omission empties the slide, the result and decision-change status are null with `not_evaluable_empty_slide`; no scorer call or benign prediction is invented.

Review alerts are optional and separate from decision dependence. When explicitly supplied, the current exploratory policy requires a decision change, area strictly below `max_area_mm2` and isolation strictly above `min_isolation_mm`. The demo uses 2 mm² and .5 mm solely to exercise software behavior. **These are uncalibrated fixture thresholds, not deployed clinical thresholds.** No lookalike percentile or clean-slide alert-rate calibration is claimed. Genuine small cancer can satisfy the same rule; every alert asks for review, never declares a floater. Original arrays and baseline predictions remain preserved; `tissue_action` is always `preserve_all_tissue`.

Run the saved-artifact demo in a new directory:

```sh
uv sync --locked --no-editable --reinstall-package floater-finder --extra test
.venv/bin/python scripts/fragment_dependence_demo.py --output results/fixtures/fragment-dependence/new-run
.venv/bin/python -m pytest tests/test_fragment_dependence.py -q -W error
```

It saves/reloads `slide.fixture.npz` and writes `alert.fixture.json`. The tracked [JSON example](../examples/fragment_dependence/alert.fixture.json) is deterministic artificial data, with a max-feature scorer unrelated to CONCH or PANDA. It is a software check, not scientific evidence. Output directories/files refuse overwrite; there are no image reads, downloads or GPU calls.

Executed Phase 1 validation: the complete local suite passed **132 tests**, including **27 new cases** for isolated/adjacent/diagonal/gap-connected pieces, non-decisive pieces, a genuine-small-positive fixture, empty counterfactuals, physical areas/scales, invalid inputs, scorer mutation and demo round-trip/no-overwrite behavior. Existing frozen-protocol checks also passed. The generated four-tile fixture contains two pieces: the artificial baseline is `cancer`, omitting the isolated positive piece yields `benign`, and the exploratory rule emits one review alert. These observations establish software behavior only; they do not measure cancer detection or a real-slide alert rate.

## Availability and remaining integration gates

The [bounded Delta check](../reports/ncsa_panda_availability_20261019.json) examined 48 names under `/projects/bfqi/shared/datasets` and `/work/nvme/bfqi/shared/datasets`, at most depth two. No PANDA/prostate-biopsy candidate was found within those bounds. It did not inspect archives, other users' directories, images or features. PANDA availability remains unresolved; no global absence is inferred. Allocation and queue snapshots are in [NCSA setup](ncsa_setup.md#prostate-biopsy-pivot-read-only-availability-check).

Phase 2 remains gated in this order:

1. Locate authorized PANDA slides, masks and provider/label metadata; verify access/license terms, measured MPP, mask semantics and artifact alignment. The plan's proposed CSV columns/provider mask codes have not been verified against a local dataset. Confirm patient/group separation where available; unknown patient identity is a leakage limitation, not permission to invent IDs.
2. Freeze a bounded same-provider development/evaluation split and a CONCH benign/cancer scorer with exact prompts, pooling, threshold and model provenance. Validate it on unmodified real slides before fragment stress tests. Confirm new-scope download/GPU authorization and concrete resources before execution; no PANDA job or download is currently authorized by historical TCGA approvals.
3. Confirm complete-biopsy tissue tiling and component geometry. Use cancer-mask-supported contiguous fragments and separate development calibration from held-out hosts/donors. Check label/provider validity and retain genuine small-positive controls. Adjacent placement may defeat component-only analysis and must be reported as a limitation until a validated fallback exists.
4. Run bounded S1 same-provider fragment experiments with raw baseline/counterfactual scores, requested/realized physical area, exclusions, seeds, provenance and explicit denominators. Calibrate the review policy on separate clean slides and report alert rates on **unmodified** benign and cancer slides, including genuine small positive regions. Keep synthetic stress results distinct from native-floater and clinical performance claims.

No real PANDA cancer scoring, cancer-fragment experiment, unmodified-slide alert rate, Grade Group result or new GPU inference has been executed for this pivot. The minimal next input is a verified authorized PANDA root (or an explicitly approved bounded acquisition plan), followed by scorer validation; the fixture alone cannot resolve either gate.
