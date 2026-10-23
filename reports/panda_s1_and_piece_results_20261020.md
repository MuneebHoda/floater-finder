# PANDA S1 and piece-dependence development results — October 20, 2026

**The 120-slide PANDA → tiling → CONCH pipeline is executed and verified.** There are 50,729 normalized 512-dimensional embeddings, 119 usable native masks, 39 GP4/5-positive high-grade masks and fixed 72/24/24 train/calibration/test splits. All 24 final-test slides remain unscored. Original TCGA evidence, original manifests and prior experiments are preserved.

| Job | Executed stage | Result | Elapsed |
|---|---|---|---|
| 23054910 | 117 new slide embeddings; 944 embeddings reused | COMPLETED 0:0 | 21:46 |
| 23055022 | All 120 artifacts verified; 96 development slides scored | COMPLETED 0:0 | 3:04 |
| 23065666 | CPU S1 development stress, existing features only | COMPLETED 0:0 | 0:14 |
| 23065744 | CPU calibration piece counterfactuals | COMPLETED 0:0 | 0:11 |

The full GPU job consumed 0.3628 GPU-hour within its approved 0.75-hour cap. The subsequent jobs used no GPU and no additional data/weight downloads.

## Clean baseline first

Top-5% benign/cancer calibration accuracy is **20/24 = 83.3%**, balanced accuracy **78.1%**, with confusion `[[5,3],[1,15]]`: 15/16 cancer and 5/8 benign slides correct. This is descriptive development evidence. The false-positive rate among these eight benign slides is 3/8; no clinical usefulness or independent final-test performance is established. All pooling methods, raw scores, errors and denominators are in the [baseline report](panda_120_embeddings_23054910.md). No trained head was needed for this initial nondegenerate engineering baseline.

## Connected cancer-fragment S1 stress

**192 trials / 32 distinct benign host slides / 21 distinct donor slides**, with 24 training and 8 calibration hosts, one seed, all six requested contamination levels and no capacity exclusions. Every donor tile has at least **10% native GP3+GP4+GP5 annotation**. Each donor subset is four-connected without bridging missing cells; fragments are nested unique prefixes of one fixed donor component per host. Host/donor are different Radboud slides in the same split. Reused donors and overlapping doses are correlated observations, not independent patients.

All **192/192 exact oracle recoveries** passed: original features, coordinates, tile IDs, metadata and pooled predictions/scores were restored. This verifies pipeline integrity; it is not learned-detector performance. Independent local metadata checks reproduced connectivity, annotation thresholds, physical/annotated areas, realized counts, score argmax and aggregate metrics for all trials.

Calibration prediction changes from the clean prediction (each cell has **8 host slides**):

| Requested foreign/original host tiles | Mean | Top-1% | Top-5% |
|---|---:|---:|---:|
| 0% | 0/8 | 0/8 | 0/8 |
| 0.5% | 0/8 | 1/8 | 1/8 |
| 1% | 0/8 | 1/8 | 1/8 |
| 2% | 0/8 | 1/8 | 2/8 |
| 5% | 1/8 | 1/8 | 2/8 |
| 10% | 4/8 | 2/8 | 2/8 |

At 10%, top-5% retains the original benign label for 3/8 mixtures versus 5/8 clean hosts: two clean-correct hosts changed to cancer. Three other hosts were already false-positive cancer predictions. Therefore 5/8 cancer responses in the mixtures must not be described as five newly induced errors. Mean pooling changes 4/8 hosts at that dose. Requested percentages use foreign tiles / **original** host tiles, not total mixture tiles or native WSI area; exact ceil-rounded realized percentages are retained.

These are genuine saved features with synthetic placement, not pixel-level contamination or evidence of actual foreign tissue. Clean evaluation remains outcome-blind; mask-guided donor selection is a separate saved-feature view. No dedicated donor re-encoding was needed because the existing representative artifacts supplied connected components of sufficient capacity.

[Protocol](../docs/panda_s1_development_v1.md) · [Raw trials](panda_s1_trials_23065666.json) · [All summary metrics](panda_s1_summary_23065666.json) · [Donor audit](panda_s1_donor_audit_23065666.json) · [Executed stress chart](figures/panda_s1_development_23065666/stress_curves.png) · [Verified execution](panda_s1_completed_23065666.json).

## Real leave-one-piece-out diagnostic

The existing model-agnostic engine ran on **24 unmodified calibration slides and 40 positive-dose calibration mixtures**, with the development top-5% scorer. Components are 8-connected occupied sampled cells with **no gap bridging**. A supplied scorer recomputes pooling on the remaining embeddings. Sparse sampling does not establish complete biopsy-piece boundaries.

Of 24 unmodified slides, **18 were evaluable and 6 were unevaluable**: each unevaluable case had one sampled component, so its only exclusion left an empty bag. Empty counterfactuals remain `not_evaluable_empty_slide`, never an assumed benign prediction or an evaluable negative. **7/18 evaluable slides had a decision-changing component**. This is a descriptive component-dependence rate, **not a review-alert rate or foreign-tissue false-positive rate**. No alert policy was supplied; `review_alert_rate` is null.

Across the 40 mixtures, **8 counterfactual reports had a decisive pure-foreign component**, exactly matching the preceding S1 prediction changes. Excluding every injected component reproduces the corresponding clean binary scores. Repeated doses involve the same eight hosts and are not forty independent cases.

Two executed examples show why automatic removal would be unsafe:

- **Known synthetic donor:** host `da15226ed2a9ca5a83e831a9c57f5380`, 3 genuine cancer-positive donor tiles / 428 original host tiles, requested 0.5%, realized about 0.701%. Excluding the 0.0375 mm² injected component changes cancer back to benign. The exact physical footprint in the JSON is authoritative.
- **Unmodified annotated cancer:** GG1 slide `03849b0243900d79446bb27849dc0bb2`. Excluding a 435-tile sampled component (5.4394 mm² footprint, 0.1710 mm² annotated cancer within sampled windows) also changes cancer to benign. That is a component containing genuine annotated tumor; it must not be labeled foreign. The occupied footprint is not the native tumor area or an asserted complete physical piece.

[Spatial footprint/annotation examples](figures/panda_piece_development_23065744/piece_examples.png) · [Genuine-cancer counterfactual JSON](panda_piece_genuine_cancer_example_23065744.json) · [Known-injection counterfactual JSON](panda_piece_synthetic_foreign_example_23065744.json) · [All 64 case summaries](panda_piece_summary_23065744.json) · [Verified execution](panda_piece_completed_23065744.json).

## Remaining gates

The embedding and development engineering stages above are executed; no fixture is used as scientific evidence. Patient-level independence remains unverified. The failed LZW mask remains excluded/unknown, and the GG1 annotation/slide-label discrepancy is retained without relabeling.

Before final evaluation, freeze the review-alert definition and its calibration protocol, address the sampled-component/topology limitation, and assess genuine-tissue damage. Organ/visual/combined detector comparisons, multi-neighbor calibration, matched random-removal controls, calibrated unmodified-slide alert rates and independent final-test performance are **not executed** in these jobs. S2/Grade Group upgrading remains stretch work. No clinical validity is claimed, and no additional model or GPU batch is authorized by the completed batch approval.

Next exact review command, from the repository root:

```sh
python3 -m json.tool reports/panda_piece_genuine_cancer_example_23065744.json
```

Software validation: **178 tests pass** with warnings treated as errors. Charts were generated from executed outputs and visually checked. This checkpoint is recorded on `feature/panda-tiling`; main and the original checkout are preserved. The verification JSON records the state at its original verification timestamp.


## Reproduce the component-example figure locally

The committed [plot inputs](manifests/panda_piece_plot_inputs_23065744.json) contain only measured coordinates, native annotation fractions and provenance for the three illustrated source slides. Their bytes match the original figure-input SHA256. Raw WSIs, tile PNGs, model weights and embedding arrays remain outside Git. From this worktree, choose a fresh output directory:

```sh
.venv/bin/python scripts/plot_panda_piece_examples.py \
  --inputs reports/manifests/panda_piece_plot_inputs_23065744.json \
  --examples reports/panda_piece_completed_23065744.json \
  --trials reports/panda_s1_trials_23065666.json \
  --genuine-report reports/panda_piece_genuine_cancer_example_23065744.json \
  --foreign-report reports/panda_piece_synthetic_foreign_example_23065744.json \
  --output results/replay/panda-piece-examples
```
