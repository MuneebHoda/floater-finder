# Detector v3: context-aware anomaly scoring remains ineffective at low burden

October 20, 2026. **Training-only research result; no independent validation.** The preregistered robust-NN5 primary detects **1/120** saved injected fragments, flags **7/72** unmodified slides, and flags five genuine annotated-cancer components. It fails the retained 20% fragment-recall utility target. All seven evaluated methods fail that target at fold-fit review budgets; no result supports deploying review alerts or launching the sealed final test. No primary switch, threshold relaxation, calibration scoring, new GPU encoding, WSI processing or new contamination draw occurred.

## Audit and new hypothesis

Historical v1 failed because visual anomaly and frozen cancer influence often occurred on different components. Its training condition intersection was 16/120 visual hits →5/120 visual-plus-influence hits; on already inspected calibration it was 5/40 →0/40. V2 combined ranks increased resubstitution training hits to 22/120 but still failed its utility targets, with 0/40 known-calibration hits. Those committed negative outcomes are unchanged. Morphology and consequence should be measured separately: a native cancer region can legitimately be unusual and decisive.

This version computes seven signals directly from real saved CONCH image vectors, observed-RGB component indices and verified relative physical coordinates: NN1, NN5, robust NN5, background-centroid distance, nearest-component-centroid distance, physically distant NN5, and equal-slide training-cohort centroid distance. Robust NN5 standardizes the component’s neighbor distance against the remaining tissue’s median/MAD, with a fixed 0.01 MAD floor. Cohort references contribute one normalized mean vector per fitting slide, so slide tile counts do not determine reference weight. These are new representation/context hypotheses rather than relaxed v1/v2 thresholds.

## Training-only design and feature boundary

[Implementation and specification](panda_detector_v3_preregistered_v1.md) were committed before results at `4bf89cd1e2f1dc838ccd84bc626d090709e83476`. Five deterministic slide-ID-grouped folds use seed 20261022. Reference centroids and strict `score > threshold` cutoffs fit clean outer-training folds only. A fitting slide is removed from its own reference. Every fitting threshold satisfies the ≤10% alerted-slide and ≤0.5-component/slide targets. Outer-fold behavior is measured separately: fold calibration does not guarantee held-slide burden. The primary robust-NN5 method was fixed in advance; other methods are ablations, not retrospectively selected replacements.

Stage 1 shortlists unusual components independently of their cancer scores. Stage 2 reports signed cancer-margin influence, decision change and the frozen counterfactual on exactly that shortlist. Influence does not veto a visual shortlist and does not label it foreign. A separate comparator applies the historical signed-influence ≥0.01 AND veto to those same candidates. No tissue is removed; hypothetical filtering only diagnoses possible harm.

Detector feature functions accept no grade labels, annotation fractions, foreign masks, donor/host IDs or absolute-position features. Physical context uses pairwise distances and is translation/rotation invariant. Ground truth enters evaluation only. The existing artificial right-edge arrangement is retained, however, and can influence which tissue qualifies as physically distant; alternative-placement robustness is not established by this run.

## Actual measured operating points

All rows below are out-of-fold **training** estimates: 72 clean slides and 120 positive-dose cases from 24 benign host slides and 16 reused cancer donor slides. Five nested doses are not independent patients. There are 1,647 injected tile observations. Native controls contain 88 components with any known positive GP3/4/5 tile fraction across 47 unmodified slides; this is not per-component cancer purity. Clean damage uses 61 originally correct slides, and recovery uses 38 induced-error instances.

| Method | Fragment hits /120 | Foreign tiles /1,647 | Clean alerts /72 | Components/clean slide | Native cancer flags /88 | Hypothetical damage /61 | Recovery /38 | Host-weighted component AP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| nn1 | 0 | 0 | 7 | 0.097 | 6 | 4 | 0 | 0.101 |
| nn5 | 0 | 0 | 7 | 0.097 | 7 | 2 | 0 | 0.095 |
| robust_nn5 (primary) | 1 | 1 | 7 | 0.097 | 5 | 3 | 0 | 0.133 |
| background_centroid | 0 | 0 | 6 | 0.097 | 1 | 0 | 0 | 0.093 |
| component_neighbor | 3 | 15 | 7 | 0.139 | 3 | 0 | 0 | 0.143 |
| distant_nn5 | 3 | 7 | 6 | 0.097 | 4 | 1 | 2 | 0.153 |
| cohort_centroid5 | 0 | 0 | 9 | 0.236 | 0 | 0 | 0 | 0.061 |

The cohort method also exceeds the OOF slide-alert budget at 9/72 (12.5%), despite fitting-fold budget compliance. The other rows meet the empirical OOF review-burden targets but detect at most 3/120 fragments. No useful operating point is demonstrated. Native-cancer and hypothetical-damage outcomes remain separate safety measurements rather than being hidden in a composite objective. Historical v1/v2 training selection and these grouped OOF estimates use different estimation procedures; they do not establish a formal improvement or deterioration against one another.

For the primary, the conditional host-cluster bootstrap 95% interval for fragment recall is 0–2.5% (24 hosts), and the clean-alert Wilson 95% interval is 4.79–18.74% (72 slides). Observing 7/72 alerts therefore does not establish a population alert rate below 10%. Its five native-cancer flags affect 5/47 annotation-positive slides (10.64%); hypothetical filtering damages 3/61 initially correct clean predictions (4.92%). All filtering outcomes are hypothetical, not automatic actions. Zero-recall bootstrap intervals collapse to [0,0] for several methods; that is a property of the limited sample and not certainty about population performance.

## Why the new signals still fail

Robust normalization modestly separates central distributions but not the tail needed for low-burden review. On evaluable/mapped controls, native annotated-cancer robust scores have median 1.318 and range −0.648–24.733 (79 component observations), versus foreign-majority median 2.812 and range −1.703–8.343 (140 observations). Native tissue can be substantially more anomalous than the injected donor. The pairwise fraction of foreign scores above native scores is 0.653, with repeated doses/donors; it is descriptive rather than an independent validation AUROC. NN5 alone is approximately 0.526 on that same descriptive comparison. Background-centroid separation is stronger centrally (0.795) but its extreme clean tail still prevents any budgeted foreign hit.

The single primary hit is the 0.5% mixture on host `afe7eb15c8438861ca43f2b20dccf260`: one foreign tile, no baseline decision change, signed influence 0.007994. The historical AND≥0.01 comparator discards it, yielding 0/120 hits. Two-stage review therefore avoids one unnecessary consequence veto, but this is insufficient scientific utility and recovers no induced error. A visual hit is neither evidence of a clinically consequential contaminant nor a reason to delete tissue.

Full tied-score precision/recall curves, nine fold-fitted quantile sensitivity/burden points, raw ranks and influence explanations are saved. Component AP gives every host equal total weight; observed positive prevalence varies by method from approximately 7.3–8.7% because unavailable contexts differ. Precision is specific to this synthetic mixture/component sampling distribution and is not a clinical positive predictive value. Curves show more review burden can surface more fragments, but such points do not replace the fixed operating point.

## Coverage, reuse and limits

Two low-mapping clean slides remain in denominators as review abstentions. One saved clean component has an empty counterfactual and remains unevaluable. Absent distant/background contexts are explicit unavailable scores, not zero anomaly or a benign prediction. Known masks contain no annotated cancer on one GG1 training slide; its slide grade is not substituted for tile labels. Native-versus-foreign plots cover available scores, not all 88 native annotated components.

Cohort references are fitted without held-fold host slides, but 95/120 held-out mixture cases have their exact donor slide in the fitting reference. No donor-truth filter removes it: that would put synthetic source identity inside feature construction. This constrains the cohort-reference interpretation and prevents claims of donor-disjoint generalization; the within-slide primary does not use cohort references. Host-cluster intervals preserve doses but are conditional on fixed reused donors and unknown patient identities. Slide-disjoint folds do not prove patient independence.

No new calibration or final-test predictions were computed. The legacy source-directory index parsed all 120 tiling metadata JSON files to resolve slide IDs; those label-bearing metadata were not completely untouched. NPZ loading and detector analysis were restricted to the 72 training slides. Metadata indexing did not create held-out predictions or supply label values to detector features. Future loaders should resolve requested IDs without indexing every split. The 24 calibration slides are already iterative development in earlier work; the 24 final-test slides remain sealed. RGB components are approximate tissue pieces, synthetic inserted cancer is not naturally occurring foreign tissue, and the zero-shot benign/cancer scorer is an engineering reference rather than a clinically validated detector.

## Execution and reproducibility

CPU Slurm job **23068965 completed 0:0** on `cn034` in 23 seconds (14-second analysis task), peak RSS 442,612 KiB. Requested resources were 2 CPUs, 8 GB, 20 minutes on `bfqi-delta-cpu`/`cpu-interactive`; no GPU. The exact source archive verified 37 files before submission. Original source artifacts and outputs were preserved.

The 120 `oracle_checks` field entries specifically record exact host-feature/coordinate-prefix preservation, saved foreign-mask identity, and frozen top-5% baseline prediction agreement during reconstruction. They are **reconstruction checks**, not a newly rerun full metadata/tile-ID oracle experiment. Historical full S1 oracle recoveries remain unchanged.

- [Predeclared configuration](../configs/panda_detector_v3_train_v1.json).
- [Exact command, source/archive/config/input hashes, output paths and resources](panda_detector_v3_job_23068965.json); [job log](panda_detector_v3_job_23068965.log).
- [All methods, folds, thresholds, full PR/sensitivity metrics and fingerprints](panda_detector_v3_training_v1.json).
- [Per-case OOF metrics and two-stage explanations](panda_detector_v3_metrics_by_case_v1.json); [evaluation-only component ranking observations](panda_detector_v3_ranking_observations_v1.json).
- [Operating points](figures/panda_detector_v3_training_v1/operating_points.png), [recall/burden](figures/panda_detector_v3_training_v1/recall_burden_curves.png), [precision/recall](figures/panda_detector_v3_training_v1/precision_recall.png), [native/foreign overlap](figures/panda_detector_v3_training_v1/native_foreign_overlap.png), [two-stage versus AND](figures/panda_detector_v3_training_v1/two_stage_vs_and.png). Each has PNG/SVG plus checksummed provenance.

```sh
PYTHONPATH=src .venv/bin/python scripts/plot_detector_v3_training.py \
  --report reports/panda_detector_v3_training_v1.json \
  --observations reports/panda_detector_v3_ranking_observations_v1.json \
  --output /tmp/panda-detector-v3-training-figures
```

Five targeted software tests cover real runner integration using temporary artificial fixtures, split filtering, geometry invariance, reference weighting, strict ties, empty/missing contexts, source preservation and separate influence explanation. Fixtures are software evidence only. No new dataset, model or checkpoint was introduced.

Next scientific requirement: validated foreground-piece identities and realistic placement/control experiments on the shared intervention engine, followed by a prospectively selected slide-disjoint development-validation cohort. Existing CONCH-v1 vectors do not yet provide useful low-burden foreignness identification in this setup. No additional GPU inference or acquisition is justified by this detector result alone.
