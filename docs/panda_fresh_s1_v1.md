# Evaluated Radboud60 — frozen S1 follow-up preparation

The next study reuses the 60 evaluated slides and 25,915 verified CONCH v1
embeddings. It prepares new representation-level contamination outcomes, with no
additional acquisition, tiling, encoding or model fitting. The original 24 test
predictions stay sealed. All data and detailed outputs remain on Delta.

## Fixed design

All 20 benign slides are hosts, including initially incorrect cases. Both the
training-selected `linear_mean_max_topk` cancer primary and exact historical
CONCH top-5% comparator remain frozen. Their known clean-correct host counts
are 18/20 and 13/20 respectively; hosts are not selected or excluded using those
predictions. Different slides are verified; different patients are not.

For each host and each of three fixed seeds 20261020/21/22, select one cancer
donor using the existing capacity-first deterministic hash order. Donors are
Radboud ISUP 1/4/5 from this exact cohort, with native GP3+4+5 fraction >=10% on
every selected tile. A single four-connected sampled component supplies nested
unique prefixes for 0.5/1/2/5/10% requested doses. Counts use the existing ceiling
against original host tile count. No duplicated donor tile, disconnected merge,
score-based donor choice or capacity fallback is allowed. Small capacity produces
an explicit exclusion at each affected dose, with unknown realized dose.

Compare two existing shared interventions:

- Isolated right-edge append: same legacy three-grid-step translation.
- Replacement: substitute representations at connected existing host positions,
  retaining original vectors/IDs/coordinates for exact restoration. It is a
  representation edit, not a simulation of an observed physical donor boundary.

Same-source shams use the identical native host under both operations. Append
shams test duplication/editing effects without biological foreign labels;
replacement shams are exact feature nulls. The oracle restores retained original
state, including substituted host evidence; merely deleting replacement indices
is insufficient. Any oracle mismatch stops the job and preserves failures.

Maximum 1200 representation interventions: 20 hosts x 3 seeds x 5 doses x 2 controls
x 2 modes. Both frozen models score each eligible intervention (maximum 2400
model-trial records). Zero-dose anchors reuse the verified clean baselines once
per slide; they are not additional independent donor/seed observations.

## Component counterfactuals and safety controls

Run the unchanged legacy eight-neighbor occupied-cell analysis with
`max_gap_tiles=0`, no missing-cell bridges and no alert policy. Analyze all 60
unmodified slides, including all 40 genuine annotated-cancer controls, plus only
the preregistered 5% dose/first-seed cases for each host/control/mode. This is at
most 140 bags / 280 model-specific analyses. Each nonempty exclusion recomputes
full pooling; deleting the only component is explicitly unevaluable.

Labels, annotations and synthetic foreign masks enter evaluation only after
component construction and scoring. Record native cancer annotation area,
foreign membership, occupied-footprint physical area, isolation and exact raw
counterfactual predictions. A genuine small positive component can be decisive.
No decisive component is automatically labelled foreign. Replacement components
are native carriers; sampled connectivity is not a complete biopsy boundary.
No actual tissue or saved artifact is deleted. Review-alert rate remains null.

## Denominators and frozen analysis

Report prediction changes across every eligible case separately from newly
induced errors among initially correct hosts, separately for each model, control,
mode and dose. The target is preservation of the original benign host label;
recognizing genuinely inserted cancer is a different diagnostic target. Report
mixture cancer response separately. Initially incorrect hosts remain visible,
and capacity/geometry exclusions stay in planned/eligible denominator ledgers.

Record complete append/replacement eligibility by fixed host/donor/seed/dose
pairing, without selecting on scores. Do not interpret different eligible cohorts
as a paired mode effect. Unique host/donor counts and repeated-trial counts remain
distinct. Error-rate uncertainty uses 2000 host-cluster bootstrap replicates,
seed 20261024, conditional on fixed donor choices. Donor reuse and unavailable
patient identity limit population inference. Raw oracle recovery is not detector
recovery. Unmodified decision dependence is not a calibrated false-alert rate.

## Integration and gates

The shared engine takes an explicit `FollowupCohort` binding manifest/protocol
hashes and complete original artifact identities. It accepts these
`engineering` sources only under that whitelist; default development/test guards
and historical results remain unchanged. Sources are never relabelled training.
Before real processing, all 60 artifacts pass the strict original fresh loader,
all saved baseline completion hashes are checked, and both clean score vectors
must match saved outputs (labels exactly; absolute numeric tolerance 1e-12).

The protocol is `configs/panda_fresh_s1_v1.json`, SHA256
`d42332cc7950bb89d9ab779912f54e28a6b91114e2a6663ee34ccd15165c9594`. It pins baseline protocol/model/manifest identities, verified input
receipts, source files, seeds, doses, controls and resource bounds. CLI default
preflight verifies metadata/models without opening slide arrays or predicting.
`--execute` additionally requires CPU Slurm and the exact new output directory.
A sealed shared registry preserves per-case interventions, exclusions, scores,
component reports, raw metrics, source/input fingerprints and failure states.
Existing outputs are refused rather than overwritten or automatically resumed.

Proposed single CPU job: account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`,
2 CPUs, 8 GB, 20 minutes maximum (0.667 allocated CPU-hours), zero GPUs, no downloads
or WSI/PNG reads. Intake uses already saved arrays and small metadata. The actual
cost of this new workload is unmeasured; the wall-time cap is not a runtime claim.
The source snapshot, exact command and bounded remote preflight are recorded in
`reports/panda_fresh_s1_preparation_v1.json` once staging is complete.

Intended new output, not a claim of executed results:

`/work/nvme/bfqi/mhoda/floater-finder/panda-fresh-baseline/radboud60-v1/fresh-s1-v1`

Further submission requires the new concrete CPU scope approval described in
`AGENTS.md`; the completed clean-baseline approval is not reused. No follow-up
experiment has been submitted or observed in this preparation. New scientific
results must be committed separately after actual execution and verification.

## Completed software and metadata checks

All 297 software tests passed with warnings as errors in a clean temporary
environment installed entirely from the offline cache. An initial run in the
worktree environment had 295 passes and two isolated installed-package import
failures; duplicate numbered package files were observed there. No application
change was made for that transient installation issue. Its six CLI tests passed
on rerun. New tests use only artificial arrays in temporary directories; they
cover leakage/identity guards, matched shams, capacity/initial-error denominators,
physical annotation area, genuine positive decisiveness and oracle-failure stop.

Bash syntax, metadata-only preflight and the 33 frozen legacy source hashes pass.
The original protocol and main remain unchanged. Bounded Delta metadata confirms
all 60 slides have the same recorded 111.82315650205668-µm nonoverlapping tile
footprint, from TIFF-derived scale, for the 112-µm requested FOV. This supports
strict compatibility checks without rescaling or inventing coordinates. Donor
connected capacities and real follow-up outcomes remain unmeasured until the
approved CPU job. The existing clean outcomes are not repeated contamination
evidence.

Metadata-only local command (no real slide arrays or predictions):

```sh
python scripts/panda_fresh_s1.py --config configs/panda_fresh_s1_v1.json \
  --config-sha256 d42332cc7950bb89d9ab779912f54e28a6b91114e2a6663ee34ccd15165c9594
```
