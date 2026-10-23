# Frozen placement audit v1

This development-only CPU audit follows shared-engine job 23069070. Freeze this
source and `configs/panda_detector_placement_v1.json` before measuring new detector
scores. Preserve the source registry, all historical outputs and final-test gate.

Use exactly the 825 previously eligible positive-dose instances: 607 foreign
interventions and 218 native shams, on four unique hosts (two per task). Retain
all 327 old exclusions. Reuse four clean anchors for 192 zero-dose instances;
do not claim these duplicates are new observations. The numeric placement fix
does not admit previously excluded cases. Verify every reconstructed slide's
complete identity against the sealed source checkpoint, and stop on prediction
or oracle mismatch. Load only training artifacts with the strict split loader.

For append, near-tissue and within-region-context additions, form an unlabeled
canvas from the cached complete host foreground and actual hash-verified donor
PNG foreground, using the existing pixel-center projection. Use eight-connected
foreground components, 0.8 tile assignment purity and 0.1 foreground coverage.
No rectangular fill, morphology, inferred bridges, grading masks or foreign
labels enter component construction. Compare membership sets, not component IDs.
Require parity with historical unmodified component memberships for all four
hosts. Checkpoint geometry and complete paired eligibility before detector scores.

Replacement uses unchanged host RGB components as **native carriers**. Report
this separately; it cannot establish detection of an observed donor boundary.
Mapping below 0.9 abstains but stays in recall denominators. Unmapped foreign
tiles are misses; an empty component exclusion is unevaluable. Pair additions
by task, condition, control, host, donor, seed and dose; report both all eligible
cases and common complete append/near/context triplets. Never select pairs using
scores, mapping success or detection outcomes. Hash mismatch stops the run.

Reuse all 35 frozen detector-v3 method/fold thresholds and reference-slide IDs;
`robust_nn5` remains primary. Each reference contributes one normalized centroid;
the host is excluded, while donor reuse is disclosed. No refitting or outcome-
guided threshold/mapping/scorer switch. Visual scores shortlist review candidates;
leave-one-component-out influence explains each candidate and never vetoes it.
S1 uses historical exact CONCH cancer top-5% pooling. S2 uses the frozen training-
selected low/high linear head. Keep cosine-margin and logit influence units separate.

Only after feature extraction/shortlisting, evaluate foreign and native-cancer
annotations. Annotation arrays follow the actual vector's original tile after
append, replacement and same-source shams. Report prediction changes separately
from newly induced errors among originally correct hosts, and recovery only
among those induced errors. Report fragment/tile recall, native tiles and genuine
cancer components flagged, clean-anchor burden and hypothetical filtering damage.
Filtering is a retrospective metric, never an automatic action. Provide host-
conditional bootstrap intervals and unique host/donor counts; repeated instances
are not independent patients. Four clean anchors cannot establish a useful review
policy or population burden. Historical cross-fit burden remains context only.

Run once through `scripts/slurm/panda_detector_placement.sbatch`: verified
`bfqi-delta-cpu` account/QoS, `cpu-interactive`, two CPUs, 8 GB, 20 minutes maximum,
zero GPUs. Stage the exact source commit in a new verified Delta snapshot and use
a fresh output directory. Outputs are a sealed registry, per-case component/
counterfactual records, metrics, frozen pairing and input/PNG identities. There
are no WSI reads, downloads, new encodings, calibration or final-test predictions.

The fixed-membership coordinate ablation and pixel-composite re-encoding are
deferred. This audit must not interpret simultaneous topology/context changes as
a pure effect of distance or claim independent/clinical validity.
