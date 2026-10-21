# Saved native/synthetic control audit v1

This separate, **truth-revealed research audit** displays the same donor PNGs in
their native slide and their saved synthetic S1 intervention. It does not modify
the existing truth-free reviewer reports or infer which tissue is foreign.

## Fixed scope

Use **all 24 original training 5%-dose append cases**, with 24 unique benign-host
slides and 16 reused cancer-donor slides. Select by split/dose, never by prediction
change, annotation strength, image appearance or detector outcome. The donor sets
were already selected by the original mask-guided S1 experiment; this does not
make donor acquisition an unbiased cancer evaluation. Distinct slides are not
verified distinct patients. No fresh60/calibration/test evaluation or original
final-test access is performed. The rejected final policy stays rejected.

For each pair, show up to four original donor-set examples, the **same PNGs** in
the synthetic panel, four other native donor examples, and four native host
examples. Selection is the unchanged x/y/index geometry-only rule. The saved
translation and bag indices are recorded, but these source galleries are neither
an image composite nor a spatial reconstruction of a contaminated biopsy.

Retain native donor baseline, clean host baseline, saved mixture prediction and
raw cosine scores. Show native RGB components overlapping the selected donor
set and all saved mixture components, retaining empty exclusions, numeric-context
abstentions and unmapped donor tiles. An overlapping native component can contain
more tissue than the donor set: its exclusion is **not a fragment-only oracle**.
Native cancer may legitimately change a prediction. Review/foreignness remain
null and tissue action none; this audit is not a floater-detection policy.

Count prediction changes across all 24 hosts separately from newly induced errors
among originally correct hosts. Retain initially incorrect hosts in the audit.
Deduplicate native component counts by donor slide/component, because donors are
reused. Case and tile-instance counts are correlated, not independent patients.
No detector recall, alert rate, harm rate or validation claim is estimated here.

## Provenance and bounded execution

Protocol `configs/panda_paired_control_audit_v1.json`, SHA256:
`cb5f47e63ec9c745fa59b379b6d6e460e083f031acc73e52b49a095ac1ab1b7b`.

Ten input receipts bind the original manifest/directory/embedding verification,
case catalog, original stress trials, cached robust-NN5 features/completion and
native gallery registry. The remote trial file is identical to the already
committed original `reports/panda_s1_trials_23065666.json`. The old development
`selection.json` is empty from its preserved serialization failure and is not
used. No failed old experiment is rerun or repaired.

Before copying images, validate the saved exact-oracle receipt; fail and preserve
partial output if it is false. This **checks the old receipt**, without rerunning
the oracle. Check exact native/synthetic score-vector concatenation, annotation
mapping, selected tile IDs/counts, connected donor grid cells, placement rule and
physical/annotated areas. Check source CSV/metadata/PNG identities against the
original encoding receipt and sealed native gallery. All selected PNGs are
byte-identical copies, RGB with their recorded dimensions, at most 1 MiB and
512x512 pixels each before decoding. Recheck sources and outputs before sealing.
No WSI, mask, NPZ, model checkpoint or network download is opened.

One CPU Slurm job: account/QoS **bfqi-delta-cpu**, partition **cpu-interactive**,
**2 CPUs, 4 GB, five-minute cap, zero GPUs** (at most 0.167 allocated CPU-hours).
Maximum 384 display references, 288 unique PNGs and 64 MiB copied PNG bytes.
The latest user “next” advances the explicitly proposed saved-control comparison;
resources are agent-selected within that direction, not expressly user-selected.
Exact pushed source and command were shown before the one submission. No duplicate,
retry, inference, embedding, stress draw, fitting or final-test job is included.

Verified new output, completed by job 23104084:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review/paired-control-audit-v1`

Expected: index, 24 JSON/HTML pairs, unchanged PNG copies, 24 registry pair
checkpoints, summary, event chain and seal. Detailed outputs/images stay on
Delta; no data/result files are copied to the Mac. Existing outputs are read-only
inputs and never overwritten. Static HTML links/provenance are tested; browser
layout remains unverified under the previously observed local-file policy.

All **386 software tests pass** with warnings as errors (33.90s), including 23
new artificial fixture cases and a complete 24-pair /16-donor software run. These
are software checks only. Original main, 33 legacy source files and all four
previous runtime freezes remain intact. [Verified real audit counts and limits](../reports/panda_paired_control_audit_results_v1.md).

Metadata-only local source preflight (no remote payload read):

```sh
python scripts/panda_paired_controls.py \
  --config configs/panda_paired_control_audit_v1.json \
  --config-sha256 cb5f47e63ec9c745fa59b379b6d6e460e083f031acc73e52b49a095ac1ab1b7b
```

On Delta, `--check-inputs` adds metadata/destination checks without PNG decoding.
Actual export requires the bounded CPU wrapper and explicit `--execute`.

## Verified staging and one submission

Pushed source `24364b4946de211ae8b608f7bf7d710408aca112` was separately staged at:

`/u/mhoda/floater-finder/releases/panda-paired-controls-v1-20261021T181828Z/source`

All 273 source files and ten input receipts verified, own queue empty and intended
output absent. Archive SHA256 `e5ea5b3d2a5bbc2e5871a6147a9b71da820b4402bb9e3ce2a944d890546d3631`;
source-manifest SHA256 `9bc9d13bce22bd15960f1b7e52fc979b6ab91e3e6607bcc53eee55401a5aba3a`.
The first archive at `panda-paired-controls-v1-20261021T181806Z/source` omitted the
pinned original trial receipt and failed metadata preflight before submission.
It is preserved; the completed archive passed before the only job submission.
No source/protocol/runtime change or Slurm retry was needed.

Exact submitted command, job **23104084**:

```sh
sbatch --parsable /u/mhoda/floater-finder/releases/panda-paired-controls-v1-20261021T181828Z/source/scripts/slurm/panda_paired_controls.sbatch /u/mhoda/floater-finder/releases/panda-paired-controls-v1-20261021T181828Z/source /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z cb5f47e63ec9c745fa59b379b6d6e460e083f031acc73e52b49a095ac1ab1b7b /work/nvme/bfqi/mhoda/floater-finder/panda-review/paired-control-audit-v1 24364b4946de211ae8b608f7bf7d710408aca112
```

Completed **0:0 in 21 seconds**, node cn137, zero GPUs; 24 paired pages /250 PNGs
/384 references, 16,981,004 copied bytes, all 299 files /25 checkpoints /28 events
verified. Previous 1,783 gallery and 145 reviewer hashes are unchanged. All
payloads remain on Delta; no new predictions, draws or oracle executions. This
scope is complete; browser layout and visual/clinical validity remain unverified.
