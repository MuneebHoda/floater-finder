# Evaluated Radboud60 — frozen S1 follow-up results

CPU job **23083320 completed 0:0 in 148 seconds** from frozen source `3a3faf1`.
All **2,382 model-specific exact restoration checks passed** across **1,191
representation interventions**; nine planned cases were excluded for connected
capacity. The sealed registry and every registered artifact hash verified.
The study reused the 60 evaluated slides / 25,915 CONCH embeddings without
acquisition, tiling, encoding, fitting or threshold changes. All payloads and
raw predictions remain on Delta; these local notes record bounded aggregates.

## Contamination outcomes and denominators

There are 20 benign hosts, three fixed seeds and 18 unique selected cancer donors.
The primary was initially correct on 18/20 hosts; the historical comparator on
13/20. All hosts were retained. Different slides are verified; different patients
are not. Each dose normally has 60 repeated host/seed instances, not 60 independent
slides. The comparison target is preservation of the **original benign host
label**. Calling an artificial bag with genuine inserted cancer “cancer” is a
separate target and is not by itself a clinical diagnostic error.

| Requested edited dose | Primary append: new host-label errors / initially correct instances | Primary replacement | Historical append | Historical replacement |
| --- | --- | --- | --- | --- |
| 0.5% | 0/54 | 0/54 | 2/39 | 2/39 |
| 1% | 0/54 | 0/54 | 4/39 | 4/39 |
| 2% | 2/54 | 4/54 | 11/39 | 11/39 |
| 5% | 9/54 | 9/54 | 17/39 | 17/39 |
| 10% | 16/54 | 15/51 | 22/39 | 22/39 |

At 5%, primary induced-error frequency is **16.7%** (95% host-cluster bootstrap
**2.0–33.3%**), involving **4/18** initially correct unique hosts under each mode.
Historical frequency is **43.6%** (20.8–66.7%), involving **8/13** hosts.
At 10%, primary append is 29.6% (12.5–49.0%; 7/18 hosts); replacement is
29.4% (10.2–49.0%; 7/17 eligible hosts). Historical append is 56.4%
(33.3–78.8%; 10/13 hosts), replacement 56.4% (33.3–77.8%; 10/13).
These are descriptive frozen-model results, not a superiority test.

Bootstrap resamples unique hosts 2,000 times with seed 20261024, conditional on
fixed donor assignments. Shared donors, unavailable patient IDs and prior exposure
to clean outcomes limit inference. Zero-event empirical bootstrap intervals at
0.5/1% primary doses collapse to zero; they are not evidence of a zero population
risk or a meaningful safety upper bound.

Prediction change is not the same numerator as a new error. At 5%, primary
append/replacement each have 9 changes in all 60 eligible instances, including
six initially incorrect instances. Historical append has **18/60 changes** but
**17/39 new errors**; replacement has **19/60 changes** but **17/39 new errors**.
The other changes correct initially incorrect host-label predictions.
At 5%, resulting cancer calls are 15/60 for primary in either mode and 37/60
append, 36/60 replacement for historical. These include pre-existing cancer calls.

Doses use ceiling counts against the original host tile count. Raw records retain
requested/realized counts, final-bag fractions, donor tile IDs, replacement targets,
translations, original/edited scores and oracle audits. Append alters bag size;
replacement retains bag size and discards native representations until the oracle
restores them. These are saved-representation interventions, not newly scanned
physical contamination.

## Eligibility and editing controls

Of 1,200 planned interventions, 1,191 are eligible: foreign append 300, foreign
replacement 297, native append 297 and native replacement 297. All nine exclusions
occur at 10%: three foreign replacements lack connected native carrier capacity;
three append and three replacement shams lack connected same-source donor capacity.
They are retained with unknown realized dose. No disconnected fragments, repeated
donor tiles or outcome-guided fallback filled the gaps.

There are 594 common eligible append/replacement pairs across controls and doses,
plus three append-only foreign cases. Foreign comparisons have 60 common pairs
per dose except 57 at 10%. On these common 10% pairs, the primary has 16/51 append
versus 15/51 replacement errors, with two append-only and one replacement-only
error events. Equal aggregate frequencies at 5% correspond to the same affected
primary instances; this does not establish equivalence of edit modes.

Same-source replacement is an exact feature null: **0/297 changes per scorer**.
Same-source append produces **0/297 primary changes** and **2/297 historical
changes** (two new host-label errors /195 initially correct instances, on one
host at 5% and 10%). Duplication/pooling can change a historical prediction without
biologically foreign tissue. Generic realized-dose fields describe edited
representations; sham biological foreign count is zero. All model/control/mode
restoration checks pass, including retained original replacement evidence.

## Component dependence and genuine-tissue safety

There are **140 counterfactual bags /280 model-specific reports**: 60 unmodified
slides plus 80 prespecified 5%/first-seed edited bags. Components retain the frozen
8-neighbor occupied-cell rule with no gap bridging. Donor sampling uses separate
4-connected eligibility. Neither rule verifies a complete biopsy boundary.

| Unmodified group | Slides | Evaluable slides | Primary slides with a decisive component | Historical slides with a decisive component |
| --- | --- | --- | --- | --- |
| Benign | 20 | 15 | 1 | 8 |
| Cancer | 40 | 28 | 13 | 7 |
| All | 60 | 43 | 14 | 15 |

Seventeen single-component slides (five benign, twelve cancer) have empty
whole-component exclusions and are unevaluable, not negative findings. There
are 273 sampled components, 256 evaluable. Among 90 components containing native
annotated cancer, **78 are evaluable**. The primary changes on **14/78**, across
13 cancer slides; all 14 exclusions change cancer to benign. Historical changes
on 7/78, including five cancer-to-benign exclusions on five slides. These are
hypothetical component-exclusion outcomes, not observed alerts or actual tissue
removal. The primary decisive carriers span 1.913–6.377 mm² of occupied footprint;
that is component footprint, not annotated cancer area or a verified physical
fragment boundary. The result supports retaining genuine positive tissue and
rejects any rule equating decisiveness with foreignness.

At the fixed 5%/first-seed synthetic condition, primary append has 3/20 decisive
known foreign components; historical has 8/20. Replacement has 2/15 primary and
7/15 historical decisive foreign-containing **evaluable native carriers**, with
five other carriers unevaluable in each case. These carrier exclusions remove
additional native evidence and are not isolated donor-removal tests. No detector
was applied, calibrated review-alert rate is **null**, and these counts are not
fragment-detector recall, false-alert rates or detector recovery.

## Execution, provenance and preservation

Approved resources: account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`,
2 CPUs, 8 GB, 20-minute cap, zero GPUs. Observed node `cn137`, elapsed 148 seconds,
Python MaxRSS 281,436 KiB, **0.08222 allocated CPU-hours**. The queue was empty
before submission and at the first completion check. No job was retried.
Shared identity was `mhoda` on `dt-login01.delta.ncsa.illinois.edu`; local execution
was verified as Darwin. No credentials were inspected or stored.

The [frozen design and exact executed command](../docs/panda_fresh_s1_v1.md)
and historical [preparation receipt](panda_fresh_s1_preparation_v1.json) remain
available. Source commit is `3a3faf199bf2a334648227281a685a999a60f7c9`, verified in
its separate 233-file snapshot. Protocol SHA256:
`d42332cc7950bb89d9ab779912f54e28a6b91114e2a6663ee34ccd15165c9594`.
All three pinned baseline input receipts remained unchanged after execution.
Both frozen clean scorers matched all saved 60-slide decisions and numeric
scores within absolute tolerance 1e-12 before intervention processing.

Remote root:

`/work/nvme/bfqi/mhoda/floater-finder/panda-fresh-baseline/radboud60-v1`

| Preserved remote artifact | SHA256 |
| --- | --- |
| `fresh-s1-v1/checkpoints/summary.json` | `1708497a6260cb7fd0cf2432a55e8d5829c853fe63ef2ab7ad75f3bc6fec8462` |
| `fresh-s1-v1/run.json` | `5fc9a9df37f59d48e63855c697d899a9761facfc1a42480815db6fb193f971ab` |
| `fresh-s1-v1/seal.json` | `604b840c2f705c90309fb9804f523ddc967bf54ffe0ba9da05c165e503edf95a` |
| `reports/fresh-s1-authorization-v1.json` | `9a5e9fc57cd863e49fbd7a6c13e514a472bc333a089074196ed33aca47370ee9` |
| `reports/fresh-s1-output-check-v1.json` | `346dfc69584a2d12e7850bca20baff99560aa562ccd223b97db19e62e219bcb5` |
| `reports/fresh-s1-safety-check-v1.json` | `84d6242fd7502f6bfd9c6b0524b6405e7b7442c65f06b3689ec96331c5508b0b` |
| `reports/fresh-s1-completion-v1.json` | `3071e37093da8dfe735e3e5675c7b8f0b73e58a3830eab5e2bb2aba3b268ceb5` |

The registry has 1,481 checkpoints /1,484 hash-chained events and a verified seal.
The final queue was empty, the original final output was absent, all 233 staged
source files and all 33 legacy hashes still matched, and original input receipts
were unchanged. Native annotation area, physical geometry and empty-exclusion states passed a
saved-JSON safety check, without running more predictions. Full predictions,
audit ledgers, raw component reports and authorization receipt remain remote.
The software suite passed **297 tests** before this unchanged runtime execution;
this checkpoint changes documentation only. Frozen follow-up sources, 33 legacy
source hashes, original rejected final protocol and main remain unchanged.
TCGA evidence, all prior PANDA artifacts and the original 24-test seal are
preserved; no original final-test predictions were computed.

The exact CPU approval is consumed. A useful foreignness/review policy is still
unvalidated. A next development stage would need a separately frozen policy
scope, matched native editing controls, genuine-cancer harm constraints and
review-burden evaluation. No additional job, GPU run, model, download, threshold
selection or final evaluation is authorized by this completed run.

Read-only local next command:

```sh
cat reports/panda_fresh_s1_results_v1.md
```
