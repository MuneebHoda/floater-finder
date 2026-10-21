# Saved native/synthetic control audit: verified

CPU **23104084 completed 0:0 in 21 seconds** from pushed source `24364b4`.
All **24 original training 5%-dose pairs**, 24 unique host slides and 16 reused
donor slides have known-provenance comparison pages. They contain **250 unchanged
PNG copies /384 display references**, totaling **16,981,004 bytes (16.19 MiB)**.
All **299 rendered/image files, 25 checkpoints and 28 events** verify. All
**386 software tests passed** before submission, including 23 artificial cases.
No new prediction, intervention draw, model fit or GPU inference was performed.

## What the cached cases establish

| Saved training audit quantity | Verified count |
| --- | ---: |
| Paired cases /unique host slides | 24 /24 |
| Unique reused donor slides | 16 |
| Originally correct benign hosts | 18/24 |
| Initially incorrect benign hosts | 6/24 |
| Prediction changes from original host | 12/24 |
| Newly induced host-label errors | 12/18 originally correct hosts |
| Old exact-oracle receipts checked /new executions | 24 /0 |
| Unique native components overlapping selected donor sets | 17 |
| Decisive overlapping native cancer-containing components | 3/17 |
| Saved mixture RGB components /decisive components | 167 /17 |
| Decisive mixture components containing appended donor tiles | 11 |
| Decisive mixture components containing no appended donor tiles | 6 |
| Appended donor tile instances /unmapped donor tile instances | 439 /8 |

These are bookkeeping observations from already evaluated, correlated training
cases, not independent performance estimates. The six initially incorrect hosts
must not be counted as newly induced errors. Here all 12 changes are new errors,
but the denominators remain different: **12/24 changes versus 12/18 new errors**.
Repeated donors, components and selected tiles do not become independent patients.
Patient identities and patient independence remain unverified.

The three decisive native components contain genuine native cancer annotation
and overlap the cancer-rich sets used as synthetic donors. They demonstrate why
decision dependence is insufficient for foreignness. Their component exclusions
can remove more tissue than the selected donor set; they are **not fragment-only
counterfactuals or exact fragment-removal oracles**. The six decisive mixture
components without appended donor tiles also cannot be labeled foreign from
decision dependence. These counts do not identify a useful alert threshold.

The eight unmapped donor tile instances stay explicit. A component containing
some appended tissue is not necessarily pure foreign tissue, complete donor
recovery or a detector hit. Do not divide 11 decisive components by 24 cases and
call it fragment recall. Detector recall and review-alert rate remain **null**;
review/foreignness decisions remain null, tissue action none, final readiness false.

## Provenance and displays

All 24 old training 5%-dose cases were included without outcome filtering. The
original S1 donor selection was mask-guided and cancer-rich; this audit is not
unbiased whole-slide cancer evaluation. Each pair shows up to four source donor
examples, the exact same PNGs in the synthetic panel, four other native donor
examples and four host examples. Display selection uses only x/y/index ordering.

The synthetic placement is a **saved embedding-coordinate construction**, not an
observed contaminated WSI, pixel composite, verified physical boundary or spatial
reconstruction. Physical captions retain the recorded **111.82315650205668-µm**
field on both axes and original coordinates. Saved translation and bag indices
are recorded separately; HTML sizing is not a physical measurement scale.

The run checked the saved oracle receipts without reexecuting them, exact score
and annotation concatenation, native/synthetic IDs, four-connected selected donor
cells, physical/annotated areas and the original placement rule. All 40 source
completion/CSV/metadata receipt groups and original PNG checksums verify. PNG RGB
mode, recorded dimensions and size bounds were checked within the Slurm job;
independent inspection used hashes and PNG headers, without local image downloads.

This is a **truth-revealed research audit**, separate from the truth-free reviewer
reports. Known source labels are not inferred detector labels. All previous
**1,783 native-gallery files and 145 original reviewer files** remain unchanged.
Static HTML links, local asset paths, research captions and absence of active
controls verify. **Browser layout and pathologist/visual validity remain
unverified**; the earlier local-file policy was not bypassed.

No WSI/mask/NPZ/model was opened, no new inference/class score/embedding, stress
draw, oracle execution, threshold fitting, fresh60/calibration/test evaluation,
GPU, download, retry or duplicate job occurred. All pixels/detailed outputs stay
on Delta. Main, 33 legacy source files, prior runtime freezes and original final
test seal remain preserved; the rejected final-policy gate stays closed.

## Remote artifacts and execution

Index:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review/paired-control-audit-v1/index.html`

`pairs/` contains the 24 JSON/HTML comparisons; `tiles/` contains the unchanged
PNG copies. The sealed summary binds every generated file and source receipt.
No local copy, public service, tunnel or upload of data was created.

Account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`, node `cn137`;
2 CPUs/4 GB/five-minute cap, zero GPUs; Python MaxRSS 244,700 KiB,
**0.011667 allocated CPU-hours**. Own queue empty after completion. Local Darwin
and shared SSH `mhoda` / `dt-login04.delta.ncsa.illinois.edu` verified. Site account
snapshot before preparation showed 4,833 CPU hours and 8 GPU hours in the previously
selected allocations; these are rounded shared balances, not this job's spend.

Source `24364b4946de211ae8b608f7bf7d710408aca112` was pushed and staged read-only;
all 273 files and ten input receipts verified. Protocol SHA256:
`cb5f47e63ec9c745fa59b379b6d6e460e083f031acc73e52b49a095ac1ab1b7b`.
[Frozen design and exact submitted command](../docs/panda_paired_control_audit_v1.md).
The first source archive omitted the pinned old trial receipt; metadata preflight
stopped before submission. That incomplete snapshot is preserved. A complete
archive passed preflight before the only Slurm submission. No job failed or retried.
The old empty `selection.json` and original serialization failure remain untouched.

All following receipts are under the remote `panda-review` root:

| Artifact | SHA256 |
| --- | --- |
| `paired-control-audit-v1/run.json` | `24e48eeb8fd550e9b4ac2b0ba3deff2b0e50d7894310fa8e26a58c10e5e78671` |
| `paired-control-audit-v1/seal.json` | `6064a1c5037d364cc0f3c82848ac24ab76f1c2a173ee06d421a39ae84a182ac4` |
| `paired-control-audit-v1/checkpoints/summary.json` | `e684f6cc7a7cb36d60f8aa6017fb285077473fb6d9ca0ea8e08ef1bb3555659d` |
| `paired-control-audit-v1/index.html` | `0af6f76a7e83e68f18d47615153efd72911182878ca8afd175d9f503a9afcb22` |
| `paired-controls-authorization-v1.json` | `d010f2d2546b150cc7477b7e32ab1ff3c718cc4e72d628fbbec9cfea6745b6ce` |
| `paired-controls-completion-v1.json` | `44a79eddff734526a00194e88b9c328cc5351d8874545bbc2dca68315e1a2eb1` |

This bounded audit is complete. The next scientific need is actual reviewer
assessment of morphology/context and a valid foreignness policy; the saved
counterfactuals alone do not supply either. No next job is submitted or implicitly
validated, and these training controls must not become independent final evidence.

Read-only next command:

```sh
cat reports/panda_paired_control_audit_results_v1.md
```
