# Four-pair pixel contamination feasibility protocol v1

This version responds to the user's October 21 pixel-reencoding instruction. It
reuses the bounded compositor without changing historical code, experiments,
models, cohorts or final-test gates. The original 24 test predictions remain
sealed. All real pixels, masks, arrays and detailed results stay on Delta.
CPU preparation is authorized by this request; GPU execution requires separate
explicit approval after the exact prepared manifest and command are reported.

## Fixed sources and scope

Four pairs are selected before new pixel effects: first two slide-ID-sorted
original-training benign hosts, first two GG1 hosts, and first four sorted
ISUP4/5 donors. Native masks are mandatory. No replacement pair is selected if
eligibility fails. This is eight different slides, not eight verified patients.

| Pair | Task | Host | Donor |
| --- | --- | --- | --- |
| 1 | S1 benign/cancer | `1f1440204eba45ff4f999795c7d52040` | `0e305c4d31f47db36c44a1d55d389193` |
| 2 | S1 benign/cancer | `291b2132e1fb9131478b8d691406874b` | `134d69e06d397dc06ed6794b737c63fd` |
| 3 | S2 low/high | `14cff64d674f558dc47ee5e817b7f671` | `1b176c9049260a8843b97349ccdd3eb7` |
| 4 | S2 low/high | `3901caec5d914bf20a44f176469b0294` | `2a6d0c4bd562bb83e9863a175af50de4` |

Only previously exported gallery PNGs are eligible. Candidate tiles have relevant
native-mask fraction >=0.1 and background <=0.5; benign hosts/crops contain no
annotated cancer and GG1 hosts/crops contain GP3 and no GP4/5. Donors require
GP3/4/5 for S1 and GP4/5 for S2 at every actual crop. Candidates are ordered by
SHA256(seed `20261027` / slide ID / tile ID), never model responses. Select the
first eligible of nine fixed anchors, checking all three nested crops. Search
is capped at 64 candidate exports per source, with at most 3x3 crop anchors.

Source crop sides are 22,50,71 pixels in a 224-square host: realized patch area
is approximately 0.965%,4.982%,10.047%, separately recorded from nominal
1%,5%,10%. Upper-left destinations start at normalized `(0.125,0.125)`;
lower-right at `(0.55,0.55)`. Python round-to-even fixes integer geometry.
Destination width and height exactly equal source crop dimensions. The existing
bilinear resize is an identity at equal size, independently pixel-checked.
No magnification change, clipping, feathering or color harmonization is allowed.

Native sham uses an eligible crop from the original host tile, moved to a
different destination rectangle. It is not the target rectangle cut/reinserted.
Each of 4 pairs x3 doses x2 destinations has foreign, native-sham, unchanged and
identity cut/reinsert variants: exactly **96 images**, plus their three distinct
pixel masks. Nulls intentionally repeat source pixels across conditions.

## CPU validity checks and freeze

One bounded CPU Slurm job uses two CPUs,8GB,ten minutes,
`bfqi-delta-cpu` account/QoS,`cpu-interactive`. No inference or new acquisition.

Checks include the pinned original cohort/embedding receipts, original image and
mask TIFF full SHA256, original PNG versus gallery and encoder-input hashes,
source metadata/coordinate order, native mask fractions versus saved CSV, and
bounded rereading of the exact original WSI tile to establish RGB equality.
Image/mask dimensions,pyramid factors,orientation and channel0 labels0..5 must
match. This is geometry verification, not histological registration proof;
mask resolution tags differ, so image geometry and measured image MPP are used.

Crop annotation fractions integrate exact native-label pixel-area overlap with
continuous crop boundaries mapped from the exported 224-grid to the native
230-grid. Labels are never bilinearly interpolated. Exact native label maps are
saved separately from compositor foreign/target/actual-change masks. These
annotations select/evaluate sources; no annotation or provenance enters NN5.

Host/donor measured MPP, native footprint, physical field and export dimensions
must agree exactly. Each source retains slide/tile ID,index,coordinates,physical
scale,full TIFF and PNG hashes,mask hashes,crop geometry and native fractions.
Every image/mask is independently checked after composition. All null pixels
must equal the original. Foreign footprint remains positive even if pasted RGB
matches some host pixels; actual changed pixels are a separate mask.

Preparation refuses existing output. A failure preserves partial output and a
failure record; no automatic retries or substitution. `completion.json` pins
all prepared files,including `image_manifest.json`. That manifest's SHA256 is
an exact GPU argument. Source/runtime,checkpoint,prompts,preprocessing,model
heads,output schema and drift tolerances freeze before any GPU outcome.

## GPU request and reproducibility gate

One A100,four CPUs,16GB,at most five minutes (0.0833 GPU-hour maximum),
account `bfqi-delta-gpu`,QoS `bfqi-delta-gpu-mhoda`,partition
`gpuA100x4-interactive`. No new weights,data,encoder or model training.
Existing checkpoint SHA256:
`40a9644b9ba0e83a74576e0a5e5f7313599fa9c9cdaf3c20f8a3e271b0e9ae7c`.
Runtime is the verified prepared private PANDA environment with site
`pytorch-conda/2.8`; no installation or dependency update.

Use unchanged `ConchEncoder`: canonical 448-pixel bicubic resize,center crop,
RGB,tensor,CONCH normalization; projected,normalized float32 512D image vectors.
Seed0;TF32 off;batch16;one CUDA GPU. Upstream Python source/version hashes and
adapter hashes must match old receipts, as must full encoder provenance.
Morphology prompts/text fingerprint are unchanged; reuse saved text vectors.

First re-encode the eight unmodified source tiles (four hosts,four donors) and
compare each with its saved vector. Require cosine distance <=1e-5 and maximum
absolute coordinate difference <=5e-4. Write the drift diagnostic and stop before
composites if any fails. Do not relax tolerances after failure. Then encode the
96 images and independently apply the same gate to all 48 unchanged/null image
vectors before scientific measurement. Total bounded encoding:104 images.

Outputs: `anchors.npz`,`unchanged_drift_gate.json`,`embeddings.npz`
(96x512 float32 vectors and opaque row IDs),`null_control_drift_gate.json`,
`measurements.json` and immutable file-hash completion receipt. Source/protocol/
manifest hashes,jobID and actual timing accompany measurements. Opaque vector
rows keep ground truth separate; the signal callable accepts query/reference
vectors only. No detector sees intervention names,source IDs or ground-truth masks.

## Frozen measurements and interpretation

For every image retain original-host cosine distance,full-donor-tile distance,
all four unchanged morphology image/text similarities and deltas,NN5 anomaly,
native-control percentile,raw clean and intervened slide predictions,and explicit
decision changes. NN5 compares the query to the host bag excluding the edited
slot. Native control scores are leave-one-out scores for the other original
host tiles; reference counts differ by the identity exclusion. Ranking is
descriptive,with no new threshold or validated foreignness alert.

Both training-selected linear primaries and historical zero-shot S1 top5pct /
S2 mean comparators stay fixed. These source slides were training data for the
linear heads, so this is mechanistic resubstitution, not model validation.
No cancer inference is made from slide grade at every tile.

Replace exactly the original host tile's vector with its reencoded image and
retain bag coordinates and other vectors. Separately calculate whole donor-tile
replacement and append on these exact sources. These full-tile interventions
are new matched engineering comparisons, not reruns of completed S1/S2 draws.
They use 1 donor vector,not 1/5/10% of host tiles. Record edited-tile percentage,
patch percentage,and edited physical area separately; sampled-bag area is not
whole-slide tissue area. Full donor-tile similarity includes surrounding donor
context; this run does not encode an isolated donor crop.

At each pair/dose/destination,subtract native-sham,unchanged and identity-null
effects from foreign effects. Preserve all raw values and 24 matched comparison
sets. Inspect within-pair dose and placement consistency without selecting an
anomaly threshold or switching a scorer. Report four source-pair outcomes and
two pairs/task; 96 repeated/control images are not independent patients. No
clinical sensitivity estimate,success cutoff or causal foreignness proof is
supported by this sample. No automatic removal is performed.

**Hard rectangular seams are a major confound.** Identity edits do not match
seams. Native paste matches boundary geometry/interpolation but may have very
different morphology and contrast. No separate seam-matched or irregular-mask
control is claimed or silently added. Foreign>sham is only feasibility evidence
under this caveat. A convincing consistent signal motivates a separately scoped
preregistered irregular-mask/background-fragment study; artifact-dominated
results require redesign; absent robust signals remain a negative finding and
may indicate loss of small-patch information in a single CONCH vector. All next
decisions require the observed measurements; none is asserted in advance.

Exact staged source,manifest hash,commands,observed CPU results and pending GPU
approval are recorded in `reports/panda_pixel_contamination_preparation_v1.md`.
