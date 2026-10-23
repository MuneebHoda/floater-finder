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

Verified output, created by job 23102479:

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


## Verified staging and exact submission

Source `1a388ef47c393afff11e73d53e05783a6a4723d5` was pushed and staged read-only at:

`/u/mhoda/floater-finder/releases/panda-dependence-export-v1-20261021T172655Z/source`

All 260 source files and eight input hashes verified before submission; queue
empty and output absent. Archive SHA256 `a43ac88d6cd706d0adbe14d6001101e0ef53600888192b5179a15e046f2554ad`;
source-manifest SHA256 `9439d7d57216c3626fb2c7fbd74a5be4ae49b9c39412744f601b8d04819263d5`.

Submitted once as **23102479**:

```sh
sbatch --parsable /u/mhoda/floater-finder/releases/panda-dependence-export-v1-20261021T172655Z/source/scripts/slurm/panda_dependence_export.sbatch /u/mhoda/floater-finder/releases/panda-dependence-export-v1-20261021T172655Z/source /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z 0d27e9f62c96e1e5e74466b2519e9e1c2f48bfe221a525da406b41517eaab970 /work/nvme/bfqi/mhoda/floater-finder/panda-review/dependence-report-v1 1a388ef47c393afff11e73d53e05783a6a4723d5
```

Authorization receipt SHA256 `0b7c202b3ea7166209bfea7823407f97e5d098682d28082372ebdfd15550c59e`.
The latest “next” advances this new bounded integration; resource values are
agent-selected, not expressly chosen by the user. No consumed approval reused.
Job **23102479 completed 0:0 in 16 seconds**. All 72 JSON +72 HTML +index files,
73 checkpoints /76 events verified. [Actual cached-dependence counts, controls,
permission-check note and remaining visual limitations](../reports/panda_dependence_export_results_v1.md).
All review decisions remain null. This bounded export scope is complete; no extra
job or retry was submitted.
