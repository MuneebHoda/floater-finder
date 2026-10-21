# Four-pair pixel contamination preparation v1

CPU preparation **23109222 timed out after 613s in scheduler Prolog on cn018**,
with no Python step,log,preparation directory or real-image completion receipt
observed. Failure metadata is preserved. After inspecting that terminal
infrastructure failure, one bounded replacement **23109277** was submitted with
`--exclude=cn018`, identical frozen source/inputs/scientific parameters, and the
same per-job resource cap. Latest observed replacement status: **PENDING
(Priority)** as of2026-10-21 17:48:34CDT. Slurm estimates start at19:39:58CDT
on October21; estimates can change. No further replacement is prepared or authorized by this record.

The 96 real images are **not yet verified/prepared**; no new CONCH inference or
scientific effect has been measured. No GPU job was submitted. Do not duplicate
the pending job. The old timeout may remain in terminal scheduler cleanup; it
has produced no output and is not an active raster-processing attempt.

The existing compositor was audited and retained unchanged. A separate runner
adds native-mask crop verification, full source-TIFF/PNG identities, physical-scale
checks, independent raster/null checks, a frozen manifest, canonical CONCH drift
gates, and paired feature/prediction measurements.

## Fixed real source pairs

| Pair | Task | Host | Donor |
| --- | --- | --- | --- |
| pair-1 | S1 | `1f1440204eba45ff4f999795c7d52040` | `0e305c4d31f47db36c44a1d55d389193` |
| pair-2 | S1 | `291b2132e1fb9131478b8d691406874b` | `134d69e06d397dc06ed6794b737c63fd` |
| pair-3 | S2 | `14cff64d674f558dc47ee5e817b7f671` | `1b176c9049260a8843b97349ccdd3eb7` |
| pair-4 | S2 | `3901caec5d914bf20a44f176469b0294` | `2a6d0c4bd562bb83e9863a175af50de4` |

All eight IDs are original-training Radboud slides with masks present in the
verified cohort. Metadata-only discovery found host gallery candidates 10,2,12,1
and donor candidates 5,3,7,4 under the fixed annotation/background rule. These
are candidate counts, not actual crop eligibility. Exact selected tile IDs,
actual donor-crop GP3/4/5 fractions, WSI/PNG equality and output validity remain
pending the scheduled CPU step. Different slides are not verified patients.
Native sham uses an eligible crop from the original host tile at another image
location; it is not an identity cut/reinsert control.

## Frozen source and checks

- Runtime commit: `61959fa148a4a3ae4aadb5ee84b9578933140f6b` (local feature branch; not pushed by this stage).
- Immutable source: `/u/mhoda/floater-finder/releases/panda-pixel-contamination-v1-20261021T223344Z/source`.
- All **276** staged files verified against the source manifest.
- Source archive SHA256: `9088f8a1ee3420e871aee140bb7f5ecc31010f3fad4f4cfa473b96a6c120b4e3`.
- Source manifest SHA256: `573c26663c3dec96b080c3f186573c513c39ff3408e469dc64f501140e894618`.
- Protocol SHA256: `33594b467bdd16c75e3b4835a744bab2e917972266a31e33779ac0be386eefb7`.
- Existing runtime: `/work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z`, site module `pytorch-conda/2.8`.
- **424 software tests pass**, including eight new pixel-study tests and the
  unchanged compositor tests, with warnings as errors. The 96-image fixture is
  artificial software evidence only. Slurm scripts pass `bash -n`.
- Local/Delta source/model-metadata/input-hash preflight passed without inference.
  All 33 original-final runtime files and local main remain unchanged; original
  final-test predictions remain sealed.
- The original verified CONCH v1 checkpoint remains pinned at SHA256
  `40a9644b9ba0e83a74576e0a5e5f7313599fa9c9cdaf3c20f8a3e271b0e9ae7c`.
  No checkpoint was loaded or rehashed in the metadata-only login-node preflight.
  The GPU runner must rehash it before inference and enforce the old provenance.

## CPU command and pending acceptance

One CPU-only job: account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`,
two CPUs,8GB,ten minutes,zero GPUs. No downloads. Exact submitted command:

```sh
sbatch --parsable /u/mhoda/floater-finder/releases/panda-pixel-contamination-v1-20261021T223344Z/source/scripts/slurm/panda_pixel_prepare.sbatch /u/mhoda/floater-finder/releases/panda-pixel-contamination-v1-20261021T223344Z/source /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z 33594b467bdd16c75e3b4835a744bab2e917972266a31e33779ac0be386eefb7 /work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-contamination-v1-prepared 61959fa148a4a3ae4aadb5ee84b9578933140f6b
```

Inspected CPU-only replacement command (already submitted once):

```sh
sbatch --parsable --exclude=cn018 /u/mhoda/floater-finder/releases/panda-pixel-contamination-v1-20261021T223344Z/source/scripts/slurm/panda_pixel_prepare.sbatch /u/mhoda/floater-finder/releases/panda-pixel-contamination-v1-20261021T223344Z/source /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z 33594b467bdd16c75e3b4835a744bab2e917972266a31e33779ac0be386eefb7 /work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-contamination-v1-prepared 61959fa148a4a3ae4aadb5ee84b9578933140f6b
```

Timeout receipt: `/work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-contamination-prolog-timeout-23109222.json`,
SHA256 `23eaf0c7a7e3dc144f7f4caa3dfe365e18af857724a19871374ebd86f901c22b`.
This is an inspected infrastructure recovery, not an outcome-selected rerun.
No crop or source was substituted; the preparation path was verified absent
before replacement. Old requested cap was600s; observed scheduler elapsed613s
includes setup/timeout handling, not measured Python processing.

Intended new output: `/work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-contamination-v1-prepared`.
At successful completion require exactly 96 images/24 matched groups,48
pixel-identical unchanged/nulls,24 foreign and24 native-sham images; separate
target/foreign/actual-change masks; all donor crops annotation-positive; equal
physical scales; no clipping/rescaling; immutable manifest/completion receipts.
Preserve partial failures. Do not assume receipt existence from Slurm RUNNING.

Handoff receipt: `/work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-contamination-pending-handoff-v1.json`,
SHA256 `19bd59119e4b5562e52ccf324ac83dfdda721b2426276fe55071a8594d1ece75`.

## GPU preparation remains approval-blocked

The prepared wrapper is `scripts/slurm/panda_pixel_encode.sbatch`: one A100,
four CPUs,16GB,five minutes maximum (0.0833 GPU-hour), account
`bfqi-delta-gpu`,QoS `bfqi-delta-gpu-mhoda`,partition
`gpuA100x4-interactive`. No new weights,slides,models or downloads.

CPU-side dependency/runtime checks that require the actual reader are also
pending; no dependency installation is planned. The exact executable GPU
command cannot be finalized until the real image manifest
exists and its SHA256 is verified. **Do not request or infer GPU approval from
this pending CPU job.** The intended encoding output is `/work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-contamination-v1-encoded`.
Eight unchanged source anchors must pass cosine-distance <=1e-5 and maximum
absolute difference <=5e-4 against saved embeddings before the96 composites;
48 null/unchanged vectors face the same gate before measurements.

Frozen measurements cover host/composite/full-donor cosine distances; paired
foreign-minus-sham/null changes; all four morphology text similarities/deltas;
fixed primary and historical S1/S2 slide predictions after one-slot replacement;
separate full-donor append/replacement comparisons; native-context NN5 ranks.
Patch area and sampled-bag edited-tile fraction remain different quantities.
No refitting,threshold search,tissue removal or pixel localization claim.

Hard rectangular boundaries remain confounded: native paste matches geometry
and interpolation but not morphology; unchanged and identity nulls do not match
seams. No separate seam-matched or irregular-mask study was added. Four
training pairs and repeated images are mechanistic feasibility,not clinical
sensitivity or independent validation.

[Complete frozen protocol and measurement/interpretation rules](../docs/panda_pixel_contamination_v1.md).

Exact next read-only command from the Mac:

```sh
ssh -o BatchMode=yes ncsa-floater 'sacct -j 23109277 --format=JobID,State,ExitCode,Elapsed,AllocCPUS,MaxRSS -P'
```

No pixel,mask,NPZ,weights or detailed result file was downloaded to the Mac.
No presentation work,expert-review paperwork,original test evaluation or GPU
submission occurred.
