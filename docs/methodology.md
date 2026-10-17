# Floater Finder methodology and contracts

Research prototype: synthetic embedding-level contamination is not verified real contamination, and cosine similarities are not clinical diagnoses. CONCH is the first model. No model is fine-tuned.

## Inputs and cohorts

The intended first contrast is TCGA-PRAD (prostate) versus TCGA-BLCA (bladder), using diagnostic slides with report linkage when available. TCGA-LUAD/LUSC, same-organ contamination, MUSK and PathGen-CLIP are later work. The currently known shared CRC/PathGen/PathMMU directories do not establish the availability of the intended TCGA cohorts.

`inventory` discovers only filenames in explicitly supplied roots, with bounded depth/count and no hidden-directory or symlink traversal. It opens neither slide pixels nor reports. CSV metadata supplies project, organ, independent class label, split, report link/provenance, tile manifest, coordinate scale and magnification. Every unknown stays blank and appears in `missing_data.json`.

TCGA participant and source-site prefixes follow the [GDC barcode documentation](https://docs.gdc.cancer.gov/Encyclopedia/pages/TCGA_Barcode/). A `DX` filename convention is reported as inferred diagnostic status, not independent verification. Curated diagnostic status needs a provenance entry. A filename does not determine PRAD/BLCA membership, diagnosis, patient independence, or magnification by itself.

Patient IDs are internal research bookkeeping. Console commands report counts, not patient identifiers or medical-report contents. Keep manifests, reports and artifacts out of git and public demo screens. `results/` and `data/` are ignored.

Assign development/evaluation patients before running experiments. Inventory rejects patient overlap across splits. Pair selection uses different patients within one split and prefers a verified normalized institution match when available. An institution mapping must include source-site code, normalized institution ID/name and provenance. Matching raw source-site codes is never substituted for an institution mapping. An unavailable mapping is a limitation, not a match.

## Tile inputs and embedding artifacts

The encoder accepts **already extracted tiles** using CSV columns `tile_id,path,x,y`. Paths are relative to the manifest. Row order is stable; IDs must be unique. Raw WSI tiling has not been implemented or exercised in this session. A verified TRIDENT tile/coordinate export or another documented tiler is needed for raw diagnostic WSIs. Do not infer coordinates from arbitrary filenames or use non-spatial tile packs as spatial slide reconstructions.

`configs/slide_metadata.example.json` is an intentionally incomplete template. Supply real slide/patient IDs, project, expected organ, independent label, split, coordinate units, regular grid step, physical scale when known, magnification and coordinate reference. Do not fill unknown fields with plausible values.

NPZ slide artifacts contain:

| Key | Contract |
| --- | --- |
| `feats` | Finite, unit-normalized floating matrix `[N,D]`, N > 0. |
| `coords` | Finite `[N,2]` coordinates in explicitly named units. |
| `tile_ids` | Unique stable Unicode identifiers aligned with feats/coords. |
| `foreign_mask` | Boolean `[N]`; true only for synthetically injected rows. |
| `metadata` | JSON scalar with slide/patient/project/organ/split/source-kind and model/coordinate provenance. |

Image and text model records must match exactly: model name, installed package/source revision, checkpoint SHA-256, projection, normalization, preprocessing and runtime metadata. Embedding dimensions must match. Fixture/real mixing is rejected. Loading uses `allow_pickle=False`. Existing output files/directories are preserved; choose a new destination for a repeat run.

`encode` caps image reads at 128 manifest rows by default and records whether the manifest was truncated. A result on a tile subset is **not** a full-slide result. Reports must retain that distinction. The same artifact can be reused for all contamination levels and seeds without re-encoding.

## CONCH interface and availability

Primary sources inspected on 2026-10-17:

- [CONCH source](https://github.com/mahmoodlab/CONCH/tree/141cc09c7d4ff33d8eda562bd75169b457f71a62), particularly `conch/open_clip_custom/coca_model.py` and `factory.py`.
- [TRIDENT encoder source](https://github.com/mahmoodlab/TRIDENT/blob/bdeeb74b7eaad8d48bda232bde7de66cae980918/trident/patch_encoder_models/load.py).

The inspected TRIDENT `conch_v1` builder accepts `with_proj` and `normalize`; its implementation defaults both to false. The proposal's `encoder_factory("conch_v1", with_proj=True, normalize=True)` explicitly enables both. Neither CONCH nor TRIDENT is installed in the local project environment, and the current remote installation was not inspected because SSH timed out. Source inspection and stub-based interface tests do not establish that an installed real model works.

The implemented adapter uses official CONCH directly, with `conch_ViT-B-16`, the factory-provided image transform and tokenizer, `encode_image(..., proj_contrast=True, normalize=True)` and `encode_text(..., normalize=True)`. It checks the installed signatures at runtime. It verifies encoder parameter coverage/shapes because upstream loading is non-strict; missing decoder weights are allowed, missing image/text encoder weights are not. This checks checkpoint compatibility, not independent authenticity of the pretrained file.

Only an existing local checkpoint path is accepted. Hub/offline settings disable implicit model downloads and implicit credentials. Actual encoding requires a Slurm job and a visible CUDA GPU; there is no login-node, CPU, MPS, fake-model or random-feature fallback. Optional PyTorch/CONCH dependencies were not installed locally. The site guide documents `pytorch-conda/2.8`, but that environment still needs verification.

Real encoding records checkpoint/source hashes, exact transforms, tile count, model-load time, image-read/preprocessing/encoding/transfer time and measured tile throughput. No throughput has been measured yet.

## Prompts, scoring and pooling

The four fixed phrases per class are in `configs/conch_smoke.yaml`; they describe prostate and urinary-bladder tissue. Do not tune them on final evaluation cases. For each class, normalize each prompt vector, take its arithmetic mean, then normalize that class mean again. Store the exact phrases and class order in the text artifact. Calibration fingerprints the vectors and their prompt provenance.

Tile scores are cosine similarities in the shared projected space. Mean pooling averages all tile scores separately for each class. Top-1% and top-5% pooling sort each class's scores independently and average its highest K, with `K=max(1,ceil(fraction*N))`. K is recomputed after injection or removal. Equal tile scores retain artifact order; equal final class scores choose the first class in the stored class order. No logit temperature or clinical probability interpretation is applied.

Original-slide errors are retained. The runner requires an independently supplied ground-truth class; it does not assume every original prediction is correct.

## Synthetic contamination and oracle

Percent means `foreign_tile_count / original_host_tile_count * 100`, not the fraction of the final contaminated bag. Use requested levels 0, 0.5, 1, 2, 5 and 10%. Foreign count is `ceil(requested_percent * original_count / 100)`; positive requests on small slides may realize larger percentages. Both values are recorded.

Host/donor must be unmodified, different-patient artifacts in the same split/model space. Positive injection needs matching coordinate units/scale/grid step. Select a four-neighbor connected donor fragment on the declared regular grid. A seeded NumPy generator chooses a starting tile in a sufficiently large connected component, then grows a connected randomized frontier. Insufficient capacity, off-grid/duplicate positions, missing grid information and incompatible spatial metadata are explicit errors.

Append unchanged donor embeddings after unchanged host embeddings. Translate the fragment one tile step beyond the host's right bounding edge, aligned near its median y; preserve relative fragment positions. IDs are donor-slide-qualified to avoid collisions. Save donor IDs, selected indices, translation, mask, seed, intended/realized contamination and original host metadata. Zero injection preserves all arrays and records zero-injection provenance.

This is a spatial visualization of an embedding mixture, **not** a pixel-level slide simulation. Physical staining, overlap, tissue processing and scanning artifacts are not reproduced. A tile fraction is not an area fraction unless equal tile footprint/scale has independently been established.

Oracle removal deletes only the known injected rows, preserves original host ordering and provenance, and verifies exact arrays plus numerically equivalent scores and identical predictions for all pooling rules. An oracle defect stops the runner; it is not silently excluded as an ordinary failed case.

## Stress-test metrics

Use one donor per host per run; donor replicates belong in separate runs. A run has one explicit development/evaluation split. For each host, seed, percentage and pooling rule, retain clean correctness, both predictions, raw class scores, tile counts, oracle status, organ/project contrast and configuration.

Within each percentage/seed/pooling stratum:

- Eligible flip rate = changed predictions among originally correct, evaluable host slides / those originally correct, evaluable host slides.
- Raw prediction-change rate = changed predictions among all evaluable hosts / all evaluable hosts, including initially wrong cases.
- Denominators count unique host slides, not tile counts or repeated seeds. If the eligible denominator is zero the eligible rate is JSON null, not zero.

Explicitly report exclusions from `failures.json`; rates describe successfully evaluated cases. Do not pool repeated seeds as independent patients. Preserve configuration, input/source hashes, exact prompts and model provenance in `experiment.json`. Zero flips are valid; do not select prompts/donors to force an impressive curve.

`plot` uses Matplotlib for an exportable scientific chart only after at least two real host slides and two contamination levels exist. It plots per-pooling mean eligible rates across seeds and rejects fixture runs. Denominators remain in `summary.json`; a small pilot is not a population estimate. No scientific chart was produced this session.

## Detector, calibration and controls

The mismatch score is maximum alternative-organ similarity minus expected-organ similarity. Expected organ comes from curated metadata; independent subtype labels and injection masks are not inputs to this score.

Visual inconsistency is `1 - maximum cosine similarity to a spatially distant tile`. Exclude all reference tiles within 1 mm by default, including self and nearby members of a compact synthetic fragment. Require a verified `microns_per_unit`; unknown pixel scale is an error. If a tile has no distant reference, its signal is undefined and evaluation fails explicitly. Double-blocked reference/query loops limit memory; time remains quadratic, so use modest subsets and scheduled compute for substantial runs. No whole-slide scalability claim is made.

Standardize each component using clean development-tile mean and standard deviation (floor 1e-8). The combined score is `lambda*organ_z + (1-lambda)*visual_z`, default lambda 0.5. Apply an equal-weight spatial average within 0.1 mm, including self. Store all parameters. Calibrate separate organ-only, visual-only and combined thresholds from clean development scores at the 99th percentile using the `higher` quantile convention; flag strictly greater scores.

Calibration rejects injected or evaluation slides. Evaluation rejects any host **or donor** patient used in calibration, altered prompts, or incompatible model/source provenance. The measured development false-alarm rate is recorded. A 99th-percentile target does not guarantee 1% false alarms on unseen slides. Fixed-coefficient scoring with fitted normalization/thresholds is training-free, with calibration; it is not parameter-free. Calibration was not selected with synthetic ground-truth labels.

Evaluation reports tile AUROC (null without both classes), detection rate and measured host false-alarm rate, precision (null if no flags), one-fragment hit, genuine host tiles removed, and predictions/scores following filtering. Compare organ-only, visual-only, combined, no filtering, oracle and seeded random removal of the same number of tiles. Separate clean controls report prediction changes and correct-to-wrong damage. All-removed cases have undefined filtered predictions rather than an invented class.

These algorithms have only software/fixture validation so far. Real suspicious regions are candidate regions, not confirmed tissue floaters.
