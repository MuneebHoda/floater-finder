# Original-training topology and native-context findings

CPU **23101968 completed 0:0 in 27 seconds** on the original **72 training slides**.
It reused cached RGB membership and morphology scores, computed new sampled-grid
crosswalks and bounded reference-context diagnostics, and retained **2160 planned
context records**. All 73 checkpoints /76 registry events verify against their
hash chain and seal. No classification prediction, threshold fitting, new policy,
WSI/PNG read, GPU or download occurred. All payloads/raw records stay on Delta.
Patient independence remains unverified; distinct slide IDs are not verified
different patients.

## Topology correspondence

| Observation on original training slides | Count |
| --- | --- |
| A sampled component spans more than one cached RGB piece | 60/72 slides |
| A cached RGB piece spans multiple sampled components | 21/72 slides |
| At least one saved tile is unassigned in the RGB map | 70/72 slides |
| Below the old 90% RGB mapping-coverage gate | 2/72 slides |
| Largest RGB mapped candidate exceeds half the saved bag | 64/72 slides |
| Largest sampled candidate exceeds half the saved bag | 61/72 slides |

The first two groups overlap; their counts must not be added as distinct slides.
These are disagreements between two proxies. Cached RGB segmentation is not
pathologist-confirmed physical tissue identity; sampled-cell adjacency is not a
verified biopsy-piece boundary. Missing RGB assignments stay unknown, with no
morphological bridging or guessed reassignment. Different mapped tiles/pieces
also prevent comparing RGB and sampled positive-component counts as new cases.

There are **389 cached RGB components** and **377 sampled components**. The latter
count alone obscures large per-slide differences: sampled components cover the
entire bag on 28 slides, whereas only one RGB exclusion removes all saved tiles.
A sole RGB-mapped component can leave unassigned tiles behind; lower empty-exclusion
counts do not establish better physical topology or usable independent context.

| Remaining sampled tiles outside candidate | Cached RGB components | Sampled components |
| --- | ---: | ---: |
| 0: empty exclusion /undefined visual score | 1 | 28 |
| 1: robust score undefined | 5 | 3 |
| 2–5: partial NN5 reference support | 5 | 3 |
| >=6: both neighbor calculations can use five neighbors | 378 | 343 |

Every component with fewer than six remaining tiles is a majority of its sampled
bag. Of the partial-support components, 4/5 RGB and 2/3 sampled components contain
native cancer annotation. Their robust score ranges are 2.75–24.73 and 11.33–14.87
respectively. Native positive tissue can therefore receive large anomaly scores.
Even full-neighbor support does not solve this: maximum native scores are 15.59
RGB and 16.22 sampled. Neighbor-count sufficiency is not calibrated foreignness.

The mappings contain 88 versus 116 native annotation-positive components; this is
one tissue cohort regrouped by two proxies. No component has unknown annotation
in these training inputs. Native annotations enter only after feature construction
for control accounting, not candidate selection or anomaly scoring. Occupied tile
footprint and cached observed RGB area remain separate fields with different meanings.

## Reference-context sensitivity

One largest geometry-defined component per slide/topology remains fixed while
nested subsets of outside tiles provide comparison context. Five target sizes
and three seeds produce 2160 planned records: **1347 reduced-context records,
24 full-context score reuses and 789 unavailable-size exclusions**. Exclusions
retain unknown realized support and score. Duplicate subsets are identified;
seed repeats are not independent slides or patients. No native tissue is edited
or removed, and no classifier decision is recomputed.

Availability changes with context size. RGB has 66/63/61/48/39 eligible slides at
2/5/6/16/32 outside tiles; sampled has 41/39/38/31/31. The main within-topology
comparison below fixes the cohort to the **39 RGB** or **31 sampled** slides with
at least 32 available context tiles. The two topology cohorts themselves differ;
this is not a paired causal comparison between mappings.

| Context tiles | RGB: mean absolute score change, fixed 39 slides | Sampled: mean absolute score change, fixed 31 slides |
| --- | ---: | ---: |
| 2 | 10.141 | 12.800 |
| 5 | 2.308 | 1.978 |
| 6 | 1.832 | 1.711 |
| 16 | 1.123 | 0.897 |
| 32 | 0.626 | 0.648 |

Each cell averages the absolute difference from that candidate's full-context
robust score over its three seeds, then gives each unique slide equal weight.
Units are the existing robust morphology score, not probability, cancer error,
or detector recall. At two context tiles the corresponding mean within-slide
seed range is 19.82 RGB /23.52 sampled; at 32 it is 1.16 /1.24. Changing which few
tiles supply comparison context can substantially change a score without foreign
tissue. Reference subsetting changes both sample count and composition, so these
measurements do not isolate a biological causal effect of count alone.

The existing implementation needs at least six outside tiles for both candidate
NN5 and self-excluding background NN5 to have five neighbors. That is a computational
support fact. These results do not select 6 or 32 as a validated review threshold,
prove stable clinical decisions, or demonstrate a successful revised detector.

The common-support contrast was clarified **after submission but before new
output inspection**, and computed from sealed JSON without changing the frozen
runtime. It is explicitly a secondary descriptive analysis, not an original
runtime output or a preregistered performance test. All-eligible summaries and
all raw exclusions remain in the immutable primary registry.

## Consequences for the next stage

The audit supports two practical requirements for future development: preserve
observed-mapping uncertainty, and expose remaining-context support before giving
an anomaly score a foreignness interpretation. A future abstention/eligibility
contract may protect unsupported comparisons; it must be a new version and be
measured with genuine positive-tissue controls. It must not silently reinterpret
missing support as a negative result or treat dominant native tissue as removable.

This audit does not repair the failed S3 rule. No threshold, majority rule,
connectivity or physical boundary was chosen after observing these results.
Any revised review candidate needs a separately frozen development experiment;
no new final-test readiness or independent validation follows. The original 24
test predictions remain sealed; the evaluated fresh 60 are not made independent
by returning to the original training cohort.

## Execution and reproducibility

Account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`, node `cn061`;
2 CPUs, 8 GB, 20-minute cap, no GPU. Elapsed 27 seconds, Python MaxRSS 378,920 KiB,
**0.015 allocated CPU-hours**. Local environment Darwin; SSH identity verified
`mhoda` on `dt-login04.delta.ncsa.illinois.edu`. Final own queue is empty.

Source `a1597699d3e6381a2f2baa35cebde1b687bdd6ff` is separately staged at
`/u/mhoda/floater-finder/releases/panda-topology-context-v1-20261021T164149Z/source`.
All 246 files and six input hashes verified before execution and after completion.
Protocol SHA256:
`7972dad8aa97db90ac3012239e68412636ce6c1010351541db9190997d8ad9ae`.
[Full frozen design, exact command, runtime, archive and manifest hashes](../docs/panda_topology_context_v1.md).
The original case catalog includes known-calibration entries but no test cases;
measurements/NPZ reads use the strict original-training whitelist only. No fresh 60,
calibration or test arrays were opened. RGB scores came from the verified original
feature cache; no completed RGB or disease experiment was rerun.

Remote root:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review`

| Preserved artifact | SHA256 |
| --- | --- |
| `topology-context-v1/run.json` | `7eeaf9cfec77b83c3653ef1ff72bf73137140ea62b275d020765afc69a12f188` |
| `topology-context-v1/seal.json` | `7ec995e21c0fecf6559951ed51f5068ba64ffd53f9d24c62fe90fdc9c5136036` |
| `topology-context-v1/checkpoints/summary.json` | `77b9974b1b9b2ee80db8f1e5c2010cb3b69587c5a60881fba7b49c4372b4bcd7` |
| `topology-context-authorization-v1.json` | `9a7b0110d62bb4a76ba925dee97f4971b0e56f2be8e8f36854f70699ac1115d0` |
| `topology-context-output-check-v1.json` | `bb19dd194b414fcaa3dc0e2d9b95d4d316bdcd207a1f4ae388d6c1239f8f1098` |
| `topology-context-support-contrast-v1.json` | `5cce918cb1a04ed8ca2fdf6439600e767182e87a0b3edf9ff80e768ea524e0bf` |
| `topology-context-completion-v1.json` | `a85f294b38b707af3d5d51c7daafe6ea2cb652b5790cacf5c8196c22da94bec9` |

Source/annotation alignment, nested reference membership, per-slide control
counts, exact recorded deltas and all registry hashes passed saved-JSON inspection.
All 315 software tests passed with warnings as errors before execution, including
nine new artificial-fixture checks. Only documentation changes afterward; original
33 legacy source hashes, frozen rejected final protocol and main remain unchanged.
All historical results, cohorts, source snapshots and source artifacts are preserved.
The original S1/S3 run, summary and seal receipts still match their pinned hashes.
Raw results stay on Delta; these local notes contain bounded aggregates only.

This completes the bounded audit. No further job was submitted. Read-only next command:

```sh
cat reports/panda_topology_context_results_v1.md
```
