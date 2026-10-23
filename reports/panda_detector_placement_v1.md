# Paired-placement detector audit — CPU 23069409

The frozen primary `robust_nn5` detects **0/607 foreign-fragment instances**
(0/10,610 foreign-tile observations) and recovers **0/39 newly induced errors**.
It raises no alerts on four clean anchors or 218 native shams. This is failure to
detect the tested interventions, not evidence of an effective low-burden policy.
All three addition placements also yield zero hits on the common eligible pairs.
No thresholds, reference folds, scorers or eligibility were changed after outcomes.

## Execution and scope

Source/protocol were committed as **bbc2845875c8ff980a20d2c7bf9123ed801afc99**
before new detector scores. CPU job **23069409 completed 0:0** on `cn034` in
**271 seconds**, requesting two CPUs, 8 GB and 20 minutes on
`bfqi-delta-cpu` account/QoS / `cpu-interactive`. Allocated CPU time was
**0.15056 CPU-hours**; Python MaxRSS was **1,319,304 KiB**. There was no GPU use.
The exact submitted command, runtime/input/output locations, source archive and
result archive hashes are in the [execution receipt](panda_detector_placement_v1/execution.json).

The source snapshot verified all 207 archived files. The completed result archive
and sealed registry verified **1,657 checkpoints /1,660 events**; external raw
outputs also match their registered hashes. All 825 reconstructed positive-dose
slides match the original complete artifact identities. Original-state restoration
and saved clean/contaminated predictions pass the reconstruction checks. These
are acceptance checks of saved interventions, not new donor draws or a repeat of
the historical full oracle study. All 1,499 used PNG exports match encoding receipts.

The audit reuses 825 previously eligible positive-dose interventions: **607
foreign and 218 native shams**, on four training host slides (two S1 benign, two
S2 GG1), 21 foreign donor slides and 24 unique source slides across roles.
Patient identity/independence is unverified. The 192 zero-dose instances refer to
the four clean anchors and are not extra clean observations. All 327 historical
geometry exclusions remain excluded. The numeric validator fix and its exact
floating-point counterexample are [audited separately](../docs/research_geometry_numeric_audit_v1.md).

Only the strict training loader opens saved slide artifacts. No new WSI processing,
acquisition, encoding, training, known-calibration predictions or final-test
predictions occurred. The original 120-slide/50,729-vector corpus, historical
reports and rejected final-test protocol remain unchanged.

## Frozen method and component interpretation

The [preregistered mapping/analysis plan](../docs/panda_detector_placement_v1.md)
and [configuration](../configs/panda_detector_placement_v1.json) reuse all 35 old
method/fold threshold records, strict score-above-threshold comparisons and
host-excluded fitting references. Reference centroids give one vote per slide;
503/607 foreign instances reuse a donor included in that fold's reference set.
This is not donor-disjoint validation.

Addition topology uses complete cached level-2 host RGB foreground plus actual
saved PNG foreground at recorded placement, with no masks/foreign labels in
mapping or detector inputs. Replacement uses **native host component carriers**;
it is not observation of a newly separate donor piece. Influence explains visual
flags without vetoing them. S1 retains exact historical CONCH cancer top-5%
pooling; S2 retains the frozen low/high linear head fitted on training hosts.
Cosine-margin and logit influences remain separate. S2 is resubstitution evidence.

All four clean component membership sets match the historical measurements.
All mappings/pair definitions were checkpointed before the first feature record
(event 828). There is no mapping-fraction abstention: the minimum across all cases
is 0.95714, above the frozen 0.9 floor. Unmapped foreign tiles remain misses.
All evaluation arrays have known saved mask annotations and follow the vector's
actual source after replacement or native shams.

| Mapping view | Instances, including shams | Unmapped foreign tile observations | Pure-foreign component observations | Mixed native/foreign component observations |
| --- | ---: | ---: | ---: | ---: |
| Clean anchors | 4 | 0/0 | 0 | 0 |
| Append | 288 | 56/3,126 | 236 | 0 |
| Near tissue | 120 | 48/2,192 | 112 | 0 |
| Native replacement carriers | 288 | 16/3,126 | 10 | 218 |
| Within-region context | 129 | 49/2,166 | 112 | 0 |

These are component/measurement observations with repeated bags, not independent
pieces or patients. No exclusion empties the bag in this restricted subset;
this does not resolve the prior six-of-24 topology limitation in other slides.

## Primary results by task and placement

These rows pool the six preregistered doses only for compact display. Complete
dose/condition strata, denominators and conditional host-bootstrap intervals are
in the [machine-readable summary](panda_detector_placement_v1/summary.json).
Every foreign instance here has an originally correct clean host prediction;
there are no initially incorrect hosts in this restricted four-host subset.

| Task / donor condition | Placement | Fragment hits /instances | Foreign tile hits /observations | New errors /originally correct instances | Recovered /new errors |
| --- | --- | ---: | ---: | ---: | ---: |
| S1 cancer | Append | 0/72 | 0/858 | 10/72 | 0/10 |
| S1 cancer | Near | 0/33 | 0/677 | 9/33 | 0/9 |
| S1 cancer | Replacement carriers | 0/72 | 0/858 | 11/72 | 0/11 |
| S1 cancer | Context | 0/42 | 0/657 | 9/42 | 0/9 |
| S2 GP4/5 | Append | 0/72 | 0/1,134 | 0/72 | NA: zero new errors |
| S2 GP4/5 | Near | 0/30 | 0/844 | 0/30 | NA |
| S2 GP4/5 | Replacement carriers | 0/72 | 0/1,134 | 0/72 | NA |
| S2 GP4/5 | Context | 0/24 | 0/785 | 0/24 | NA |
| S2 same-grade GP3 | Append | 0/72 | 0/1,134 | 0/72 | NA |
| S2 same-grade GP3 | Near | 0/23 | 0/671 | 0/23 | NA |
| S2 same-grade GP3 | Replacement carriers | 0/72 | 0/1,134 | 0/72 | NA |
| S2 same-grade GP3 | Context | 0/23 | 0/724 | 0/23 | NA |

The 39 S1 induced-error instances repeat two benign host slides across donors,
seeds, doses and modes; they are not 39 independent errors/patients. Zero S2
label changes do not establish resistance of a clinical grading system.

The primary has **0/4 clean-anchor alerts**, zero components per anchor, **0/3
genuine annotated-cancer component flags** across the two GG1 clean hosts, and
0/4 hypothetical clean-prediction damage. Native shams have **0/218 alerts** and
0/218 damage among originally correct sham instances. Four anchors cannot verify
the population 10% alert target; retain historical 72-slide cross-fit burden as
prior development evidence. All-zero conditional bootstrap intervals are
degenerate and do not bound population recall or establish safety.

## Matched placements and alternative methods

There are **88 complete append/near/context triplets**, fixed from geometry
eligibility before scores: 20 S1 foreign, 22 S2 GP4/5 foreign, 17 S2 same-grade
foreign and 29 native-sham groups. Thus each placement has **59 matched foreign
instances**, including 35 at 10% dose. The primary detects **0/59** fragments and
**0/1,874** foreign-tile observations in each mode.
Dose/condition strata and paired numerator/denominator/host counts are retained;
replacement is not mixed into these triplets. Geometry exclusions limit the
paired subset. Simultaneous topology/context changes do not isolate a causal
distance effect, and the present zero detections cannot establish a transfer gap.

| Frozen method | Foreign fragment hits /607 | Foreign tile hits /10,610 | Clean alerts /4 | Native-sham alerts /218 | Hypothetical native-sham damage /218 |
| --- | ---: | ---: | ---: | ---: | ---: |
| NN1 | 0 | 0 | 0 | 0 | 0 |
| NN5 | 0 | 0 | 0 | 0 | 0 |
| **Robust NN5 primary** | **0** | **0** | **0** | **0** | **0** |
| Background centroid | 0 | 0 | 0 | 0 | 0 |
| Component neighbor | 3 | 6 | 0 | 0 | 0 |
| Distant NN5 | 0 | 0 | 0 | 5 | 3 |
| Cohort centroid5 | 0 | 0 | 0 | 0 | 0 |

Component-neighbor's three hits are two S1 append cases at 0.25%/0.5% on one
host and one S1 replacement-carrier case at 10% on the other. None is a newly
induced-error recovery. The two append cases have no common eligible triplet;
do not describe their missing near/context comparisons as detector failures.
All seven methods have zero fragment hits in the common 59-foreign triplets.

Distant NN5 alerts on **80/607 foreign-containing instances**, flags **zero
foreign tiles**, and instead flags **26,580 repeated native-tile observations**
across foreign instances and shams. Its five native-sham alerts, all on one benign
host, produce three hypothetical benign-to-cancer prediction errors. No native
annotated-cancer component is flagged in this subset, which has only three such
clean components and no unmodified high-grade hosts. Zero new cancer-component
flags does not overturn the earlier v3 finding of five flags among 88 native
cancer components. These native-tissue findings are adverse controls; no tissue
was actually removed. All alternatives recover zero induced errors. There is no
outcome-guided switch away from the primary.

## Verification and next boundary

**272 tests pass** with warnings treated as errors. New artificial tests cover
RGB contact/background gaps, native carriers, truth-blind inputs, coordinate
invariance, absent context, empty exclusions, strict threshold ties, source-
following annotations, genuine positive regions, induced-error denominators,
paired dose strata and explicit sham burden/harm denominators. Fixtures are
software evidence only. Main, all 33 frozen historical source hashes, the rejected
protocol hash and presentation/submission files are unchanged.

The result archive includes every raw component score, physical geometry,
counterfactual, annotation array and foreign mask; its complete file hash list is
in the execution receipt. A verified local mirror is under
`results/panda/detector_placement_v1_23069409/`. Versioned committed
[case metrics](panda_detector_placement_v1/metrics_by_case.json),
[pairing/PNG identities](panda_detector_placement_v1/eligibility.json) and
[registry receipt](panda_detector_placement_v1/registry.json) preserve all methods.

No useful floater review policy or final-test readiness is established. Freeze
and independently validate the predictive baseline before a disease-performance
claim; do not spend the sealed final set on this failed detector. The existing
[fresh-cohort proposal](../docs/panda_fresh_validation_v1.md) remains metadata
only, with new acquisition/encoding behind explicit scope/resource approval.
Fixed-membership context ablations and actual pixel-composite encoding remain
unexecuted. No additional job is necessary to read the completed audit.

Exact next command from this checkout, for read-only hash verification:

```sh
PYTHONPATH=src .venv/bin/python scripts/research_status.py results/panda/detector_placement_v1_23069409 --summary
```
