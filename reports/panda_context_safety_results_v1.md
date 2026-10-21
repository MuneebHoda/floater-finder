# Numeric-context eligibility and native controls: training findings

CPU **23102229 completed 0:0 in 12 seconds**, from pushed source `0340d60`.
All **72 original training slides**, 73 checkpoints and 76 events verify against
the new sealed registry. The audit reused previously sealed JSON only: no image,
array, classifier, encoder, segmentation or score computation. All **336 software
tests passed** before submission, including 21 new artificial-fixture checks.
Raw artifacts remain on Delta; these notes contain bounded aggregates only.

## What the contract does

`assess_context(candidate_tiles, total_tiles, diagnostic_score)` returns numeric
abstention for fewer than six outside comparison tiles or a candidate occupying
more than half the saved tile bag. An abstention retains its old diagnostic score
but withholds a comparison score. Otherwise the result is only a supported numeric
comparison. Both NN5 calculations need six references; this does not establish
score stability. The majority veto is a new conservative engineering candidate,
proposed after the previous training audit and frozen before this accounting.
It is not an independently validated or physical tissue-size threshold.

**All review and foreignness decisions remain null; automatic tissue action is
none.** Null is an abstention, not a negative alert. No review policy was fitted,
accepted or retroactively substituted into old experiments. A numeric eligibility
gate is available to future callers; the historical detectors remain unchanged.

## Coverage and native-cancer controls

| Training observation | Cached RGB membership | Sampled occupied cells |
| --- | ---: | ---: |
| Original components | 389 | 377 |
| NN5 support alone: >=6 outside tiles | 378/389 | 343/377 |
| Conservative numeric eligibility | 325/389 | 316/377 |
| Slides with at least one eligible comparison | 64/72 | 44/72 |
| Slides with none | 8/72 | 28/72 |
| Abstained components | 64/389 | 61/377 |
| Components with <6 comparison tiles | 11 | 34 |
| Components occupying >half the sampled bag | 64 | 61 |

The sparse-context and majority reasons overlap: every sparse-context candidate
is also a majority. Do not add the two reason counts. Relative to NN5 support alone,
the majority veto additionally withholds **53 RGB /27 sampled comparisons**.
These are coverage counts, not sensitivity, specificity or improvement in safety.
Component regroupings are not independent cohorts; the two columns must not be
summed. Patient independence is unverified.

Native annotation is joined only after truth-free gate construction. All inputs
are unmodified tissue, and a mask-positive cancer component is a genuine-tissue
control for a future claim of foreignness. Slide-level grades are not per-tile
truth; annotation-negative components are not automatically benign tissue.

| Native annotated-cancer observation | Cached RGB | Sampled cells |
| --- | ---: | ---: |
| Positive components before gating | 88 | 116 |
| Positive components with full NN5 support | 82/88 | 94/116 |
| Positive components still numerically eligible | 44/88 | 75/116 |
| Unique slides containing eligible positive components | 25 | 19 |
| Positive components abstained | 44/88 | 41/116 |
| Additional positive abstentions from majority veto beyond NN5 | 38 | 19 |
| Old diagnostic score range of eligible positive components | -0.648 to 5.065 | -0.615 to 4.717 |

There are 47 unique annotation-positive training slides under either grouping;
positive/abstained slide groups can overlap. No component has unknown annotation
in this particular training input, but missing-annotation handling is tested and
remains explicit. Genuine positive tissue can still be both numerically supported
and visually unusual. **Remaining eligibility is not a false alert**, and the
withheld controls are not demonstrated prevented harms. No decision or tissue
exclusion was performed. Review-alert rate, foreign-fragment recall and genuine-
tissue prediction damage remain **unmeasured/null**, not zero.

## Topology and comparison uncertainty remain

Among eligible comparisons, **320/325 RGB** and **299/316 sampled** use at least
one tile unassigned in the cached RGB mapping. **79/316** eligible sampled candidates
themselves contain unassigned RGB tiles. These stay unknown; they were neither
assigned to guessed physical pieces nor silently removed from saved scores.
The new gate does not repair the topology disagreements found by the previous
audit or prove that reference tissue is biologically appropriate.

Observed RGB area and occupied tile footprint remain distinct. The majority veto
uses sampled tile occupancy, not measured whole-biopsy area. Both mappings remain
proxies for physical boundaries. No score cutoff, unknown-mapping cutoff, isolation
rule, topology choice, threshold sweep or reference thinning was added here.
The earlier score-sensitivity finding still applies after meeting the NN5 count
requirement. All scores in this study are reused morphology units, not cancer
probabilities or evidence of clinical validity.

## Consequence and next development step

The software now expresses unsupported comparisons explicitly and prevents their
accidental use as negative alerts. It does **not** provide a useful floater detector
or establish that a candidate is safe to remove. The next defensible integration
is a review-only dependence report: preserve the baseline and all tissue, show
influential components with context/mapping uncertainty, and keep foreignness
unset. Any future foreignness policy needs its own versioned development plan
and measured genuine-tissue controls before independent validation. Do not relax
the rejected final-test gate or call the already evaluated fresh 60 pristine.

## Execution and provenance

Account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`, node `cn095`;
2 CPUs, 4 GB, five-minute cap, zero GPUs. Elapsed 12 seconds, Python task 3 seconds,
MaxRSS 70,576 KiB; **0.006667 allocated CPU-hours**. Queue empty after completion.
Local execution is Darwin; shared SSH identity verified as `mhoda` / `dt-login04`.

Source `0340d605acd6bee8ea913d09307a326750cb1a5c` was pushed and separately verified
in a 253-file read-only snapshot. Protocol SHA256:
`9e8a75b0d0a9eb244e840850dd03b6cfb8aa742dec6770b6c9078f9bd5d92871`.
[Full contract, source location, resources and exact submitted command](../docs/panda_context_safety_v1.md).

Remote output:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review/context-safety-v1`

| Preserved artifact | SHA256 |
| --- | --- |
| `run.json` | `36bd034645465fbbc220582abdbca7bc9e20fa7f10d1a69fddf74c3deb81ad9d` |
| `seal.json` | `acbe852f1a5be0f438f11002b5fd2fb76e766c2450950607627dc08416ea5a53` |
| `checkpoints/summary.json` | `3a5686dedfed7caa474b1b71f11a2fb04adc4fe29647318dbb08d837aba8228f` |
| Parent `context-safety-authorization-v1.json` | `3baf39581f5032081388e6441ef42cd941446f55f9d2b7bd54a24ae786a9aaa1` |
| Parent `context-safety-completion-v1.json` | `7bc8726d4fc2ed8ce0bab3d920b3e8b6df0f2ef18d57892c5d2b998f255dc0a4` |

Independent saved-JSON inspection verified every eligibility reason, old score,
withheld comparison, annotation join, physical-area field, aggregate and hash
chain. All 253 source files, four pinned inputs, original protocol and 33 legacy
source hashes remain verified; `main` is unchanged and original final output
absent. The old audit is read without opening its writer lock and is reverified
before sealing. TCGA, original120/fresh60, prior outputs and failed/rejected
protocols are preserved. No GPU, downloads, new fitting, original test prediction,
extra job or retry occurred. This bounded development scope is complete.

Read-only next command:

```sh
cat reports/panda_context_safety_results_v1.md
```
