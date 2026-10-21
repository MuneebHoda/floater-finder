# Saved-training dependence report export v1

This integration exports **72 original training slides /389 cached RGB components**
from saved JSON only. It reuses the historical CONCH v1 zero-shot benign/cancer
`top5pct` scorer attached to those cached predictions. It does not substitute the
newer linear predictor, compute new predictions, or transfer counterfactuals to
sampled components with different memberships. All old experiments are preserved.

## Reviewer contract

The reusable `review_report.build_report()` joins allowlisted saved evidence with
matching topology and numeric-context records. It validates baseline/counterfactual
score-label consistency, original tie behavior, memberships, physical metadata,
signed influence, empty-exclusion semantics and the frozen context gate.

Each slide JSON and standalone HTML shows the original baseline and every cached
component, in original order without ranking or shortlisting. A record includes
saved hypothetical exclusion, decision change, occupied tile footprint, observed
RGB area, bounding box, isolation lower bound, outside support, unknown RGB
assignments, diagnostic morphology score and supported/withheld comparison score.
The two area definitions remain distinct. RGB bounds are not physical boundaries.
Six NN5 references and the conservative majority veto remain unvalidated
engineering requirements, not a calibrated foreignness policy.

**Decision dependence stays visible even when numeric context abstains.** No
missing/empty prediction becomes a benign result. Every review/foreignness output
is null and tissue action none. Cosine scores are not probabilities or clinical
diagnoses. Genuine cancer may legitimately be decisive. The report has no deletion
control, automatic exclusion, prediction recalculation, image panel, external asset
or script. It does not establish visually confirmed foreign tissue.

An allowlist keeps slide grades, annotations, foreign masks, synthetic truth and
per-tile class scores out of reviewer JSON/HTML. Native annotation joins separately,
after each report is built, for audit-only control counts. Cached clean cases are
strictly training and unmodified. The old catalog contains known calibration rows,
which are excluded before report construction; it contains no final test case.
The already evaluated fresh60 remain outside this stage, and all original 24
final-test predictions remain sealed.

## Freeze and bounded execution

Protocol: `configs/panda_dependence_export_v1.json`.
SHA256: `0d27e9f62c96e1e5e74466b2519e9e1c2f48bfe221a525da406b41517eaab970`.
Eight input hashes bind the original manifest/case catalog and both previous
registry run/summary/seals. Complete input event/checkpoint chains are verified
without opening their writer locks. Exact original training membership is checked
before slide JSON is read. Source, model/prompt metadata and output identities
are preserved; all rendered-file hashes are included in the new sealed summary.

One new CPU Slurm export: account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`,
**2 CPUs, 4 GB, five-minute cap, no GPU** (maximum 0.167 allocated CPU-hours).
The latest user “next” advances this bounded review-only integration; resources
are agent-selected within that scope. The exact pushed source and command are
shown before submission. Do not reuse a consumed stage approval, retry, duplicate
or overwrite an existing report run. No images/arrays, model calls, GPU, downloads,
new calibration, classification performance measurement or final-test execution.

New intended output, not yet a completion claim:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review/dependence-report-v1`

Expected artifacts: `index.html`, 72 `reports/<slide>.html`, 72 truth-free
`reports/<slide>.json`, 72 registry slide checkpoints containing separate
annotation-control records, aggregate `checkpoints/summary.json`, event chain,
run identity and terminal seal. All detailed artifacts remain on Delta; no local
data/results are downloaded. Local notes contain bounded aggregate/status metadata.

All **350 tests pass** with warnings as errors (40.88s), including fourteen new
artificial-fixture tests. Static fixture HTML checks verify component disclosures, research
labels and no active/remote content. **Visual preview is unverified:** browser
security policy rejected the local-file fixture URL; no workaround was attempted.
Fixtures are software evidence only.

Metadata-only preflight:

```sh
python scripts/panda_dependence_export.py --config configs/panda_dependence_export_v1.json \
  --config-sha256 0d27e9f62c96e1e5e74466b2519e9e1c2f48bfe221a525da406b41517eaab970
```

`--check-inputs` adds remote metadata checks; execution requires the bounded CPU
wrapper and `--execute`. Exact staged source/command and observed export findings
will be appended only after they exist. Export success is not detector validation
or permission to unseal the rejected final evaluation.
