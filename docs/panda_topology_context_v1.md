# Original-training topology and native-context audit

This completed diagnostic follows the failed S3 transfer rule. Its scope is the original
**72 training slides only**, using existing CONCH v1 artifacts. The evaluated
fresh 60, known-calibration arrays and original 24 final-test arrays are outside
this study. Old development-case JSON contains known calibration records but
no test cases; filter it to training before measurements. All data/results stay
on Delta. No WSI, mask image or PNG is read; no classifier or encoder runs.

## Fixed measurements

Reuse the cached 220/10 RGB component memberships and the original detector-v3
full-context robust-NN5 scores, with exact source-file hashes. Do not repeat RGB
segmentation or the earlier prediction/stress experiments. Build the existing
recorded-grid 8-neighbor occupied-cell memberships with zero missing-cell bridges
for their correspondence with those cached RGB memberships.

For each slide, retain the membership-overlap matrix, RGB pieces fragmented by
the sample graph, sampled components spanning multiple RGB pieces, exact matches,
and unassigned RGB tiles. Unassigned tiles stay unknown and remain in outside
context. Neither mapping is declared a pathologist-confirmed physical boundary.
Report occupied-tile footprint separately from observed RGB tissue area; those
areas have different definitions and must not be substituted for one another.

Describe candidate size/share, remaining tile count, majority of the sampled bag,
and robust-NN5 support. The existing algorithm compares each candidate tile with
up to five outside tiles, then normalizes against outside tiles' nearest
neighbors excluding themselves. Therefore the reference operations both reach
five neighbors only with **at least six outside tiles**. Fixed diagnostic groups
are empty 0, singleton 1, partial 2–5, full>=6. These are algorithmic support groups,
not fitted review thresholds or a new foreignness policy. A majority simply means
more than half of saved tiles, not more than half of actual biopsy tissue.

## Bounded reference-context experiment

Select one largest component per slide and topology using tile count alone;
resolve ties by original tile indices. Never select by a score, prediction,
grade or annotation. Keep every candidate feature fixed while using nested
outside-context permutation prefixes of **2,5,6,16,32** tiles under seeds
**20261026/27/28**. Record available full-context score, subset indices, realized
support and score difference. Unavailable target counts remain explicit
exclusions. When requested context equals the full remainder, reuse the cached
score. Mark repeated subsets; they are not independent observations.

Maximum planned records: 72 slides x 2 topologies x 5 sizes x 3 seeds =**2160**.
This measures sensitivity to reference subsetting, which changes both support
and composition. It does not simulate biological contamination or establish
that reference size alone causes clinical errors. Summaries give each unique
slide equal weight after averaging its seed repeats. No size, reference count,
visual threshold or component rule is chosen from the results.

Annotation-known and native cancer-positive tile membership are joined only
after feature construction, using verified source-following native masks for
control accounting. Unknown masks stay unknown. Slide grades are not labels for
every tile. No disease predictions, review flags, filtering, detector recall or
clinical validity are estimated in this study.

## Source, execution and preservation

Frozen protocol: `configs/panda_topology_context_v1.json`, SHA256
`7972dad8aa97db90ac3012239e68412636ce6c1010351541db9190997d8ad9ae`.

The manifest, directory index, embedding-verification receipt, cached cases,
original feature checkpoint and its completion receipt are all hash-bound.
The strict development loader resolves training membership before any NPZ reads.
All 72 originals must load; all cases/cache/annotations must align. Input slide
identities are checked again before sealing. Source/geometry/provenance failures
stop and preserve partial output. No automatic retry or overwritten experiment.

One bounded CPU job: account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`,
**2 CPUs, 8 GB, 20-minute cap**, zero GPUs; at most 0.667 allocated CPU-hours.
Existing prepared runtime and saved inputs only. No downloads, dependency change,
model fitting, alert calibration, original-test access or additional model.
The latest “next” request advances this development audit; resource values are
agent-selected within that bounded research scope. Exact source/command is shown
and recorded before submission. No completed stage approval is reused.

Verified output, created by job 23101968:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review/topology-context-v1`

Observed outputs are a new sealed registry: `run.json`, `events/`, 72 per-slide
`checkpoints/slide-*.json` files, `checkpoints/summary.json` and `seal.json`.
Raw membership matrices, scores, context samples and annotation/control counts
remain on Delta; locally authored notes contain bounded aggregate facts only.

Metadata-only local preflight:

```sh
python scripts/panda_topology_context.py --config configs/panda_topology_context_v1.json \
  --config-sha256 7972dad8aa97db90ac3012239e68412636ce6c1010351541db9190997d8ad9ae
```

`--check-inputs` additionally checks remote metadata hashes and destination
absence. Actual execution requires `--execute` inside the frozen CPU Slurm
wrapper. These diagnostics cannot make the previously evaluated 60 independent
or bypass the rejected original final-test protocol.

## Before-output-inspection analysis clarification

After submission, before viewing any new result, fixed a secondary common-support
contrast: within each topology, compare all five context sizes only among slides
whose geometry-defined largest component has at least 32 remaining tiles. This
eligibility uses support counts, not scores, predictions or annotations. Report
all-eligible size summaries separately; different target sizes can admit different
slide cohorts. This is an explicit clarification after runtime-source freezing,
not a changed runtime or a newly optimized detector.

## Verified staging and exact executed command

Source `a1597699d3e6381a2f2baa35cebde1b687bdd6ff` was staged read-only at:

`/u/mhoda/floater-finder/releases/panda-topology-context-v1-20261021T164149Z/source`

All 246 source files and six original input hashes verified before submission.
Metadata preflight passed, the queue was empty and the intended output absent.
Archive SHA256 `2132f2c87654dc98fb605e93e0dad96a77cde0a39b6b669bddc7f7240d8aaf4d`; source manifest SHA256
`65601eedf31e99f1814a26afa8d0fec575774b544bdde22d6d007bf4395dd1aa`.

Submitted once as **23101968**, completed 0:0 in 27 seconds:

```sh
sbatch --parsable /u/mhoda/floater-finder/releases/panda-topology-context-v1-20261021T164149Z/source/scripts/slurm/panda_topology_context.sbatch /u/mhoda/floater-finder/releases/panda-topology-context-v1-20261021T164149Z/source /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z 7972dad8aa97db90ac3012239e68412636ce6c1010351541db9190997d8ad9ae /work/nvme/bfqi/mhoda/floater-finder/panda-review/topology-context-v1 a1597699d3e6381a2f2baa35cebde1b687bdd6ff
```

All 315 tests passed with warnings as errors before execution, including nine
new artificial-fixture tests. No dependency was added. The sealed registry has
73 checkpoints /76 events and all 72 slide identities remain verified.
[Observed findings, denominators, context contrasts and limitations](../reports/panda_topology_context_results_v1.md).
No detector was retuned or validated; this bounded audit is complete.
