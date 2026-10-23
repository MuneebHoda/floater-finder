# S2 development results — October 20, 2026

**The preselected primary mean-pooling model showed no newly induced low-to-high errors on the eight calibration hosts at any tested dose.** Secondary top-pooling models were more sensitive, but already misclassified most clean low-grade calibration slides. These are binary zero-shot model changes under synthetic embedding contamination, not clinical Gleason Grade Group upgrades. Nothing here validates a foreign-tissue detector.

CPU Slurm job **23067396** completed `0:0` in 19 seconds (task 10 seconds, maximum RSS 360,004 KiB). It used 2 CPUs, 4 GB, a 10-minute limit, `bfqi-delta-cpu` account/QoS and `cpu-interactive`. No GPU inference, downloads or final-test evaluation occurred. The exact source was committed as **35e0a8dae57e22808420b45ae040fc2f8c3710a5** before execution. The source archive SHA256 was `5e6938eaaa45d23871085f6cb94e82b25d12e80d2fba15bbd30da09570a65974`; all 361 source files were verified on Delta. [Submission and retrieval provenance](panda_s2_submission_v1.json) records the exact command, paths and artifact hashes.

## Clean audit and primary selection

The original prompts, CONCH v1 checkpoint, cached normalized embeddings, argmax threshold/tie rule and classwise pooling are unchanged. Checkpoint SHA256 is `40a9644b9ba0e83a74576e0a5e5f7313599fa9c9cdaf3c20f8a3e271b0e9ae7c`; four-class text fingerprint is `1af114595a1aa2657102590b31ab480c431b6b61e87882230791b98609e6ce46`; fixed prompt-file SHA256 is `9767f2ddb12f8c20ef905ae65db1796e0cf001a078e8179816022aff6317180a`. S2 uses the low/high pair from those cached four-class text embeddings. Mean pooling was selected **before inspecting any S2 contamination outcome**, using the existing clean evidence. The runner recovered every existing low/high clean prediction and score exactly before its first contaminated prediction and saved that audit separately.

| Pooling | Training correct / 48 | Training low / 24; high / 24 | Calibration correct / 16 | Calibration low / 8; high / 8 |
| --- | ---: | --- | ---: | --- |
| **Mean, primary** | **35** | **22; 13** | **12** | **8; 4** |
| Top 1% | 29 | 7; 22 | 10 | 2; 8 |
| Top 5% | 30 | 8; 22 | 11 | 3; 8 |

These balanced cohorts make accuracy equal to balanced accuracy. Mean calibration accuracy is 75%, with only 50% high-grade recall. The baseline supports an engineering stress test, not reliable clinical grading. Calibration has previously been examined and is development evidence, not a fresh independent validation cohort.

## Design, coverage and preservation

There are **32 distinct ISUP1 hosts** (24 training, eight calibration), **37 distinct donor slides**, and **55 distinct slides in their union**. Some low-grade donors are also hosts in other trials. Different slide IDs do not establish different patients; patient identity remains unknown. All pairings stay within the same split and known same-patient pairs are prohibited.

The completed run has **760 trial records: 632 positive mixtures and 128 zero-dose references**. The zero-dose entries repeat the original hosts under four condition labels; they are not 128 independent clean slides. All **760/760 oracle removals exactly restore original arrays, order, metadata, raw low/high scores and predictions**. Donor indices are unique, four-connected on the verified sampled tile grid and nested across increasing doses. No missing cells are bridged. Post-execution checks verified every saved native-pattern constraint and every nested index prefix.

Doses are 0, 0.5, 1, 2, 5 and 10% foreign tiles divided by **original host** tile count, rounded upward. Raw records preserve requested/realized dose, donor tile IDs/indices, original mask fractions, physical footprint/annotated areas, source hashes, translated coordinates through the recorded translation plus immutable native coordinates, and all three model outputs. Original slide arrays and baseline predictions are preserved. Right-edge translation is an artificial layout, not evidence of naturally occurring floaters.

| Condition | Split | Hosts | Donor slides | Positive mixtures | Chosen component capacity range |
| --- | --- | ---: | ---: | ---: | --- |
| High-slide GP4/5+ | Train | 24 | 14 | 120 | 36–327 |
| High-slide GP4/5+ | Calibration | 8 | 4 | 40 | 59–105 |
| Same-grade GP3+, no GP4/5 | Train | 24 | 11 | 120 | 37–316 |
| Same-grade GP3+, no GP4/5 | Calibration | 8 | 3 | 40 | 42–216 |
| High-slide GP4+, no GP5 | Train | 24 | 8 | 120 | 54–327 |
| High-slide GP4+, no GP5 | Calibration | 8 | 3 | 40 | 59–105 |
| High-slide GP5+ | Train | 24 | 7 | 120 | 15–186 |
| High-slide GP5+ | Calibration | 8 | 1 | 32 | 37–37 |

The main donor criterion is native GP4+5 fraction ≥0.10 in **every selected tile**. Same-grade controls require native GP3≥0.10 and GP4=GP5=0. The GP4-positive/no-GP5 control permits GP3; it does not assert pure GP4 tissue. GP5-positive controls permit GP3/4. The actual selected GP4-positive/no-GP5 tiles in this run happened to have GP3=0. Composition conditions can overlap, reuse donors and select different fragments; they are matched on host and dose, not on all donor characteristics.

**Eight exclusions** are all calibration GP5-positive 10% trials: the only eligible chosen donor component has 37 unique four-connected tiles, but hosts require 40–52. The 10% GP5 calibration result is **unavailable (0 evaluable hosts), not a zero error rate**. All primary GP4/5 and same-grade/GP4 control doses cover all 32 hosts. The corrupt/unavailable calibration mask remains unknown and is excluded from native-pattern donor selection; it is not repaired or treated as negative.

## Primary GP4/5 contamination results

| Dose (%) | Mean train newly induced / originally correct | Mean calibration newly induced / originally correct | Top 1% calibration | Top 5% calibration |
| ---: | --- | --- | --- | --- |
| 0 | 0/22 | 0/8 | 0/2 | 0/3 |
| 0.5 | 0/22 | 0/8 | 0/2 | 0/3 |
| 1 | 0/22 | 0/8 | 1/2 | 0/3 |
| 2 | 0/22 | 0/8 | 2/2 | 2/3 |
| 5 | 0/22 | 0/8 | 2/2 | 3/3 |
| 10 | 1/22 | 0/8 | 2/2 | 3/3 |

The two initially-high training hosts under mean pooling, six initially-high calibration hosts under top 1%, and five initially-high calibration hosts under top 5% are excluded from **new-error denominators**, while retained in prediction-change reporting. For the primary GP4/5 condition every recorded label change is low→high; there are no high→low reversals. Across doses, the primary training effect is one instance on one host at 10%; calibration has none. Repeated doses must not be added as independent hosts.

At 10%, the calibration mean high-minus-low cosine margin rises by an average **0.005669**, without crossing the class boundary in any host. Top-1% and top-5% margins rise by **0.017426** and **0.022966** respectively. The secondary models' larger flip rates accompany much poorer clean low-grade specificity; the primary is not changed after seeing that contrast.

Per-dose 95% Wilson intervals use unique originally correct host slides: mean 0/8 is **0–32.4%**, top-1% 2/2 is **34.2–100%**, and top-5% 3/3 is **43.9–100%**. These wide conditional intervals do not account for reused donors or unknown patient clustering. No clinical or population-level inference is made. [Structured per-dose results and uncertainty](panda_s2_development_v1/analysis.json) retain all denominators.

## Controls and native cancer safety

At 10% mean pooling, training newly induced errors are 1/22 for GP4/5+, 0/22 for same-grade GP3+, 0/22 for GP4-positive/no-GP5, and 2/22 for GP5-positive. Calibration mean has 0/8 for GP4/5+, same-grade and GP4/no-GP5; GP5-positive at 10% is unavailable. These are different selected donor fragments with reused donors, so differences do not isolate a causal effect of pattern composition.

The same-grade calibration GP3 control under top-5% induces **1/3** new low→high errors at 2%, 5% and 10%. At 10% it also reverses one initially-high prediction to low, yielding **two prediction changes but only one new error**. Thus top-pooling instability is not specific evidence of high-grade contamination. Top-1% same-grade calibration controls induce 0/2 at all doses. Full training/calibration pooling comparisons, score shifts and reversal counts are preserved in [summary.json](panda_s2_development_v1/summary.json).

Annotation-guided native GP4/5 components provide a separate genuine-cancer control. There are **428 components across 24 training high-grade slides** and **122 across seven calibration high-grade slides**; all 550 exclusions leave a nonempty counterfactual. Mean-pooling native exclusion changes high→low in **six training components on six slides and two calibration components on two slides**. Top-1% has no native changes; top-5% has one training change and no calibration changes. These are native annotation-defined fragments on sampled cells, not observed-RGB whole pieces or blinded detector flags. Genuine annotated high-grade tissue can legitimately be decisive and must not be called foreign or automatically discarded.

As an annotation-informed representation diagnostic, the same 10% GP4/5 donor fragment is compared with its original donor context and with the recipient host context using median nearest-five cosine distance. It is farther from the host in **23/24 training and 8/8 calibration cases**. Median distances are 0.10705 host versus 0.06173 original context in training, and 0.11921 versus 0.09256 in calibration. Native genuine components have median native-context distances 0.07168 and 0.08808 respectively. Component sizes/context sizes are not matched and distributions overlap. These diagnostics provide no calibrated foreignness threshold, alert policy, sensitivity or specificity; injection labels and mask fractions are evaluation metadata, not detector features.

## Artifacts, reproduction and next gate

- [Frozen protocol](../configs/panda_s2_development_v1.json) and [method](../docs/panda_s2_development_v1.md).
- [Full raw trial scores, annotation fractions and provenance](panda_s2_development_v1/trials.json), [native safety](panda_s2_development_v1/native_safety.json), [donor audit](panda_s2_development_v1/donor_audit.json), [pairings](panda_s2_development_v1/pairings.json), [all exclusions](panda_s2_development_v1/exclusions.json), [original completion hashes](panda_s2_development_v1/completion.json).
- [Measured-result figure](figures/panda_s2_development_23067396/s2_development.png) with [SVG](figures/panda_s2_development_23067396/s2_development.svg) and [figure provenance](figures/panda_s2_development_23067396/provenance.json).

Reproduce the figure locally without scoring any slide:

```sh
PYTHONPATH=src .venv/bin/python scripts/plot_panda_s2.py \
  --input-dir reports/panda_s2_development_v1 \
  --output-dir results/panda/s2_figure_reproduction
```

Software verification includes six S2 fixture tests covering native label alignment, pattern-specific controls, missing masks, no gap bridging, development/test separation, original-host preservation and exact oracle recovery, correct new-error/reversal denominators, empty native counterfactuals and a full fixture run that refuses baseline drift. Fixtures are software checks, never PANDA performance evidence. The frozen runtime used the first five tests; the sixth only extends local regression coverage.

The independently held-out 24 slides remain unscored. S2 establishes a bounded, reproducible stress-test implementation and a **negative primary calibration outcome**, alongside sensitive but poorly specific secondary scorers and genuine-cancer dependence. It does not satisfy a detector-readiness or clinical-grading gate and does not authorize the rejected v1 final job. A future final evaluation requires a new scientifically justified frozen protocol and explicit authorization.
