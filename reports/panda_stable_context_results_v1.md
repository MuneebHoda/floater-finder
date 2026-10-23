# Fixed-support candidate: executed, utility gate failed

CPU **23108680 completed 0:0 in 21 seconds** from pushed source `204c194`.
The frozen primary detected **3/24** saved foreign fragments, hypothetically
recovered **1/12** induced errors with all donor/no native tiles shortlisted,
and alerted **8/72 unmodified slides (11.1%)**. It fails the prespecified recall,
recovery and clean-alert targets. The matched full-context comparator also fails
the utility gate. **No threshold, budget, primary or component rule was changed.**
Neither result justifies opening the original final test.

## Observed out-of-fold training results

All denominators include abstentions. Both methods use the same component
eligibility and source-disjoint folds. The comparator is not the historical v3
operating point; direct numerical improvement over that prior experiment is not
established. These are iterative training findings, not independent validation.

| Measure | Fixed32/min3 primary | Matched full context |
| --- | ---: | ---: |
| Fragment hits: any donor tile shortlisted | 3/24 (12.5%) | 2/24 (8.3%) |
| All donor tiles shortlisted | 2/24 | 1/24 |
| Donor tile instances shortlisted | 37/439 (8.43%) | 19/439 (4.33%) |
| Unmodified slides alerted | 8/72 (11.1%) | 7/72 (9.72%) |
| Components shortlisted per unmodified slide | 9/72 =0.125 | 7/72 =0.0972 |
| Maximum components on an unmodified slide | 2 | 1 |
| Genuine annotation-positive components shortlisted | 1/88 | 0/88 |
| Annotation-positive unmodified slides affected | 1/47 | 0/47 |
| Hypothetical damage to initially correct clean predictions | 0/61 | 0/61 |
| Label return among induced errors | 1/12 | 1/12 |
| Source-exact hypothetical induced-error recovery | 1/12 (8.3%) | 1/12 (8.3%) |
| Native host tiles shortlisted across positive cases | 2 | 0 |
| Training-candidate gate | **Failed** | **Failed** |

Primary recall **12.5% <20%**, source-exact recovery **8.3% <25%**, and clean
alerts **11.1% >10%** fail their targets. Its other observed engineering targets
are met, but those do not override the failed gate. The comparator's observed
burden meets the fitting target while recall/recovery remain inadequate. The
additional primary hit accompanies higher native review burden; these counts do
not demonstrate a scientifically established improvement or a useful alert policy.

The 24 mixtures use **24 unique benign host slides and 16 reused donor slides**.
Eighteen hosts were originally correct and six initially incorrect. There are
**12/24 prediction changes**, all newly induced errors among **18 originally
correct hosts**. Recovery therefore uses the **12 induced errors**, not all 24
hosts or the 18 originally correct ones. Initially incorrect hosts are retained
but cannot create newly induced errors. The 439 donor tile observations can reuse
the same source tiles; they are not independent tissue samples or patients.

The primary's single recovered case meets the stricter source criterion: all
appended donor tiles and no native host tiles are shortlisted, with the original
host label restored under hypothetical saved-score pooling. No tissue was
actually removed. Complete donor coverage alone does not imply pure removal if
native tiles are also shortlisted. Generic label return is reported separately
to avoid the earlier native-carrier-removal interpretation error.

The one genuine cancer-containing component shortlisted is native tissue with
positive grading annotation, not known foreign tissue. Zero observed damage to
the historical clean predictions does not establish clinical safety. No reviewer
assessed the images, and no shortlist is converted into a claim of foreignness.

## Coverage, uncertainty and method limits

All **72 original training slides /24 saved 5%-dose cases** are retained, with
**556 original RGB components**. **473** meet fixed support/minority eligibility,
giving **1,419** feature estimates; **83** abstain. Forty-two components have fewer
than 32 outside tiles and all 83 exceed half the sampled bag; these reasons overlap.
All evaluated three-seed reference subsets are distinct, but repeated contexts
remain measurements of the same component. Two low-mapping unmodified slides
remain review abstentions in the 72-slide denominator. Missing RGB assignments
remain unknown and their saved tiles remain possible outside references.

The source graph forms **48 groups**: host/donor-connected groups plus unused
singleton training sources. Every held host and every reused donor is excluded
from that fold's clean threshold-fitting data. Grouped fold construction, strict
clean-only cutoff fitting and all metric denominators were independently checked.
Source IDs support partition/provenance only; they do not enter anomaly features.

Conditional 95% intervals preserve source reuse:

- Primary fragment recall, **16 donor-slide clusters**: **0–25.0%**.
- Comparator fragment recall, 16 donor-slide clusters: **0–18.52%**.
- Source-exact recovery, 16 donor-slide clusters: **0–23.53%**, for both methods.
- Primary clean alerts, **48 source groups**: **4.54–18.42%**; comparator **3.89–17.11%**.
- Primary clean-alert Wilson interval: **5.74–20.42%**; comparator **4.79–18.74%**.

The 2,000-resample intervals condition on frozen scores/folds/thresholds and omit
refitting/selection uncertainty. Source-disjoint slides are not proven independent
patients. The intervals do not establish population burden below 10%. RGB proxies,
sampled bag occupancy, synthetic right-edge construction and native disease
heterogeneity constrain interpretation. Fixed context and consensus did not solve
low-burden identification in this study; this does not prove no future method can.

## Execution, integrity and preserved evidence

Account/QoS **bfqi-delta-cpu**, partition **cpu-interactive**, node **cn137**;
2 CPUs, 8 GB, ten-minute cap, zero GPUs. Root elapsed 21 seconds; Python task
15 seconds, MaxRSS **365,672 KiB**, **0.011667 allocated CPU-hours**. Own queue was
empty before submission and after verification. Site `accounts` showed a pre-run
snapshot of 4,714 CPU hours /8 GPU hours in the previously selected allocations;
these are rounded shared balances, not this job's spend. Local Darwin and shared
SSH identity `mhoda` / `dt-login04.delta.ncsa.illinois.edu` verified after the user
confirmed manual reconnection. No credentials were read or requested.

All **265 staged source files /seven input receipts** verify. The sealed registry
contains **96 case checkpoints +summary, 100 events**. Source grouping, every
reference subset, score minimum/abstention, both clean-only thresholds, flags,
annotation controls, hypothetical pooling, metric denominators and final gates
were independently reproduced from saved JSON without opening WSI/images/models
or loading slide arrays outside the Slurm job. The job rechecked all original
in-memory source identities and input receipts before sealing.

Saved **24 exact-oracle receipts** were checked; no new full oracle execution or
contamination draw was performed. The strict loader opened only original training
artifacts. No new CONCH/model inference, GPU, download, fitting of a disease model,
fresh60/calibration/test predictions, duplicate submission, job failure or retry.
New hypothetical class pooling uses existing saved tile scores only. All image
vectors, reference indices, detailed case metrics and raw outputs remain on Delta.
Only bounded status/count/hash facts returned for these locally authored notes.

The user confirmed **no reviewer is available**. The blank packet remains unchanged
at **0 reviewed /24 pending**, with no invented judgments or reviewer contact.
Main, all six preceding runtime freezes and **33 legacy source files** are intact;
the original final output remains absent. Original PANDA120/fresh60, TCGA and prior
failed results are preserved. **416 software tests passed** before execution;
subsequent edits are documentation only. Human/visual/clinical validation remains
unverified and `final_test_ready=false`.

Remote output:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review/stable-context-v1`

Pushed runtime source `204c194524943e75813e966f300e39dbb5e63bcb`:

`/u/mhoda/floater-finder/releases/panda-stable-context-v1-20261021T214940Z/source`

Protocol SHA256 `bb92f57b73190cf207e32248720b7f963c742086942c7186b6a76d3540b093ae`.
[Fixed design and exact command](../docs/panda_stable_context_v1.md).
Archive SHA256 `0956e4e42d60edf24a2bb489296d1d5b728178732c0516ea9856b784a7e5ce68`;
source-manifest SHA256 `0933e036ed0b0f8c4afc751b3c8cde738397c7a20c143b0a02695ed00ac852aa`.

All receipts below are under the remote `panda-review` root:

| Artifact | SHA256 |
| --- | --- |
| `stable-context-v1/run.json` | `ea4087a08b5326f29ac6510f540b667453e4cae6ca9269bf64c5ed6802669b09` |
| `stable-context-v1/seal.json` | `2f09e07906cc9a9a90588852c59499ef405d4493e90aba12660d37e39fd0910e` |
| `stable-context-v1/checkpoints/summary.json` | `5fa2207de3622cfb534a3139b6c73a0abc1c357854f4799dd4c1b1b3b7f7cb9c` |
| `stable-context-authorization-v1.json` | `97d7e81a271838ee19423703d9c363f9392f9195dbe5a1b81c0c8a5d94b76784` |
| `stable-context-completion-v1.json` | `c5eeca3dd295128edff570333973f6f8d79776fdec3118e56e51d7817d9e3abe` |

This bounded candidate test is complete. A useful foreignness policy remains
unsupported; no retuning, primary switch or extra job follows automatically.
The original final test stays sealed. Expert review remains pending as requested.

Read-only next command:

```sh
cat reports/panda_stable_context_results_v1.md
```
