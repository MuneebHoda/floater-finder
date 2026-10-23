# Expanded pixel research program v1 — October 21, 2026

The executable first stage prepares **10,000 candidate image/control records on
Delta**, independently of the existing 96-image pilot. It does not authorize a
new GPU submission. The candidate count is not a count of unique RGB images,
successful extractions, independent slides, or patients. The CPU receipt supplies
the exact rendered and deduplicated counts before an inference scope is approved.
All images, masks, embeddings and detailed results stay on Delta.

## Verified resources and existing work

Observed 18:43 CDT, after verifying `mhoda` / `dt-login04.delta.ncsa.illinois.edu`:

| Quantity | Live evidence |
| --- | --- |
| GPU account / user QoS | `bfqi-delta-gpu` / `bfqi-delta-gpu-mhoda` |
| QoS deposited limit | 600,000 billing-TRES minutes = 10.0000 batch A100-hour equivalents |
| Exact usage | 95,500 billing-TRES minutes = 1.5916667 equivalents |
| Exact remaining | 504,500 billing-TRES minutes = **8.4083333 equivalents** |
| Raw QoS usage | 5,730,000 billing-TRES seconds; agrees exactly with root-job accounting |
| Rounded displays | `accounts`: 8 remaining; `jobcharge --detail --all`: 1.60 used |
| Noninteractive A100 | `gpuA100x4`, UP, default 30 min, maximum 48 h, GPU weight 1000 |
| Interactive A100 | `gpuA100x4-interactive`, UP, maximum 1 h, GPU weight 2000 |
| Other TRES weights | Batch CPU=62.5, memory=16/GiB; interactive CPU=125, memory=32/GiB |
| Limits | Association permits GPU QoS without a partition restriction; interactive partition QoS permits one running/submitted job per user |
| CPU preparation | `bfqi-delta-cpu` / `bfqi-delta-cpu`, `cpu` batch, 4 CPUs, 16 GiB, 30 min |

These are allocation equivalents, not guaranteed wall time or immediate GPU
availability. Slurm uses MAX_TRES billing. With one A100, four CPUs and 16 GiB,
GPU weight dominates: batch costs 1× and interactive 2×. Historical completed
batch A100 jobs used this exact sub-allocation; a new `sbatch --test-only`
admission check is recorded separately. The QoS UsageFactor is 1, and
associations/limits/QoS/safe accounting enforcement is enabled. The official
[Delta job guide](https://docs.ncsa.illinois.edu/systems/delta/en/latest/user_guide/running_jobs.html)
also describes the batch/interactive charging distinction; current CLI settings
take precedence where documentation differs.

The ten GPU charges, including failed job 23051627, are preserved in
[`panda_gpu_program_metadata_audit_v1.json`](../reports/panda_gpu_program_metadata_audit_v1.json).
For each allocated root job, compute `billing_TRES * ElapsedRaw / 3,600,000`.
Do not sum individually rounded `jobcharge` rows. Old reports of elapsed GPU
hours remain unchanged; they did not include the interactive multiplier.

Existing CPU **23109277** is pending on priority; existing GPU **23109340** is
pending on `afterok:23109277`. Leave both intact. Failed prolog job 23109222 is
preserved. No completed real pixel experiment is claimed. Scientific runtime
`61959fa148a4a3ae4aadb5ee84b9578933140f6b` has 276 verified files; its source
manifest hash is `573c26663c3dec96b080c3f186573c513c39ff3408e469dc64f501140e894618`.
Launcher `1b4d19b39c3535a326bc6b00ef497f857e440cf7` has five verified files;
manifest hash `a7738f5eb9f14c64ac0b13d278da74811b0a25f962ff365e0521a16df20c9528`.
Frozen pilot protocol hash is `33594b467bdd16c75e3b4835a744bab2e917972266a31e33779ac0be386eefb7`.

Existing checkpoint:
`/work/nvme/bfqi/mhoda/floater-finder/inputs/models/conch_v1/pytorch_model.bin`,
802,235,437 bytes, expected SHA256
`40a9644b9ba0e83a74576e0a5e5f7313599fa9c9cdaf3c20f8a3e271b0e9ae7c`.
This hash was verified in previous scheduled encoding. **The current-file hash
must be reverified by the new CPU job**; metadata inspection alone does not
establish it. The pinned model, tokenizer, preprocessing and runtime fingerprints
are in `configs/panda_gpu_program_v1/protocol.json`.

## Source selection and independence

The verified 120-slide manifest contains 72 original training slides. Excluding
the pilot's eight sources leaves **64 masked, available Radboud sources**:
22 benign, 22 GG1, 20 ISUP4/5. Selection uses ascending
`SHA256('20261021/pixel-program-v1/'+image_id)` within each group. It does not use
new scores. Select 19/group: the first 15 for benchmark B and the next four for
dense study C. The remaining seven are unused reserves, not automatic substitutes.

| Study | Fit | Calibration | Source-held-out validation | Total |
| --- | ---: | ---: | ---: | ---: |
| B pixel benchmark | 27 (9/group) | 9 (3/group) | 9 (3/group) | 45 |
| C dense/multiscale | 6 (2/group) | 3 (1/group) | 3 (1/group) | 12 |

All 57 image IDs are distinct; B and C do not overlap. Original calibration,
24 sealed original-test slides, and all eight pilot sources are excluded.
Known patient IDs: **zero**. These are source-slide splits, not verified patient
splits. Any subsequently known patient crossing roles/folds blocks execution.
Original disease scorers were developed on original training sources; their
results here are mechanistic/resubstitution evidence, never independent cancer
generalization. A newly fitted foreignness detector has its own source-held-out
validation, whose small number of slides limits its uncertainty.

The 40 predetermined pairs use 24 fit, eight calibration, eight validation pairs.
Actual unique hosts/donors/union: **18/18/27**, **6/8/9**, **7/6/9** respectively.
Within-fold host/donor roles may overlap across pairs; across-fold overlap is zero.
All nine host-grade × donor-grade directions occur in fit. The exact source IDs,
paths and original image/mask hashes are in
[`sources.csv`](../configs/panda_gpu_program_v1/sources.csv); the exact pair list
is in the protocol. Repeated sources/pairs/images are not independent replicates.

## A — finish and freeze the original pilot

Inspect the existing CPU completion, then the GPU drift gates and completion.
Require eight canonical unchanged anchors and all 48 unchanged/identity null
vectors to meet the existing cosine-distance ≤1e-5 / max-absolute-difference
≤5e-4 gates. Verify all 96 parent/mask/image hashes, native versus foreign source
controls, and foreign-minus-sham/null embedding-distance comparisons. Record
raw values and denominators; do not infer localization from a global vector or
infer foreignness from a decision change. Any drift, oracle, source or mask
failure stops interpretation; preserve partial artifacts and inspect before retry.
Freeze a new result receipt; do not edit the old protocol or overwrite outputs.

Contribution: determine whether pixel replacement produces a representation
effect beyond a whole-donor-vector intervention and matched native-source edits.
The pilot's four pairs cannot establish clinical sensitivity.

## B — 10,000 candidate image/control records

**Hypothesis:** foreign-source fragments cause a source-dependent representation
shift beyond matched native edits and seam-only perturbations, across doses,
host/donor grade directions, placements and editing styles.

`40 pairs × 5 patch sizes × 5 placements × 2 shapes × 5 variants = 10,000`.
Square sides 11,16,22,50,71 exported pixels correspond to approximately
0.24%,0.51%,0.96%,4.98%,10.05% of the 224×224 image; record realized physical
area from each source's measured MPP/native footprint, not an assumed 0.5 MPP.
The source field remains the existing approximately 112-µm export contract.
Fields, tile-bag dose and full-slide tissue dose remain different quantities.

Fixed centers are NW(.2,.2), NE(.8,.2), SW(.2,.8), SE(.8,.8), center(.5,.5).
First three require measured tissue; SE requires a tissue/background boundary;
center is the detached-background condition. A host tile is selected in fixed
hash order from at most 64 original unbiased exports using native mask/RGB
eligibility, never predictions. Detached placement requires every footprint
and two-pixel surrounding-ring RGB channel ≥240 **and** native labels all zero.
Mask label zero alone is background/unknown and is insufficient evidence.
If the predetermined condition is unavailable, exclude that matched group.

Donor and native-sham crops require ≥10% relevant native annotation at all five
sizes, background ≤50%; benign requires zero GP3/4/5, GG1 zero GP4/5. Slide grade
does not label every tile. Native sham comes from a different tile of the same
host slide. No physical rescaling, interpolation change or replacement slide is
allowed. Rectangles retain their complete source footprint. Irregular support
is the largest four-connected RGB-tissue component within the measured donor
crop; no dilation, gap bridging, invented physical boundary or mask-based disease
shape is used. Crop truncation and an RGB proxy remain limitations.

Five matched variants:

- Foreign paste: selected donor pixels inside the selected support.
- Native sham: host-source pixels with **identical donor support and geometry**.
- Seam-only: preserve host interior; perturb the one-pixel inner boundary by the
  foreign boundary's mean absolute contrast, recording realized contrast and
  clipping. This matches a scalar, not complete seam morphology.
- Unchanged: original RGB.
- Identity: cut/reinsert original destination pixels, required pixel-identical.

Save exact native crop boxes, source TIFF/PNG hashes, level-0 origins, measured
scale, group/pair/fold, requested/realized area, destination support, actual
changed pixels, donor RGB-tissue support and all native label fractions.
Foreign source footprint, RGB tissue and changed pixels are separate truths.
Controls' foreign masks are zero. Source support masks do not prove real-world
foreignness. A degenerate edit excludes its entire five-control group.

Deduplicate by canonical RGB bytes, retaining every logical record and group
mapping. Cross-fold duplicate pixels stop the job. At most 6,000 edited images
plus 155 unique hosts are expected from this schedule: **6,155 is a conservative
upper bound, not a measured exact count**. `completion.json` records exact
unique-image counts by split; no GPU scope uses 10,000 as an inference count.
Additional unchanged-anchor re-encodings are recorded as per-job overhead.

CPU gate: ≥8,000 rendered records, both shapes/all five sizes/all five contexts
represented in each fold, ≥3 unique hosts and donors per fold, verified scale,
labels and source hashes, no cross-fold collisions, <4 GiB output. Inspect
exclusion rates by grade/dose/context; a failed gate is a feasibility limitation,
not permission to fill missing cells. Coverage counts remain published even
if a smaller useful subset is proposed in a **new** protocol.

Costs: preparation capped at four CPUs/16 GiB/30 min (≤2 allocated CPU-hours).
Expected input hash/read volume is bounded to these 57 sources; no acquisition.
Up to 2,880 bounded candidate tile reads, plus small crops/metadata. Budget
<4 GiB for the generated set including masks/provenance. Historical CONCH jobs
give roughly 17.5–38.1 images/s including overhead, implying a rough 3–6 min
for ≤6,155 images; this is an extrapolation, not a measured new runtime.
The first 512-image batch profiles actual I/O/model/billing costs before scaling.
Profile cap 15 min; remaining fit/calibration/validation batches each cap 10 min.

Primary outcomes: foreign-minus-native paired embedding displacement and NN5
score differences by dose/context/grade/style; false-positive scores on shams,
seams and native cancer; source-level uncertainty. Report direction and effect
size even if null. Keep feature-only profiling separate from validation scoring.

Contribution: an auditable real-pixel benchmark that separates source effects,
native tissue edits, null edits and an explicitly limited seam control.

## C — dense and multiscale representations

**Hypothesis:** greater spatial coverage and context improve fragment mapping
without making native cancer appear foreign. Use the 12 separately selected
sources above; do not mix these with B's fit/calibration/validation sources.
Proposed fields 112,224,448 µm, 50%-field strides, separate per-scale contracts,
RGB-only tissue selection, up to 4,096 views/slide/scale = **147,456 maximum**.
The CPU coordinate/coverage manifest and exact retained/deduplicated count do
not yet exist. The old tiler has no overlapping-stride interface; **do not claim
it implements this study or submit a GPU job against invented tile directories**.
A separate bounded dense adapter/CPU preflight is the next C implementation gate.

Start with four source-disjoint profile slides selected by source hash, including
all three grade groups. Record TIFF geometry, realized fields/strides, overlap,
RGB occupancy, sampling holes and annotations after RGB selection. Compare
full low-resolution RGB connected components with sampled occupied cells and
native annotations; report observed split/merge/coverage errors and unevaluable
components. Do not bridge missing tiles or infer complete physical boundaries.
Preserve overlapping-view correlation and clipped component limits. Masks can
audit native-cancer coverage, not select clean evaluation tiles.

Profile GPU cap 30 min, then up to two hours for the full measured manifest;
CPU planning/export cap initially four CPUs/16 GiB/30 min, expand only after
measuring. Estimated image storage <25 GiB for 147,456 compressed 224-pixel
views is an unverified planning bound; use actual bytes/view before approval.
At historical38.1/s, 147k views alone imply about65 min; actual overhead is unknown.
Measure localization IoU/fragment recall at matched review burden, true native
cancer flags, clean prediction damage, and component exclusion evaluability.
The 112-µm scorer may be reused only after contract/drift checks; 224/448-µm
scoring requires validity confirmation, not silent transfer of old thresholds.

Go only if coverage mapping is reproducible, native cancer retained, partial
topology labeled, and the first profile forecasts completion within the cap.
Contribution: quantify how spatial coverage and physical context affect safety,
rather than treating denser tile count as an improvement by itself.

## D — small learned localization candidate

**Hypothesis:** a small frozen-feature detector distinguishes source inconsistency
beyond editing artifacts on source-held-out slides and a held-out editing style.
Compare frozen NN5/contextual similarity, decision dependence, a linear detector,
their predeclared combination, seam-only classifier and matched/permuted controls.
No backbone fine-tuning or second segmentation backbone at this stage.

First fit a fixed L2 logistic candidate on CONCH query features and the mean of
other local/slide-context features. Native ground truth is an evaluation target,
never an input. Do not feed variant names, masks, source IDs, coordinates encoding
edit location, dose, or clean-original feature differences to the detector.
Features are fit-standardized; regularization C=1, seed20261021, class-balanced
fit weights with equal total weight per source host; no hyperparameter sweep.
Fit and calibrate on rectangular edits only; irregular edits on validation
sources are a held-out style. Native/sham/seam/null and genuine annotated cancer
are negatives for **foreignness**, even when consequential to classification.

A global feature cannot localize pixels. Add at most 25 spatially recorded
windows per image on a predetermined, source-balanced 1,000-image subset,
≤25,000 new views, then map window scores to pixels with recorded coverage.
The subset/window manifest, crop geometry/scale and exact deduplication are
CPU gates still to implement; do not claim a segmentation model already exists.
GPU window encoding cap one hour; the small model fits/evaluates on CPU
(initial2CPUs/8GiB/20min). Disk planning <4 GiB windows; measure first.

Calibration selects the highest recall subject to alerts on ≤10% of unmodified
source slides and mean ≤0.5 flagged components/slide. Include genuine-cancer
flag counts separately. With only nine calibration sources, ≤10% allows **zero
observed alerted slides**; that is not a population guarantee. If no useful
threshold satisfies burden, retain the negative finding. A threshold with zero
foreign recall is not a useful operating point. Freeze one chosen policy or
declare no deployable policy; no selection using validation outcomes.

Report tile/window and fragment recall, precision, IoU with coverage/exclusion
denominators, unmodified source alerts, shams/seams flagged, genuine annotated
cancer flagged, burden, hypothetical prediction damage and recovery of newly
induced errors. Recovery denominator is originally correct hosts that acquire
an error; show initially incorrect hosts and ordinary prediction changes
separately. Oracle replacement must restore the exact baseline features and
prediction; any failure is a pipeline defect. No actual tissue deletion.

Go to more complex models only if predeclared paired source-bootstrap intervals
show improvement over the strongest simple baseline at the burden constraint
on held-out sources/style, without a corresponding seam/native-cancer failure.
Small sample uncertainty may prevent that conclusion. Contribution: test whether
frozen pathology representations support foreign-fragment localization that
generalizes beyond a particular compositor.

## E — external provider and one additional encoder

Current Karolinska proposal: 60 sources (20/group), catalog TIFF total
**3,512,683,208 bytes**. **0/120 image/mask files present** in checked intended
Delta paths; zero source-ID overlap with all189 known PANDA sources. No patient
independence established. No download authorized or started. The
[official PANDA reader](https://raw.githubusercontent.com/DIAGNijmegen/panda-challenge/main/notebooks/getting-started-with-the-panda-dataset.ipynb)
uses Radboud labels0/1/2/3/4/5 and Karolinska0background/unknown,1benign,2cancer;
Karolinska cannot supply GP3/4/5-specific truth. Header/pyramid, RGB-channel and
physical-mask compatibility are unverified. A provider-specific adapter and
pixel registration checks must pass before any frozen external evaluation.
Do not reinterpret historical fresh-Radboud60 results as a pristine external test.

Reserve up to one billed GPU hour, contingent on separate exact acquisition,
CPU input, model-validity and frozen-cohort authorization. Freeze the Radboud
model/detector before inspecting external predictions. Report source-level
performance, clean alerts and native-cancer harm; no post-outcome threshold fix.

Investigate **UNI2-h only** as the additional-encoder feasibility candidate.
The [official model card](https://huggingface.co/MahmoodLab/UNI2-h) specifies a
681M-parameter image encoder with 1,536-dimensional features and224-pixel
ImageNet-normalized input. Access/terms, local checkpoint/hash, pinned runtime,
preprocessing implementation and GPU memory profile are unverified. Keep its
image-only space separate from CONCH's512-dimensional projected image/text
space. It cannot use CONCH text prompts or vector thresholds. No download,
new adapter inference or fine-tuning is authorized here. After these gates,
propose at most a matched 1,000-image representation comparison with its own
source-disjoint small linear detector and physical-view contract, one-hour cap.

The historical PathGen branch remains read-only. Its documented architecture/
tokenizer discrepancy and missing verified weights remain unresolved; it is
not an additional executed comparison. Contribution of E: distinguish provider
and representation generalization from repeated within-provider synthetic tests.

## Provisional billing ceilings, not spending authorization

| Stage | Maximum billed A100-hour equivalents |
| --- | ---: |
| A existing pilot, five min interactive ×2 | 0.1667 |
| B first512 profile,15min batch | 0.2500 |
| B remaining ranges,3×10min batch | 0.5000 |
| C dense profile,30min batch | 0.5000 |
| C full dense,2h batch | 2.0000 |
| D window features,1h batch | 1.0000 |
| E Karolinska,conditional1h | 1.0000 |
| E UNI2-h,conditional1h | 1.0000 |
| **Total maximum** | **6.4167** |

Against8.4083 observed remaining this retains1.9917 equivalents. Running jobs
and other account activity can change it. Queue one GPU at a time, not a GPU
array or parallel encoders. Stop early when a question is answered or a validity
gate fails; allowances do not need to be consumed. Before each expansion, record
pre/post `accounts`, `jobcharge --detail --all`, root `sacct`, live QoS usage,
wall time, throughput, I/O, peak memory, failures and a recomputed remaining
budget. Require QoS delta = sum allocated billing-TRES×elapsed seconds, allowing
accounting propagation only by a later read-only check. Never infer billed
capacity from rounded `accounts` alone. Failed allocated jobs also consume quota.

## Executable handoff and freeze procedure

The stage receipt records the exact new source snapshot, archive/source-manifest
hashes, protocol hash, runtime and CPU command. New files are separate from the
historical scientific runtime; no old frozen file changes. Preparation is:

```sh
sbatch --parsable "$PROJECT/scripts/slurm/panda_pixel_program_prepare.sbatch" \
  "$PROJECT" "$RUNTIME" "$CONFIG_SHA256" \
  /work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-program-10k-v1-prepared
```

`PROJECT`, `RUNTIME` and `CONFIG_SHA256` in this template are resolved literally
in the execution report. No dependent GPU job is submitted automatically. This
batch CPU partition can prepare B while the old interactive pilot is queued.

After CPU completion, the **read-only** command prints exact proposed profile
and remaining batch commands with the actual CPU receipt hash and deduplicated
split ranges:

```sh
PYTHONPATH="$PROJECT/src" "$RUNTIME/bin/python" \
  "$PROJECT/scripts/panda_pixel_program_preflight.py" \
  --project "$PROJECT" --runtime "$RUNTIME" --config-sha256 "$CONFIG_SHA256"
```

It emits no GPU commands if feasibility fails. Proposed profile is first512 fit
images,15min batch; subsequent fit remainder, calibration, validation are
nonoverlapping exact ranges,10min each, sequential after billing reconciliation
and explicit scope approval. The generic GPU script checks the actual CPU
receipt/manifest and PNG/RGB hashes, existing checkpoint/provenance and unchanged
anchors before encoding. Outputs carry pixel hashes, float32 normalized512D
features, model/preprocessing contract, source/config/receipt pins, job and
timing. It runs no predictions. It cannot silently invoke another encoder.

C/D/E commands **must not yet be materialized with invented manifests**. Freeze
their measured coordinate/window/provider/encoder inputs and source revisions,
then use verified `gpuA100x4`/`bfqi-delta-gpu`/`bfqi-delta-gpu-mhoda`,oneA100,
4CPUs,16GiB and the respective table caps with the existing encoding batch
infrastructure only after its per-view input contract is validated. They are
gated subsequent deliverables, not executable submitted experiments today.

## Analysis freeze, reproducibility and stop rules

Save immutable config, source-manifest/hash and parent commit, source image/mask
checksums, selected rows/pairs/exclusions, true coordinates/scales/support masks,
dedup map, encoder/preprocessor/checkpoint/tokenizer/runtime hashes and seeds.
Before detector training, create a versioned analysis lock with predictor and
detector parameters, feature contracts, fold/style membership, calibration rule,
threshold, match rules, primary endpoints and exact input hashes. Commit that
lock before a single source-held-out validation evaluation. Archive all failures,
raw paired predictions/scores and confusion counts; preserve prior negatives.

Use seed20261021 and2,000 host-source cluster bootstrap replicates for95%
intervals, keeping every matched dose/placement/sham for a source together.
Also resample unique donor sources in a two-way sensitivity analysis because
donors repeat. Report unique hosts, donors, overlap, unavailable patient IDs and
per-grade/context exclusions. Do not treat10,000 records as10,000 independent
biopsies. Primary endpoints and subgroup counts are declared above; exploratory
analyses are labeled, no threshold/scorer switch after validation outcomes.

No automatic final-test evaluation, original-test label/prediction access, human
expert judgments, tissue deletion, bulk download, second-encoder execution or
backbone training occurs in this preparation. A null finding, insufficient
eligible pixels, seam confounding, a burden failure or exhausted safe budget
is an acceptable scientific outcome and stops escalation.
