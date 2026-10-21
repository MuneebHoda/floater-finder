# Shared research engine v1

The historical `experiments.py`, S1/S2 runners, CONCH artifacts and all measured results remain unchanged. New callers use `floater_finder.research`; this is an incremental shared boundary, not a repository-wide move into empty packages.

## Audit and integration

The old S1 and S2 modules independently check source/split/grade, traverse annotation-selected four-connected components, validate donor indices, translate the same appended fragment and construct near-identical provenance. They already share dose rounding (`panda_stress.foreign_count`), grid adjacency, saved artifacts, pooled scoring and oracle removal. Review runners also repeat verified input loading and result writing. New code reuses those existing input/scoring primitives, consolidates new source/condition validation and interventions, and supplies exact legacy adapters. Historical files are preserved so published source hashes continue to resolve.

`research.contracts` defines frozen, versioned `PredictionTask`, `SlideArtifact`, `DonorSelection`, `InterventionSpec`, `DetectionResult`, and `ExperimentRun`. `SlideArtifact` stores an immutable private NPZ snapshot, returning a new validated `Slide` on materialization. Metadata cannot alias the original. The predictor interface is a callable accepting a `Slide` and returning an ordinary scalar/list JSON prediction mapping; the portable linear-probe interface is `load_predictor(directory).score_slide`.

`research.engine.apply_intervention(host, donor, spec, occupancy=...)` returns an intervention result with the new slide, retained immutable original and audited identities. `result.verify(scorer)` verifies output integrity, restores all original vectors/coordinates/IDs/metadata and checks exact prediction equality. Replacement must use this restoration: deleting marked tiles cannot recover replaced host evidence. `legacy_s1` and `legacy_s2` use the same core and reproduce historical metadata, logical arrays, ID order, ID string dtype (including the S1 zero-dose widening) and predictions. Legacy oracle equality is logical: NumPy string arrays historically retain widened storage after removal; the new retained snapshot restores even the original dtype.

`donor_components` unifies annotation conditions. Native Gleason fractions are donor eligibility/evaluation information, never hidden predictor inputs. `select_donors` ranks capacity first, then a deterministic seed/host/condition/donor hash, selects multiple distinct donors and yields a connected unique nested prefix. Mask-unavailable donors are ineligible for annotation-specific conditions. Same-source sham controls are explicit and never labelled biological foreign tissue.

## Implemented modes and interpretation

- `append_legacy`: exact historical three-grid-step right-edge append.
- `near_tissue`: rigid translation to a known, bounded, unoccupied overview footprint, within 224 µm Chebyshev distance of observed RGB tissue.
- `replacement`: substitute donor vectors at a unique connected set of existing host positions; retain original IDs, coordinates and private original vectors.
- `within_region_context`: a distinct, explicitly described observed boundary context using verified empty geometry; this is representation placement, not physical embedding inside tissue.
- Same-source shams apply the same operations using native host representations. They are editing/sampling controls, not foreign contaminants.

Near/context placement **requires** a complete bounded foreground overview with source SHA, measured physical scale and its explicit RGB rule. An absent sampled tile is not evidence of an empty area. Both foreground collision and existing exported-host footprint collision are checked, and the entire donor footprint must stay inside the verified image bounds. No morphology, invented bridges or unsampled-region vacancy assumptions are used. Search is capped at 100,000 anchors and foreground at four million pixels. Failure produces an exclusion rather than a fallback outside the image. RGB threshold segmentation is a measured proxy, not pathologist-verified tissue boundaries; fine tissue missed at level 2 remains a limitation.

**For a fixed appended feature bag, relocating coordinates cannot change any order-invariant mean/top-K/linear-pooling prediction.** The runner explicitly verifies equal feature bags and exact predictions. Such placement affects spatial/context detectors, not the underlying bag classifier. Replacement changes evidence and may change its prediction. Coordinates alone are not a pixel-level simulation.

## Registry, checkpoints and status

`Registry(output, ExperimentRun(...))` records immutable configuration/source/dataset/checkpoint identities. Exclusive atomic writes prevent overwriting checkpoints. A locked append-only event chain records planned/running/verified/failed/excluded states, Slurm IDs, validation and limitations. Checkpoint payloads and the event chain are SHA-verified on reopening and reporting; a terminal seal detects tail changes. Failed/running runs can resume only with the same configuration and input identities; verified runs return their saved summary. Unregistered partial artifacts require inspection and are never silently overwritten. CPU status:

```bash
PYTHONPATH=src python scripts/research_status.py /path/to/versioned/run
```

Registry JSON is intentionally one file per event/checkpoint: no service/database, no additional dependency. In-process verified-chain caching avoids quadratic shared-filesystem reads; final reports/reopens rehash every registered artifact. Filesystem owners can still change files, so public immutable source/result hashes remain the external audit anchor.

## Bounded real-input acceptance

`configs/research_engine_acceptance_v1.json` is frozen before any new measured outcomes: first two slide-ID-sorted training hosts per task, two eligible donors, three deterministic seeds, doses 0/.25/.5/1/2/5/10%, four intervention modes and same-source shams. Four bounded level-2 overviews are the only new WSI reads. Existing saved-CONCH artifacts are verified before use. All test predictions remain sealed. No GPU or model inference is requested.

The CPU runner records raw before/after/oracle scores, exact legacy comparisons, geometry exclusions, realized dose against the original host count and coordinate-only prediction invariance. Results are real-input **engineering acceptance and placement ablation**, not independent validation or clinical performance. Repeated seeds/donors/doses are trial instances, never patients. Optional previously selected portable S2 predictors are hash-pinned before any contaminated predictions; selection cannot use this experiment's outcomes.

Resources: one task, 2 CPUs, 4 GB, at most 15 minutes, verified `bfqi-delta-cpu` account/QoS and `cpu-interactive` partition. Exact source/output/command and measured cost are recorded separately after submission. Architecture is committed before new outcomes; scientific findings are a separate commit.

## Separate pixel-composition study: prepared, not executed

A useful next study would use four training host/donor tile pairs selected by fixed slide/tile hashes, three fixed patch area fractions (1%, 5%, 10%) and two placements. Each pair/area/placement has four variants: unchanged host, foreign patch, same-source patch and a cut/reinsert host seam/boundary control. This gives **96 composite/control images**, plus original donor/host hashes already available. Record parent tile/WSI IDs, file SHA, exact pixel mask, patch box, area, interpolation, clipping and compositing operation; use identical canonical CONCH v1 preprocessing. Compare pooled-score change, embedding distance and detector anomaly against both sham and seam controls. Fail on changed input hashes or a missing same-source/seam control. No model or fresh weights are needed.

GPU inference remains approval-blocked. Proposed envelope: one existing-checkpoint A100, 4 CPUs, 16 GB and 5 minutes (0.0833 GPU-hour), on verified `bfqi-delta-gpu`/`gpuA100x4-interactive`. The prior 944-tile profile completed in 54 seconds (`reports/panda_gpu_profile_23051673.json`); this is a conservative queue reservation, not a measured runtime for composites. Acquisition is zero bytes; generated PNG/NPZ storage is estimated below 100 MB. Before requesting approval, freeze exact real-input tile IDs/masks/checkpoint/output, provide the concrete Slurm command, and separately test CPU composition. This version has **not** composed real slides, re-encoded any image, or claimed pixel-level results.

## S2 v2 integration preparation (before its contaminated outcomes)

`configs/research_engine_acceptance_v2.json` adds `same_grade_gp3_only` beside `high_gp45`, uses the training-only selected low/high linear predictor, and hash-pins `selection_frozen.json` (`acff113f…`). It retains the v1 file unchanged. The runner checks the selected model ID, class order, training-only selection, untouched-test flag and predeclared engineering-readiness gate before creating run outputs. The stronger predictor is not selected using any contaminated prediction. Both original append and new placements share the same frozen model. Every checkpoint key and metric group includes the donor condition.

The initial bounded S2 v2 run has only two slide-ID-sorted training hosts. The head was fit on training slides, so this stress experiment is **resubstitution**, not independent validation and not completion of the full S2 v2 cohort. A fresh cohort or properly cross-fitted contamination study is still required. S1 continues its historical top-five-percent scorer. A native same-source sham is explicitly `foreign_mask=False`; separate audited `altered_indices`/`altered_count` retain edit tracking without creating false foreign-tissue truth labels. The development loader resolves training IDs before opening tiling metadata; it never opens test embedding arrays or test tiling metadata.
