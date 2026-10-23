# Pixel GPU submission v1

**GPU job23109340 is submitted and PENDING (Dependency)** as of2026-10-21
17:55:22CDT. It waits for **CPU23109277 to finish successfully**. CPU preparation
is still PENDING (Priority); its real96-image manifest does not exist yet.
The scheduler reports `afterok:23109277(unfulfilled)`. No new CONCH inference
or pixel-level scientific effect is verified. No further CPU/GPU job was submitted.

The user's instruction “Submit GPU execution and commit the code” explicitly
authorizes the proposed bounded GPU job while preparation is pending. This
record supersedes earlier approval-pending notes. The dependency and receipt
checks preserve CPU validation before actual model inference; queue submission
is not a claim that preparation succeeded.

## Exact submitted command

```sh
sbatch --parsable --dependency=afterok:23109277 --kill-on-invalid-dep=yes /u/mhoda/floater-finder/releases/panda-pixel-gpu-launch-v1-20261021T225437Z/source/scripts/slurm/panda_pixel_after_cpu.sbatch /u/mhoda/floater-finder/releases/panda-pixel-gpu-launch-v1-20261021T225437Z/source /u/mhoda/floater-finder/releases/panda-pixel-contamination-v1-20261021T223344Z/source /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z 33594b467bdd16c75e3b4835a744bab2e917972266a31e33779ac0be386eefb7 573c26663c3dec96b080c3f186573c513c39ff3408e469dc64f501140e894618 23109277 61959fa148a4a3ae4aadb5ee84b9578933140f6b
```

Slurm verified: account `bfqi-delta-gpu`,QoS `bfqi-delta-gpu-mhoda`,partition
`gpuA100x4-interactive`,one GPU,four CPUs,16GB,five minutes. Nominal maximum
GPU reservation0.0833 GPU-hour; no running GPU allocation has begun.
`--kill-on-invalid-dep=yes` requests cancellation if CPU success becomes
impossible. The existing CPU job remains untouched. Do not submit duplicates
or automatically retry either stage. Old CPU23109222's prolog timeout remains
preserved; its terminal cleanup on cn018 was still visible at verification.

## Verified source and preparation gates

- Launcher code commit: `1b4d19b39c3535a326bc6b00ef497f857e440cf7`.
- Launcher source: `/u/mhoda/floater-finder/releases/panda-pixel-gpu-launch-v1-20261021T225437Z/source`; all **5** staged files verified.
- Launcher archive SHA256: `171c24d398f51717bf32a0d3ddbf4739de7a6d0081dbc1141e79faa3f0b7a8d0`.
- Launcher source-manifest SHA256: `a7738f5eb9f14c64ac0b13d278da74811b0a25f962ff365e0521a16df20c9528`.
- Scientific runtime commit: `61959fa148a4a3ae4aadb5ee84b9578933140f6b`.
- Scientific runtime source: `/u/mhoda/floater-finder/releases/panda-pixel-contamination-v1-20261021T223344Z/source`; all **276** files reverified.
- Original runtime source-manifest SHA256: `573c26663c3dec96b080c3f186573c513c39ff3408e469dc64f501140e894618`.
- Original protocol SHA256: `33594b467bdd16c75e3b4835a744bab2e917972266a31e33779ac0be386eefb7`.
- Runtime: `/work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z`, module `pytorch-conda/2.8`.
- **432 software tests pass** with warnings as errors, including eight new
  dependency-launcher tests; all source/scientific parameters and33 legacy
  final-test runtime files remain unchanged. Main is preserved.
- Metadata/model/input preflight passed without inference; Slurm `--test-only`
  accepted the request before the one actual submission. The historical
  runtime CLI's hard-coded `gpu_submission_authorized:false` display is its
  old metadata-only status; current authorization is the user's instruction
  and separate receipt,not a changed frozen scientific setting.

The launcher first verifies the pinned original source,successful CPU receipt,
exact jobID/source/protocol/four pairs,all prepared image/mask hashes,and absence
of GPU output. It then freezes the **actual** manifest SHA256 in a new exclusive
receipt and invokes the unchanged CONCH runner. Missing or changed inputs stop
it. No placeholder manifest hash is supplied and no tile/pair is substituted.
The manifest hash remains **unknown at submission** until CPU preparation
materializes it; this is explicitly distinct from a completed real-data preflight.

The original runner still checks the checkpoint hash and canonical environment,
encodes eight unchanged source anchors first,stops on drift,then encodes96
composite/control images and checks48 null vectors before frozen measurements.
No encoder/model inference occurs on the login node or in the resolver.

## Paths and immutable receipts

- Intended CPU output: `/work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-contamination-v1-prepared` (not present at submission).
- Intended GPU output: `/work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-contamination-v1-encoded` (not present at submission).
- GPU log: `/work/nvme/bfqi/mhoda/panda-pixel-encode-23109340.out`.
- Authorization receipt: `/work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-contamination-gpu-authorization-v1.json`, SHA256 `f9a65f554ceac54de9f09d2c236dea14c029473ee6bc9740d06eab132e6e1aa6`.
- Submission verification: `/work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-contamination-gpu-submission-v1.json`, SHA256 `ae335245be448ce3633bdade6844f285f96d9ff025fa188d6c42f573d0974886`.
- At actual launch,the exclusive sibling receipt will be
  `pixel-contamination-gpu-launch-23109340.json`; it does not exist yet and
  will record the verified real image-manifest/CPU-completion hashes.

Frozen measurements retain host/composite/full-donor feature shifts,foreign-minus-
sham/null comparisons,morphology similarities,fixed primary/historical S1/S2
slide predictions after one-slot replacement,separate whole-donor append/
replacement comparisons and native NN5 ranks. Patch area and sampled-bag dose
remain distinct. Four source pairs are not independent clinical sensitivity
evidence. Rectangular boundary artifacts remain confounded; no pixel localization
or automatic tissue removal is claimed.

[Original preparation and exact four pairs](panda_pixel_contamination_preparation_v1.md).
[Dependency launcher and preserved gates](../docs/panda_pixel_gpu_submission_v1.md).

Exact next read-only command from the Mac:

```sh
ssh -o BatchMode=yes ncsa-floater 'sacct -j 23109277,23109340 --format=JobID,State,ExitCode,Elapsed -P'
```

No local payload downloads,new data/weights,additional model,refitting,threshold
selection,presentation work,expert-review paperwork or original final-test
evaluation occurred. The original test remains sealed.
