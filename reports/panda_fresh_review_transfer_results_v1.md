# S3 conservative review-transfer results

CPU **23101320 completed 0:0 in 35 seconds** from frozen source `a5d819c`.
All 140 saved S1 bags produced verified review checkpoints and 9800 model/policy
records. The primary combined rule finds **0/20 known foreign fragments per
mode**, flags **4/60 unmodified slides**, and would damage **4/46 initially
correct unmodified predictions** under hypothetical filtering. Those four flags
contain genuine annotated cancer. This rule does not provide a useful review
operating point. No cutoff was relaxed and no original final-test prediction ran.

## Fixed design and interpretation

The [frozen transfer diagnostic](../docs/panda_fresh_review_transfer_v1.md)
uses existing CONCH v1 embeddings, both frozen cancer scorers and the exact saved
8-neighbor/no-gap S1 component memberships. No contamination draw, baseline
experiment, tiling, embedding or counterfactual-component experiment was repeated.
The visual rule is strict agreement with all five old training-clean robust-NN5
thresholds: **score >9.32818765238456**. The prior thresholds used RGB components;
this study uses sampled occupied cells. This conservative new aggregation has
not been independently calibrated for the new topology.

There are 60 unmodified slides plus 20 foreign append, 20 foreign replacement,
20 native append and 20 native replacement bags, all at the predeclared 5% dose
and first seed. Synthetic cases reuse 20 benign hosts and 11 unique cancer donors;
18 hosts are initially correct for the primary, 13 for historical. Different
slides are verified, different patients are not. The cohort had already been
clean-scored and S1-evaluated before this visual study. It is iterative development,
not pristine independent policy validation. Native floaters were not adjudicated.

The 840 deterministic-policy records and 8960 random-control records total 9800;
these are not 9800 independent mixtures, slides or patients. There are 625 component
observations across the 140 bags, including repeated native tissue. Visual scores
are unavailable for 35: 27 empty exclusions and 8 single-tile background references.
Seventeen of 60 unmodified slides are single-component abstentions; they remain
in all-slide burden denominators. Five of 20 replacement bags per control also
abstain. These are unknown exclusions, not evidence that those slides are safe.

## Primary scorer: review burden and genuine-tissue harm

| Fixed rule | Unmodified slides flagged /60 | Mean flagged components per slide | Genuine cancer-containing components flagged /90 | Hypothetical damage /46 initially correct slides |
| --- | --- | ---: | --- | --- |
| Visual only | 5/60 | 0.0833 | 4/90 | 4/46 |
| Decision dependence only | 14/60 | 0.2500 | 14/90 | 13/46 |
| Combined | 4/60 | 0.0667 | 4/90 | 4/46 |

Of 90 native cancer-containing sampled components, 78 have evaluable exclusions.
The table uses the all-component denominator; four combined flags are also 4/78
evaluable genuine components. This is a negative control for foreignness.
All four combined flags remove native cancer evidence and change cancer to benign.
The reported damage is a hypothetical model-label change, not an actual clinical
outcome or an action on saved tissue.

The primary combined point estimate meets the observed <=10% slide-flag and
<=0.5-component targets, but its unique-host bootstrap flag-rate interval is
**1.7–13.3%**. Zero foreign recall and hypothetical native-cancer damage prevent
acceptance of the rule despite its low review burden. The four flagged carriers contain
**504–510 sampled tiles**, occupying **98.44–99.61% of their bags**, with
**6.302–6.377 mm²** occupied footprint. Their exclusions leave only 2–8 tiles.
These are sampled carriers, not verified physical fragment boundaries. Limited
remaining native context can make a dominant component look visually unusual;
this observed pattern motivates a development topology/context audit, not a
post-outcome size threshold or a foreignness claim.

## Primary scorer: known synthetic tissue and label returns

Each edit mode has 20 host/donor bags and 446 known foreign tile observations.
An overlap hit is not automatically isolated fragment localization in replacement:
its native carrier includes additional host evidence.

| Rule | Append fragment hits /20 | Append foreign tiles flagged /446 | Append induced host-label errors returning to benign /3 | Replacement fragment hits /20 | Replacement foreign tiles flagged /446 | Replacement label returns /3 |
| --- | --- | --- | --- | --- | --- | --- |
| Visual | 0/20 | 0/446 | 1/3 | 1/20 | 26/446 | 0/3 |
| Dependence | 3/20 | 78/446 | 2/3 | 2/20 | 52/446 | 1/3 |
| Combined | 0/20 | 0/446 | 1/3 | 0/20 | 0/446 | 0/3 |

There are 3/18 newly induced original-benign-host-label errors per mode at this
single seed; this differs from 9/54 in the prior three-seed S1 summary. Initially
incorrect hosts remain present but never enter the new-error denominator.
Recognizing genuine inserted cancer is a separate diagnostic target.

The combined append **1/3 label return removes 507 native tiles, removes zero
foreign tiles, and retains all 26 foreign tiles in that bag**. It cannot support
a claim of successful contaminant removal. The saved metric
`recovered_host_label_errors` measures return to the original benign label only;
localization, native loss and genuine-tissue harm must accompany it. Decision-only
append also creates one empty hypothetical bag; that case is unevaluable and is
not counted as a benign recovery. All source tissue/embeddings remain unchanged.

## Controls and historical scorer

Primary combined flags 0/20 native append and 0/20 native replacement shams.
Visual-only still flags one native replacement carrier; the edit is an exact
feature null. Decision-only flags one bag per native mode. These native cases
contain no synthetic foreign truth.

Random controls keep the combined rule's **per-bag flag count and bag selection**
fixed and choose components uniformly, with 32 fixed draws. They test localization
within those bags, not independent selection of which slides to review. Primary
append random draws hit 15/640 repeated fragment observations (mean 0.469 hits per
20-bag draw) and return 32/96 repeated induced-error labels (mean 1/3 per draw).
Primary replacement random flags are all zero because combined flags are zero.
On the 60 unmodified slides, random controls have the same 4/60 slide flags and
average 1.781 genuine components flagged and 1.438 damaged predictions per draw,
compared with four of each for combined. These descriptive controls are not an
independent random-cohort superiority test.

The historical scorer remains a comparator; it is not selected after outcomes:

| Rule | Unmodified flags /60 | Genuine cancer-containing components flagged /90 | Hypothetical damage /47 initially correct | Append hits /20 | Replacement hits /20 |
| --- | --- | --- | --- | --- | --- |
| Visual | 5/60 | 4/90 | 1/47 | 0/20 | 1/20 |
| Dependence | 15/60 | 7/90 | 10/47 | 8/20 | 7/20 |
| Combined | 2/60 | 1/90 | 1/47 | 0/20 | 1/20 |

Historical combined recovers 0/8 induced host-label errors in either mode, despite
one replacement overlap hit. That hit flags a 507-tile carrier: 26 foreign plus 481
native tiles. The cleaner-looking 2/60 unmodified rate still includes native
cancer harm and weak localization. No useful policy follows from switching scorers.

Uncertainty resamples unique hosts 2000 times with fixed seed 20261025, retaining
all repeated controls. Primary combined label-return interval is 0–100% from only
three induced-error hosts; this is conditional uncertainty, not a clinical estimate.
Zero-event empirical bootstrap intervals collapse to zero and are not population
safety bounds. Donor reuse, selection/exposure history and unknown patient identity
limit all generalization claims. No model, threshold, component rule or primary
policy was changed after seeing these results.

## Execution and preserved evidence

Verified account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`, node `cn100`;
2 CPUs, 8 GB and 20-minute cap, zero GPU. Observed elapsed 35 seconds,
Python MaxRSS 345,324 KiB, **0.01944 allocated CPU-hours**. Local environment is
Darwin; shared identity was `mhoda` on `dt-login04.delta.ncsa.illinois.edu`.
The queue is empty and the original final output remains absent. No retries,
downloads, extra encoder/model, threshold fitting or original-test predictions.

Frozen source: `a5d819c360950d15ad0de84569ea5289edcb8942` at
`/u/mhoda/floater-finder/releases/panda-fresh-review-transfer-v1-20261021T161755Z/source`.
All 240 source files and the metadata-only preflight verified before submission;
all 240 files and 33 legacy source hashes matched afterward. Protocol SHA256:
`f6c27f854187978ec5d2cb2e889adb8279b618d1a98c1d03cb370494109f68e9`.
The [protocol note](../docs/panda_fresh_review_transfer_v1.md) records the exact
command, runtime and source archive/manifest hashes.

Remote root:

`/work/nvme/bfqi/mhoda/floater-finder/panda-fresh-baseline/radboud60-v1`

| Preserved remote artifact | SHA256 |
| --- | --- |
| `fresh-review-transfer-v1/run.json` | `333953c2cff96440fcc3fc419ccd654e9ca4c93296c825264bdd9ee7bd3c676e` |
| `fresh-review-transfer-v1/seal.json` | `07854f839db097b80a22e332f595675d66cfb8f2d4bd79d9436b0dbbe0a46a9a` |
| `fresh-review-transfer-v1/checkpoints/summary.json` | `fe9eede3cbaec667110f6353eb615959931cdea5ae972187117e8a12f630d92f` |
| `reports/fresh-review-transfer-authorization-v1.json` | `93abe4ea705202c34b4340bdd64fdedd28f42febae66881d1c15cfe1a0bc6898` |
| `reports/fresh-review-transfer-output-check-v1.json` | `4338a7795632c780c21599557496436dc3d11e1a40c1198dff6cee16d8c070cf` |
| `reports/fresh-review-transfer-interpretation-v1.json` | `ad23c1041c334dc13c4e7ecf49c0be64929f20b1cab9e6c78c93ff8b40192af3` |
| `reports/fresh-review-transfer-completion-v1.json` | `166cfcffc7621d4d1239a9fb1626efe2e898d503da7571fff1ccfddb1c510f3b` |

The registry verifies **141 checkpoints /144 events** and its terminal seal.
Both original S1 and baseline receipts remain unchanged after execution.
Every policy denominator and random-control draw count was checked against saved
JSON, with no additional inference. All raw component records/predictions stay
on Delta. Local notes contain bounded aggregates only; no artifacts were downloaded.
The unchanged code passed **306 tests** with warnings as errors before execution,
including nine new artificial-fixture tests. Bash syntax, original protocol,
33 legacy source hashes and main remain preserved, as do all historical results.

This completes the bounded S3 transfer stage. The next scientific need is a
truth-blind topology/native-context feasibility audit using original development
data, before designing another rule. This requires a separately frozen scope;
no further job is launched here. Do not use these negative outcomes to retune a
threshold and describe the same 60 slides as independent validation. The original
24 final-test predictions remain sealed and unsupported final execution stays blocked.

Read-only next command:

```sh
cat reports/panda_fresh_review_transfer_results_v1.md
```
