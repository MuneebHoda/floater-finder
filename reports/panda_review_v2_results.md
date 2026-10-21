# Detector v2: ranked review remains unsupported

October 20, 2026. This is a new, separately preregistered **development investigation**, not a revision of rejected v1. It reuses the saved measurements from 96 unmodified PANDA training/calibration slides and 160 positive-dose S1 mixtures. No acquisition, tiling, WSI segmentation, GPU encoding, original S1 draws or individual component-exclusion jobs were repeated. The 24 final-test slides remain unscored. Calibration outcomes were already known from v1: every v2 calibration result below is **iterative development, not independent validation**.

**Outcome:** a fixed combined rank improves training fragment recall from v1's 5/120 to 22/120, but still misses the preregistered 20% recall and 25% recovery targets on training. On known calibration, both v1 and v2 detect **0/40** fragments. Ranking one component on every slide increases recall at an unacceptable review burden and flags genuine native cancer. This is not a meaningfully validated detector improvement and does not authorize final testing.

## Design and execution

The committed design is [development protocol](../docs/panda_review_v2_development.md) and [configuration](../configs/panda_review_v2_development.json). Source was committed **before execution** at `668d9b8c4e3e8aa300bda6ff15e416c601c2e024`. An exact Git archive was staged to a separate Delta release; all 367 source files matched their hashes. CPU job **23067454** completed `0:0` on `cn095` in 23 seconds (14-second analysis task, peak RSS 118,600 KiB), using 2 CPUs, 4 GB, a 10-minute limit, `bfqi-delta-cpu` / `cpu-interactive`. No GPU was requested.

Five fixed, untrained scores use clean-training empirical percentiles: visual anomaly; **absolute margin influence**; physical spatial rank (smallness and isolation); equal visual/relevance rank; and a fixed weighted average (visual 0.5, absolute influence 0.25, smallness/isolation 0.125 each). Absolute influence is prediction relevance, not evidence of foreignness or a binary decision change. The signed quantity is the frozen benign/cancer baseline margin minus the component-excluded margin; positive values mean the component supports the cancer margin relative to its exclusion.

For each score, four clean-training slide-maximum quantiles and caps of one/three components, plus reject-all, give nine candidates (45 across five strategies). Threshold exceedance is strict. A tied group crossing the cap abstains; low-mapping slides and empty component exclusions remain unevaluable. Selection uses training only, retaining the confirmed ≤10% unmodified-slide alert rate and ≤0.5 components/slide, plus the preregistered native-cancer and hypothetical-damage gates. All candidate metrics, including failures, are retained.

The detector feature boundary excludes injection truth, native annotations, slide grades, identifying donor/host metadata, component coordinates and absolute placement. Annotation/injection truth enters evaluation and training safety selection only. Tests verify feature blindness, calibration-invariant normalization/selection, signed versus absolute influence, ties, split guards and mixed-component auditing. No learned classifier was fitted.

## Why the old AND policy failed

| Existing v1 condition on a donor-bearing component | Train mixtures /120 | Known-calibration mixtures /40 |
|---|---:|---:|
| Visual threshold alone | 16 | 5 |
| Signed influence ≥0.01 alone | 61 | 12 |
| Area/isolation alone | 103 | 32 |
| Visual **and** influence | 5 | 0 |
| Every v1 condition | 5 | 0 |

The five visual-pass calibration mixtures are the **five nested doses of one host**, `f88e932503d0e42467edb710bb8b9c46`, not five independent slides. Four have exactly zero signed influence; the 10% mixture has influence 0.000558, still far below 0.01. None changes its prediction upon exclusion. The 10% component also exceeds v1's 0.25 mm² size limit. Thus the same components do not supply both visual inconsistency and consequential model influence.

Among 40 calibration donor-bearing component observations, signed influence is negative in 4, zero in 11 and positive in 25; only 12 reach 0.01. Among 26 native annotated-cancer components on unmodified calibration slides, 8 are negative, 4 zero and 14 positive. One native annotated-cancer component changes the binary prediction upon exclusion. A native annotated-cancer component contains at least one mapped native tile with a positive known GP3/4/5 mask fraction; this is not a claim that every tile or pixel in that component is cancer. The two populations overlap: median visual anomaly is 0.165 for donor-bearing versus 0.136 for native annotated cancer, with native cancer reaching 0.460 and donor components reaching 0.279. Native cancer can be visually unusual and decisive legitimately.

## Component construction, size and artificial placement

Calibration has one donor-bearing observed component in every one of 40 mixtures, with observed areas ranging from 0.0114 to 0.5280 mm² (median 0.0985). Training has one in 107 mixtures, two in ten, three in two, and seven in one. A four-connected tile fragment can therefore split under the observed RGB/pyramid foreground rule. No component has **both mapped donor and mapped host tiles** in these stresses; this does not establish pixel-level purity or verified physical tissue boundaries. Unmapped native foreground can still occur in a component. Five of 607 donor-tile observations in calibration and 25/1,647 in training are unassigned by the dominant-component mapping rule and are retained as misses.

Every positive mixture (120/120 train; 40/40 calibration) contains a donor-bearing component at or beyond the unmodified host's observed rightmost foreground extent. This reflects the existing **artificial translated right-edge placement**, not a property of natural contaminants. Absolute coordinates are excluded from ranking, but isolation and size can still benefit from that construction. No alternative-placement robustness or natural-floater performance is established. The lack of co-mapped native tiles shows that component merging is not the observed primary failure in this particular engineered setup.

## Train-selected operating points

| Strategy | Selected threshold; cap | Train fragment hits /120 | Train clean alerts /72 | Calibration hits /40 | Calibration clean alerts /24 | Calibration native-cancer components flagged /26 | Calibration clean damage /20 |
|---|---|---:|---:|---:|---:|---:|---:|
| Visual rank | 1.0; 1 (reject-all) | 0 | 0 | 0 | 0 | 0 | 0 |
| Absolute-influence rank | 1.0; 1 (reject-all) | 0 | 0 | 0 | 0 | 0 | 0 |
| Spatial rank | 0.8756830601092896; 1 | 2 | 7 | 0 | 5 | 0 | 0 |
| Visual + relevance | 1.0; 1 (reject-all) | 0 | 0 | 0 | 0 | 0 | 0 |
| Combined average **(train-selected primary)** | 0.806181693989071; 3 | 22 | 3 | 0 | 1 | 1 | 0 |

The primary's training fragment recall is 18.33%; foreign-tile recall is 139/1,647 (8.44%), and recovery is 6/38 newly induced error instances (15.79%). Its 3/72 clean alerts yield 0.0417 components/slide. It flags 2/88 native annotated-cancer components and hypothetically damages 3/61 originally correct clean predictions (4.92%). It passes the engineering burden/harm constraints narrowly but **fails both utility gates before calibration**.

On calibration, primary burden is 1/24 slides and 0.0417 components/slide; the alert is a native annotated-cancer component (1/26 components, on 1/15 slides with positive native cancer annotation). There is no induced-error recovery: 0/8 instances across two affected host slides. The primary also flags one native-only component in an injected mixture without hitting the donor. No tissue is removed by this software; all filtering outcomes are hypothetical.

At every positive calibration dose (0.5%, 1%, 2%, 5%, 10%), each selected v2 strategy has 0/8 fragment hits. The original-correct low-dose error denominators remain **five benign hosts per dose**, with induced errors 1, 1, 2, 2, 2 respectively. The three initially incorrect benign hosts are excluded from newly induced errors. Recovery denominators of 8 across all doses are repeated error instances, not eight independent patients.

## What happens if review is offered on every slide?

These are **unbudgeted top-one diagnostics**, not deployable alerts or selected operating points.

| Ranking | Calibration fragment hits /40 | Clean slides offered review /24 | Mean components/clean slide | Native annotated-cancer components flagged /26 | Hypothetical clean damage /20 |
|---|---:|---:|---:|---:|---:|
| Visual | 13 | 23 | 0.958 | 11 | 0 |
| Absolute influence | 6 | 24 | 1.000 | 15 | 2 |
| Spatial | 8 | 24 | 1.000 | 5 | 0 |
| Visual + relevance | 21 | 24 | 1.000 | 14 | 2 |
| Combined average | 19 | 24 | 1.000 | 11 | 0 |

Ranking helps surface some engineered fragments if almost every slide is reviewed. The apparent 52.5% recall of visual-plus-relevance comes with 100% clean-slide alerts, twice the component budget, 14 native-cancer components flagged and 2/20 originally correct predictions damaged by hypothetical filtering. It does not satisfy the task's review policy. The component cap does not itself control slide-level alert burden.

## Matched controls and uncertainty

Every selected method has 20 area-bin- and burden-matched random draws. For the primary, training matched mean fragment recall is 11.96% versus its 18.33%; mean new-error recovery is 12.76% versus 15.79%. **23/36 requested training component matches are forced singleton pools**, so this comparison provides limited independent ranking evidence. Calibration primary and matched controls both detect zero fragments; one of two requested calibration matches is forced. Reject-all methods also have zero-burden controls and provide no evidence of superiority. Spatial selected controls average 1.25% calibration fragment recall while the method gets zero; its 5/24 clean alerts already fail the confirmed budget.

Primary training fragment recall has a conditional unique-host bootstrap 95% interval of 7.5–30.83% (24 hosts, fixed reused donors); recovery has interval 0–37.84% over the 14 hosts that experience induced errors. Calibration primary fragment recall is zero in every resample of its eight host slides; this degenerate bootstrap interval must not be interpreted as certainty of zero population performance. Primary calibration clean alerts 1/24 have a Wilson 95% interval of approximately 0.74–20.24%. Thus a small observed alert count does not establish a population rate below 10%.

There are 24 distinct training hosts and 16 donor slides; calibration has eight distinct hosts and five reused donor slides. Nested doses, component rows and random draws are not independent patients. Patient identifiers are unavailable; distinct slides do not prove distinct patients. Quantile normalization also weights components rather than giving equal weight to slides. All uncertainty is exploratory and conditional on these source/placement choices, with no clinical validity claim or confirmatory significance test.

## Reproduction and next scientific gate

- [Exact job, source archive and artifact hashes](panda_review_v2_job_23067454.json), [job log](panda_review_v2_job_23067454.log).
- [All candidates, normalized training references, metrics and gates](panda_review_v2_results.json).
- [Per-case selected-strategy metrics](panda_review_v2_metrics_by_case.json) and [evaluation-only component decomposition](panda_review_v2_decomposition_by_component.json).
- [Trade-off figure](figures/panda_review_v2/ranked_review_tradeoff.png), [signal distributions](figures/panda_review_v2/signal_distributions.png), [v1 condition intersections](figures/panda_review_v2/v1_failure_intersections.png). PNG/SVG and provenance accompany each figure set.

Recreate the figures without model execution:

```sh
PYTHONPATH=src .venv/bin/python scripts/plot_panda_review_v2.py \
  --results reports/panda_review_v2_results.json \
  --components reports/panda_review_v2_decomposition_by_component.json \
  --output /tmp/panda-review-v2-figures
```

No useful train/calibration operating point is supported by this v2 investigation. **Final testing remains blocked**; the frozen rejected v1 protocol and completed preflight are unchanged. The submission can accurately demonstrate a verified CONCH pipeline, vulnerability stresses, genuine-cancer safety counterexamples and the measured review trade-off. Stronger foreignness claims need better independent development evidence, realistic placement/contaminants and expert-validated piece boundaries, with separate scope/resource approval before new data or GPU work. S2 grade scoring is a separate experiment; this saved benign/cancer v2 analysis does not establish S2 detector performance.
