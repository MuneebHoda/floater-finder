# Floater Finder — October 21 presentation outline

This is a slide narrative and reproducible figure pack, not an executed final-test report or a PowerPoint file. Every quantitative figure comes from real, saved development observations. Artificial arrays remain software fixtures. All 24 test slides are unscored.

| Slide | Takeaway and speaker evidence | Figure |
|---|---|---|
| 1. The safety question | Which tissue component controls a frozen prostate-biopsy prediction, and when should a pathologist review it? Preserve tissue and baseline; decisive does not mean foreign. | [CONCH pipeline and protocol](figures/panda_review_v1_final/pipeline_and_protocol.png) |
| 2. What actually ran | 120 real Radboud slides; 72 train / 24 calibration / 24 test; 50,729 saved CONCH v1 embeddings; 112 µm representative tiles with coordinates. Patient separation is unknown. No new model or GPU inference for review analysis. | Same pipeline; [artifact evidence](panda_full_cohort_completed_23054910.json) |
| 3. Clean cancer baseline | Fixed top-5% calibration confusion `[[5,3],[1,15]]`: accuracy 20/24, balanced accuracy 78.125%. Development only. Existing panels also show exploratory pooling and low/high classification; keep attention on benign/cancer top-5%. | [Preserved clean classification figure](figures/panda_clean_baseline_23055022/calibration_confusion.png) |
| 4. Synthetic cancer fragments can change decisions | 192 S1 draws are 32 hosts × six doses, not 192 patients. Calibration new errors by positive dose are 1/5,1/5,2/5,2/5,2/5 originally correct hosts. Eight error instances affect two hosts; three initially wrong hosts stay outside the new-error denominator. | [Preserved contamination curves](figures/panda_s1_development_23065666/stress_curves.png); [audited transitions](panda_scientific_audit_v1.md) |
| 5. Dependence is not foreignness | Both a known injected three-tile component and a genuine annotated cancer-containing component change cancer to benign on exclusion. The genuine example contains 0.171 mm² annotated cancer inside a much larger sampled component; do not describe that whole component as a tiny cancer focus. | [Preserved paired examples](figures/panda_piece_development_23065744/piece_examples.png) |
| 6. Physical pieces need evidence | Observed RGB connectivity replaces inferred sampled-cell links without filling gaps. Four of six formerly single-component calibration cases become multiple, but threshold sensitivity and approximate boundaries remain. | [Actual training RGB quality examples](figures/panda_review_v1_final/topology_quality_checks.png) |
| 7. Review utility and clean harm conflict | Combined: 0/24 clean alerts but 0/40 fragments detected. Decision-only: 8/8 induced-error instances recovered, 4/24 clean slides alerted and 3/20 clean-correct predictions damaged under hypothetical filtering. Never delete tissue. | [Review tradeoff](figures/panda_review_v1_final/review_tradeoff.png) |
| 8. Genuine tissue and reviewer burden matter | Spatial-only flags 19/24 clean slides, 3.58 components/slide and 4/26 genuine-cancer components. Decision-only flags 1/26 genuine-cancer components. Zero-flag matched random controls are uninformative. | [Burden and genuine-tissue controls](figures/panda_review_v1_final/review_burden_and_genuine_tissue.png) |
| 9. A useful negative result | No preregistered candidate reaches useful recall with acceptable burden. Five calibration mixtures pass the selected visual threshold and none also pass influence. Do not relax thresholds to create a success. | [Frozen failure funnel](figures/panda_review_v1_final/review_failure_funnel.png) |
| 10. Reproducible handoff | 192 software tests pass. Frozen rejected protocol, source hashes, masks/unknowns, denominators and statistical plan are committed. CPU preflight verified 10,988 files across 24 held-out slides without predictions or label decoding. Final evaluation is prepared but blocked; clinical usefulness remains unverified. | [Frozen preparation and exact commands](../docs/panda_final_test_v1.md) |

Do not headline a 0% false-alert rate: 0/24 has a Wilson 95% interval extending to 13.8%, and the combined policy misses all calibration fragments. Repeated doses, random draws and reused donors are not independent patients. Native genuine cancer controls do not establish verified absence of every real-world contaminant. TCGA organ-classification numbers are historical and are not cancer evidence.

## Reproduce figures without new model inference

Run from the repository root in the locked environment with `plots` and `test` extras. Use a fresh output directory. The five new charts export PNG and SVG and record source/input/file hashes. Their committed source-overview PNGs are bounded actual training RGB previews, not generated histology.

```sh
.venv/bin/python scripts/plot_panda_review.py \
  --selection reports/panda_review_selection_v1.json \
  --diagnostics reports/panda_review_diagnostics_v1.json \
  --qa reports/panda_topology_qa_v1/provenance.json \
  --output results/presentation/review-figures-new-run
```

The diagnostic summary can be regenerated from the checksum-pinned `component_cases.json` retained on Delta at `/work/nvme/bfqi/mhoda/floater-finder/panda-review/development-v1-20261020T235701Z/component_cases.json` (identity in `reports/panda_review_measurement_checkpoint_v1.json`). Retrieval is not a model run. Its script accepts only train/calibration cases and checks the saved selection measurement hash:

```sh
.venv/bin/python scripts/summarize_panda_review.py \
  --selection reports/panda_review_selection_v1.json \
  --metrics reports/panda_review_metrics_by_case_v1.json \
  --topology reports/panda_topology_audit_v1.json \
  --cases results/panda/review_development_v1/component_cases.json \
  --output results/presentation/review-diagnostics-new-run.json
```

Earlier figure sources remain `scripts/plot_panda_baseline.py`, `scripts/plot_panda_s1.py` and `scripts/plot_panda_piece_examples.py`; each preserved figure directory contains provenance. The piece plot's exact tabular input is committed as `reports/manifests/panda_piece_plot_inputs_23065744.json`. See [complete findings](panda_review_results_v1.md) for metric definitions and limitations.
