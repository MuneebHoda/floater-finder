# Parallel 10,000-record CPU preparation — submission receipt

**CPU job `23109667` was submitted once at 19:07:42 CDT on October 21.**
It is PENDING (Priority); the actual job has no scheduler start estimate yet.
No real image preparation, checkpoint rehash or new inference is complete.
The existing pilot CPU `23109277` and GPU `23109340` remain pending and untouched.

The user restored their manual connection. The local host is Darwin, and the
one shared-connection test confirmed `mhoda` on
`dt-login03.delta.ncsa.illinois.edu`. No password/Duo automation or SSH edits.

## Verified staging and admission

- Separate source snapshot:
  `/u/mhoda/floater-finder/releases/panda-pixel-program-v1-479238282837/source`.
- All **73 staged files** match their frozen SHA256 values.
- Source manifest SHA256:
  `479238282837d51818b72a612118dc999e0a85b9f2082a5896968d7f6b5da00a`.
- Source archive SHA256:
  `77708c9a486ed661bbee378438c2368fa12c5e827a053b7aecb31592123ed48f`.
- Protocol SHA256:
  `8e4f4b6683d1647b94b7e5168205ce30e2ff6fcd4aa78fcb4ae95357d9ef85a9`.
- Parent commit: `7b337832ef1dcd21737eb0d5475ff975e2939358`. This new source is an
  uncommitted working-tree snapshot; no new commit or push is claimed.
- The prepared Delta runtime imports and read-only protocol/source preflight
  passed. It correctly reports CPU completion pending and GPU unauthorized.
- Slurm accepted the exact CPU script with `--test-only`, including exclusion
  of `cn018`, where the prior pilot attempt stalled in prolog.
- Slurm also accepted a **test-only** one-A100/four-CPU/16-GiB/15-minute request
  on `gpuA100x4` under `bfqi-delta-gpu` / `bfqi-delta-gpu-mhoda`. That confirms
  current scheduler admission for the proposed resource shape. Test-only IDs
  are not submitted jobs; **no new GPU job was submitted**.

## Queue availability is the immediate limitation

At 19:06 CDT, the advisory test-only forecasts were October 26 at 23:14:58 for
normal CPU batch and October 29 at 04:56:37 for normal A100 batch. The exact CPU
script test forecast October 26 at 23:15:58. These are scheduler estimates, not
reservations or guaranteed starts; the actual submitted job initially reports
N/A. The forecasts extend beyond the October 21 deadline. Configured access and
remaining allocation do not imply usable wall time before the deadline.

The GPU balance is unchanged at **8.4083333 batch-A100-hour equivalents**:
95,500 of 600,000 billing-TRES minutes used, no currently running GPU allocation.
The already queued five-minute interactive pilot could consume up to 0.1667
equivalents when it runs. Interactive A100 has a 2× billing weight; a future
switch would require an updated exact scope and budget before authorization.
No queue workaround, cancellation, duplicate pilot or automatic GPU escalation
was attempted.

## Exact submitted CPU command

```sh
sbatch --parsable --exclude=cn018 /u/mhoda/floater-finder/releases/panda-pixel-program-v1-479238282837/source/scripts/slurm/panda_pixel_program_prepare.sbatch /u/mhoda/floater-finder/releases/panda-pixel-program-v1-479238282837/source /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z 8e4f4b6683d1647b94b7e5168205ce30e2ff6fcd4aa78fcb4ae95357d9ef85a9 /work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-program-10k-v1-prepared
```

Verified resources: `bfqi-delta-cpu` account/QoS, `cpu` partition, one node,
four CPUs, 16 GiB, 30-minute cap, zero GPUs. The job has no dependency on the
original pilot. Its work can proceed independently when scheduled.

Intended output:
`/work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-program-10k-v1-prepared`.
Intended log: `/work/nvme/bfqi/mhoda/panda-pixel10k-gate-23109667.out`.
Expected records, masks, RGB deduplication, source facts and CPU/model-hash
completion receipt are described in the [frozen plan](../docs/panda_gpu_research_program_v1.md).
The exact real eligible and unique inference counts remain unknown until this
job succeeds; 10,000 is the frozen candidate count.

Remote exclusive receipts preserve the one-attempt handoff:

- Intent: `panda-review/pixel-program-10k-v1-submission-intent.json`, SHA256
  `4decf5c5e8ba7c04d6587be50d89ec4f0aba65ae4835bb070d4fe81512b4fab8`.
- Submission: `panda-review/pixel-program-10k-v1-submission.json`, SHA256
  `8e21a2136cac41a0369d00e5d9c28772b9bc20f497411a6e1e53ee894ba54e16`.

Both receipt paths above are relative to
`/work/nvme/bfqi/mhoda/floater-finder/`.
[Local bounded submission metadata](panda_gpu_program_cpu_submission_v1.json)
records exact command/resources, staging hashes and scheduler replies.

The previously completed local verification remains **443 tests passing**;
no software changed during this submission. No image, mask, embedding, weights,
or detailed research outputs were downloaded. Original final-test predictions,
historical experiments and main remain preserved.

## Exact next read-only command

```sh
ssh -o BatchMode=yes ncsa-floater 'squeue --start -j 23109277,23109340,23109667 -o "%.12i %.12T %.22S %.28R"'
```

Inspect this existing job and its completion/failure receipt before any retry.
After successful CPU preparation, inspect exclusions/coverage and actual dedup
counts, then freeze the concrete profile scope. Its GPU submission still needs
explicit authorization.
