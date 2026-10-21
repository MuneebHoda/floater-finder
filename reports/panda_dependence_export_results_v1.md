# Saved-training dependence report export: verified results

CPU **23102479 completed 0:0 in 16 seconds**, from pushed source `1a388ef`.
It exported **72 original training slides /389 cached RGB components** into
**72 standalone HTML reports, 72 reviewer JSON reports and one HTML index**.
All 145 rendered files, 73 checkpoints and 76 registry events verify. The export
reuses saved predictions and context scores; no classifier, encoder, image/array
read, segmentation, new score, GPU or download occurred. All detailed artifacts
remain on Delta. **350 software tests passed** before execution.

## What is now integrated

The reusable report builder combines allowlisted saved baseline/counterfactual
predictions with matching RGB spatial metadata and the frozen numeric-context
gate. It verifies memberships, physical areas/bounds, score-label/tie consistency,
signed influence, empty exclusions and gate equality. Historical experiments
and their runtime sources remain unchanged.

Each report retains all components in original cached order, without ranking,
shortlisting or a fitted review threshold. It shows hypothetical exclusion,
prediction change, original baseline, occupied tile footprint separately from
observed RGB area, approximate RGB bounds, isolation lower bound, remaining
comparison tiles, unmapped RGB assignments and diagnostic/supported scores.
A saved decision change **remains visible when numeric context abstains**.
Empty exclusions stay unevaluable, never an assumed benign prediction.

Every `review_alert` and `foreignness` field remains **null**, with tissue action
`none`. This is a research dependence report, not a validated foreign-tissue
classifier or a clinical recommendation. It has no deletion/recalculation control,
active scripts, remote resources or image panels. Grades, annotations, foreign
masks and synthetic truth are absent from reviewer JSON/HTML. Native annotation
is joined afterward only in separate audit/control records.

## Saved evidence represented, not new performance measurements

| Quantity | Verified count |
| --- | ---: |
| Training slides represented | 72 |
| Cached RGB components | 389 |
| Nonempty saved counterfactuals | 388/389 |
| Unevaluable empty exclusions | 1/389 |
| Decision-changing components | 25/388 evaluable |
| Unique slides with a decision-changing component | 23/72 |
| Decision-changing components with numeric support | 5/25 |
| Decision-changing components with numeric abstention | 20/25 |
| Decision-changing components containing native cancer annotation | 10/25 |
| Unique slides with those annotation-positive decisive components | 10 |
| Annotation-unknown components in this input | 0 |

These are cached counterfactual descriptions, not newly induced cancer errors,
recovery, false alarms, foreign-fragment recall, prevented harm or newly estimated
classification performance. The ten positive controls each contain at least one
native annotation-positive tile; they are not necessarily pure cancer components.
Annotation-negative components are not automatically benign tissue. All inputs
are unmodified native tissue, and a component changing the prediction is not
therefore foreign. Numeric support does not establish biological context suitability
or score stability. No additional cross-tab or threshold was selected from these
results; alerts/recall remain unmeasured/null, not zero.

The scorer is specifically the **historical CONCH v1 zero-shot benign/cancer
`top5pct` model** attached to the existing RGB cache. It is not the newer frozen
linear primary, and no outcome-guided scorer switch occurred. Prompt and model
fingerprints are preserved in the report provenance. Counterfactuals were not
attached to sampled components with different memberships. RGB bounds and
isolation lower bounds remain proxies, not confirmed physical tissue boundaries.
Different slides are not verified different patients. These 72 are development
training slides; no independent validation follows.

## Access and remaining limitations

Remote index:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review/dependence-report-v1/index.html`

Per-slide JSON/HTML are in the sibling `reports/` directory. Registry checkpoints
retain separate control counts, and `checkpoints/summary.json` binds the hashes
of all 145 rendered files. No report/data file was copied to the Mac. This local
note contains bounded aggregate/status facts only.

Fixture and all real HTML passed static checks for component disclosures, research
labels, expected links, escaped content and absence of active/remote content.
**Visual rendering is unverified:** browser security policy rejected the local-file
fixture preview. No alternate surface or URL workaround was attempted. The reports
also have no tissue-image panels yet; numeric bounds alone do not permit visual
confirmation. A useful next bounded development integration is previews from
existing Delta tile exports, with all source/provenance and uncertainty retained.
No image-processing job has been launched for that future step.

An optional post-run inspection assumed owner-only file permissions and failed.
All 145 content/path hashes passed; actual file modes are **0660** (project-group
read/write). Owner-only report permissions were not a frozen protocol requirement;
permissions were recorded and left unchanged. No source change, dataset change or
job rerun was used to complete inspection.

## Execution and preservation

Account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`, node `cn095`;
2 CPUs, 4 GB, five-minute cap, zero GPUs. Elapsed 16 seconds; Python task 8 seconds,
MaxRSS 121,300 KiB; **0.008889 allocated CPU-hours**. Own queue empty afterward.
Local environment Darwin; shared SSH identity `mhoda` / `dt-login04` verified.

Source `1a388ef47c393afff11e73d53e05783a6a4723d5` was pushed and verified in a
separate 260-file read-only snapshot. Protocol SHA256:
`0d27e9f62c96e1e5e74466b2519e9e1c2f48bfe221a525da406b41517eaab970`.
[Contract, exact source, bounds and submitted command](../docs/panda_dependence_export_v1.md).

Remote root:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review`

| Preserved artifact | SHA256 |
| --- | --- |
| `dependence-report-v1/run.json` | `6aa2ddcb11f1dbfc40975f121744bc6811c58f879b3c16d43c25378345bf1325` |
| `dependence-report-v1/seal.json` | `e39bdef356f22cce786f2598014518a31022187f3c6b3fd1ecf2d7a83978a534` |
| `dependence-report-v1/checkpoints/summary.json` | `876742124f003983a4edcb44aef8e39f69910b34777cc3027d0cc14ab56b17fa` |
| `dependence-report-v1/index.html` | `3a3336fc3e27414c91586fe732881a91a90a8776aaaf8c9062cd093894b7963f` |
| `dependence-export-authorization-v1.json` | `0b7c202b3ea7166209bfea7823407f97e5d098682d28082372ebdfd15550c59e` |
| `dependence-export-completion-v1.json` | `7ae084249f6516e181b44a04c0695f976405a4c165baecd0d8ba8788acf69a76` |

Independent inspection verified every reviewer report against its saved evidence,
all aggregates and control joins, absence of truth fields from reviewer outputs,
all rendered files and registry seals, 260 source files and eight unchanged input
receipts. The old registries are read without opening writer locks and reverified
before sealing. The original rejected final protocol, 33 legacy source hashes
and main remain unchanged, with the final output absent. Original120, evaluated
fresh60, TCGA, all old experiments and final-test seal are preserved. No fresh60,
calibration or original test prediction, new fitting, download, GPU, duplicate or
job retry occurred. This bounded export scope is complete; detector validity and
final-test readiness remain unestablished.

Read-only next command:

```sh
cat reports/panda_dependence_export_results_v1.md
```
