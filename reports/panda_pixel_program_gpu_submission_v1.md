# Stage B GPU profile submission

**GPU profile `23109849` was submitted once at 19:39:23 CDT on October 21.**
It is PENDING (Dependency), with zero elapsed time and no scheduled start.
No new CONCH inference or real pixel result is complete.

The user's “Okay I approve it” authorizes this benchmark's bounded profile and
conditional remaining encoding. The total ceiling is **45 normal-batch A100
minutes / 0.75 billed equivalents**: a 15-minute profile followed, after artifact
inspection and charge reconciliation, by at most three 10-minute ranges. The
remaining ranges are approved conditionally but **not yet submitted**. This
approval does not cover dense study C, learned-window stage D, external data,
another encoder, extra images or original final-test predictions.

## Exact submitted command

```sh
sbatch --parsable --dependency=afterok:23109667,afterany:23109340 --kill-on-invalid-dep=yes /u/mhoda/floater-finder/releases/panda-pixel10k-profile-launch-v1-a2589ae29beb/source/scripts/slurm/panda_pixel_program_after_cpu.sbatch /u/mhoda/floater-finder/releases/panda-pixel10k-profile-launch-v1-a2589ae29beb/source /u/mhoda/floater-finder/releases/panda-pixel-program-v1-479238282837/source /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z 479238282837d51818b72a612118dc999e0a85b9f2082a5896968d7f6b5da00a 8e4f4b6683d1647b94b7e5168205ce30e2ff6fcd4aa78fcb4ae95357d9ef85a9 23109667
```

Slurm verifies `bfqi-delta-gpu` / `bfqi-delta-gpu-mhoda`, `gpuA100x4`, one A100,
four CPUs, 16 GiB, 15 minutes, billing TRES1000. Both dependencies must resolve:

- CPU `23109667` must succeed. Failed CPU dependency requests cancellation.
- Existing pilot GPU `23109340` must terminate before this profile starts.
  This preserves at most one running GPU, including a failed/cancelled pilot.

The pilot CPU `23109277`, pilot GPU `23109340` and 10k CPU `23109667` were
unchanged and still pending at submission. No duplicate or automatic retry.

## Actual-input and scientific gates

The first range is `[0,min(512,actual_fit_unique_count))`, selected from the
CPU manifest's deterministic ordering. No calibration/validation prediction
is run. The actual CPU completion SHA256, deduplicated image count and range
length are **unknown while CPU preparation is pending**. The resolver freezes
them in an exclusive launch receipt before invoking the unchanged encode script.
It supplies no placeholder input hash.

The resolver rechecks all 73 scientific files, exact source/protocol/job identity,
real source kind, current checkpoint checksum from CPU verification, 57 source
fact hashes, 45/12 study source counts, eligibility gate, generated/excluded
denominators, actual dedup/split counts, a maximum6,155 unique images, and absence
of any prior profile output. Failed checks stop before encoder loading. The
unchanged encoder independently checks PNG/RGB hashes, the checkpoint, canonical
model/preprocessing/runtime, unit512D vectors and unchanged-anchor drift.

If CPU preparation exits zero with a failed scientific feasibility gate, the
GPU resolver will stop before inference; its brief allocated check may still
incur a charge. Do not equate scheduler CPU success with scientific validity.
No model download, refit, disease prediction, alert threshold or clinical result
is part of this profile.

## Frozen source, authorization and receipts

- Scientific source: 73 files at
  `/u/mhoda/floater-finder/releases/panda-pixel-program-v1-479238282837/source`.
- Scientific manifest SHA256:
  `479238282837d51818b72a612118dc999e0a85b9f2082a5896968d7f6b5da00a`.
- Frozen protocol SHA256:
  `8e4f4b6683d1647b94b7e5168205ce30e2ff6fcd4aa78fcb4ae95357d9ef85a9`.
- Launcher: five verified files at
  `/u/mhoda/floater-finder/releases/panda-pixel10k-profile-launch-v1-a2589ae29beb/source`.
- Launcher source manifest SHA256:
  `a2589ae29beb4fcaa2a05118678af48465b4553da89be8c3af659d555f6f69ca`.
- Launcher archive SHA256:
  `4312e571624043e2c4af178b78233a88971a7f7142bbbdb6a13f187b0286f8a2`.
- User authorization SHA256:
  `7693dbf2a9e45d8bd46525a817a91a5cd5392fec58b6b2a9e6ca3436eec39a3e`.
  [Scope and inspection rules](../docs/panda_pixel_program_gpu_approval_v1.md).
- Both snapshots are working-tree bundles from parent commit
  `7b337832ef1dcd21737eb0d5475ff975e2939358`, not new commits or pushes.

Relative to `/work/nvme/bfqi/mhoda/floater-finder/panda-review/`:

- Authorization: `pixel-program-10k-v1-gpu-authorization.json`.
- Submission intent: `pixel-program-10k-v1-profile-submission-intent.json`, SHA256
  `bb32d55d07f3e606410e2d14cf9b83579766b4b6fb59b2c947c27fb49b0b337d`.
- Submission: `pixel-program-10k-v1-profile-submission.json`, SHA256
  `131a56b54fa862463fc8fac1c112544ec5ef2922996f782803c612e2f5c3541a`.
- Intended actual launch receipt:
  `pixel-program-10k-v1-profile-launch-23109849.json` (does not exist yet).
- Intended profile output: `pixel-program-10k-v1-profile/` (not created yet).

Log: `/work/nvme/bfqi/mhoda/panda-pixel10k-profile-23109849.out`.
[Bounded scheduler/source submission metadata](panda_pixel_program_gpu_submission_v1.json).

## Billing, queue and verification

At 19:38 CDT, live partition weights remained CPU62.5 / memory16 perGiB /
GPU1000. At these resources the GPU dominates. Exact own-QoS balance remained
**8.4083333 batch A100-hour equivalents**, with95,500 of600,000 billing-TRES
minutes used and no running GPU. `accounts` displayed8 and `jobcharge` displayed
1.60 used. Pending reservations are not evidence of completed GPU usage.

The exact test-only request passed; its advisory batch forecast was October29
at04:50:37. The actual dependent job reports no ETA. Queue forecasts extend
beyond the October21 deadline; approval and remaining quota do not guarantee
timely capacity.

All **453 software tests pass** with warnings treated as errors (56.79s),
including ten new artificial receipt/dependency-launch tests. Shell syntax,
staged CLI help, exact scheduler admission, five launcher hashes and all73
original scientific hashes passed. No dependencies added or scientific runtime
changed. Main, earlier experiments and the original final test are preserved.
No local data/weights/images/masks/embeddings were downloaded.

## Exact next command and scaling gate

```sh
ssh -o BatchMode=yes ncsa-floater 'squeue --start -j 23109277,23109340,23109667,23109849 -o "%.12i %.12T %.22S %.28R"'
```

After actual CPU/profile completion, inspect the existing receipts and drift/
feature contracts, reconcile root-job charges and live usage, then materialize
the exact remaining deduplicated ranges within the approved30-minute remainder
ceiling. Do not request the same approval again within this unchanged scope.
Stop on missing/invalid artifacts, unexplained charges, a changed source/encoder,
or a forecast over the ceiling; inspect failures before any retry. Other research
workstreams remain separately gated.
