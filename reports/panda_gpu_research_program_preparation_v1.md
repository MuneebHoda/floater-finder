# Expanded GPU program: verified audit and prepared parallel CPU scope

**Follow-up:** authentication is restored, staging/admission passed, and CPU job **23109667** is submitted. [Current execution status and exact command](panda_gpu_program_cpu_execution_v1.md). The preparation history below is preserved.

Prepared on the local Mac on October 21. No data, weights, embeddings, or detailed
remote experiment outputs were downloaded. New code/manifests are separate from
the unchanged scientific runtime of the pending96-image pilot.

## Verified allocation

At 18:43:37 CDT, live QoS showed600,000 billing-TRES minutes deposited,95,500 used,
504,500 remaining: **8.4083333 batch A100-hour equivalents**. Root job history
exactly reconciled to5,730,000 raw billing seconds =1.5916667 used equivalents.
`accounts` rounded the balance to8; `jobcharge` displayed1.60 used because its
rows are rounded. Failed job23051627 is included in the charge ledger.
[Bounded audit and all ten charge rows](panda_gpu_program_metadata_audit_v1.json).

Current configuration: `gpuA100x4` isUP with48h maximum/1×GPU weight;
`gpuA100x4-interactive` isUP with1h maximum/2×GPU weight. Association permits
`bfqi-delta-gpu-mhoda` without a partition restriction. Historical noninteractive
A100 jobs completed under the exact association. **A fresh scheduler test-only
admission check did not run:** the shared SSH connection expired before its
remote command started. Do not confuse configured eligibility/historical usage
with a new successful scheduling test or available queue capacity.

The6.4167-equivalent staged plan, including the pending pilot's worst-case0.1667,
leaves1.9917 of the observed8.4083 for verification/reruns. These are provisional
ceilings; no new GPU scope has been authorized or submitted. The next profile
must reconcile live QoS and actual job charges before scaling.

## Actual source and benchmark counts

- 64 eligible masked original-training sources outside the existing pilot:
  22 benign,22 GG1,20 high-grade. Selected 57 deterministically,19/group.
- B:45 sources,27 fit/9 calibration/9 validation. C:12 separate sources,6/3/3.
- Forty predetermined within-fold pairs:24/8/8. Unique host/donor/source unions
  are18/18/27,6/8/9,7/6/9. No source crosses folds/studies or the eight pilot IDs.
- No known patient IDs. Original disease scorers already used these training
  sources; their predictions here cannot establish independent disease validity.
- 10,000 candidate records,2,000 matched groups. Real eligible count and exact
  deduplicated inference count remain **unknown until CPU preparation runs**.
  At most6,155 unique composite/host images under the frozen schedule, not a
  measurement. Five control types, five sizes/placements and two shapes retain
  exact source/pixel-mask provenance and measured physical areas.
- Karolinska 60 candidate sources have0 source-ID overlap with189 known sources;
  0/120 intended image/mask files exist.3,512,683,208catalog bytes are not acquired.
  Provider-specific mask semantics/scale checks and separate acquisition remain
  blockers. UNI2-h is feasibility only; no verified checkpoint/access/runtime.

[Full hypotheses, controls, stop/go rules, budget, uncertainty and phase gates](../docs/panda_gpu_research_program_v1.md).
[Frozen source list](../configs/panda_gpu_program_v1/sources.csv).
[CPU protocol and model/source fingerprints](../configs/panda_gpu_program_v1/protocol.json).

## Prepared execution snapshot

The local archive contains73 source/config/test/documentation/metadata files;
it contains no image/data payloads. It is a **working-tree snapshot**, not a new
commit. Parent commit is`7b33783`. Do not claim these new changes are committed,
pushed, staged on Delta or executed until the corresponding actions occur.

- Source manifest SHA256: `479238282837d51818b72a612118dc999e0a85b9f2082a5896968d7f6b5da00a`.
- Archive SHA256: `77708c9a486ed661bbee378438c2368fa12c5e827a053b7aecb31592123ed48f`,202,983 bytes.
- Protocol SHA256: `8e4f4b6683d1647b94b7e5168205ce30e2ff6fcd4aa78fcb4ae95357d9ef85a9`.
- Intended fresh Delta source:
  `/u/mhoda/floater-finder/releases/panda-pixel-program-v1-479238282837/source`.
- Existing runtime:
  `/work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z`.
- Intended new CPU output:
  `/work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-program-10k-v1-prepared`.

After manual reconnection, verify identity once, stage the separate snapshot,
verify every source byte, and test scheduler admission. Prepared exact CPU command:

```sh
sbatch --parsable /u/mhoda/floater-finder/releases/panda-pixel-program-v1-479238282837/source/scripts/slurm/panda_pixel_program_prepare.sbatch /u/mhoda/floater-finder/releases/panda-pixel-program-v1-479238282837/source /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z 8e4f4b6683d1647b94b7e5168205ce30e2ff6fcd4aa78fcb4ae95357d9ef85a9 /work/nvme/bfqi/mhoda/floater-finder/panda-review/pixel-program-10k-v1-prepared
```

This new `cpu` batch request is4 CPUs/16 GiB/30 minutes, no GPU or downloads,
maximum2 allocated CPU-hours. It can prepare B in parallel with the existing
pilot, independently of its results. The user authorized CPU preparation in
the current request; reconnection is a missing transport dependency, not a
request to approve the same CPU scope again. No duplicate pilot is submitted.

Expected CPU outputs:57 source-provenance JSONs, RGB-deduplicated PNGs,2,000 or
fewer matched support/changed-mask NPZs, `records.jsonl`, `exclusions.json`,
`unique_images.json`, and `completion.json` with actual counts/coverage/costs
and current checkpoint SHA256. A failure preserves partial output and writes
`failure.json`; never reuse an incomplete directory automatically.

The read-only preflight emits proposed exact GPU commands only after successful
CPU coverage/dedup gates. Those scopes require explicit authorization after
their actual counts and hashes are shown. C/D/E still require their additional
coordinate/window/provider/encoder input implementations and freezes; no
invented paths or scientific successes stand in for those gates.

## Existing pilot and connection state

Last successful scheduler check: CPU 23109277PENDING(Priority),GPU 23109340
PENDING(Dependency); no new inference/completion was observed. Runtime 276 files
and launcher 5 files were rehashed successfully. Current checkpoint rehash is
delegated to the new CPU job; the expected hash is historical verified evidence.

The next SSH command failed before execution with:
`Permission denied (gssapi-with-mic,password)`. Stopped remote work and requested
manual Mac Terminal/Duo reconnection; no authentication retry or credential
request. Immediate next command for the user:

```sh
ssh ncsa-floater
```

Software verification is recorded in the progress update after the final test
run. Scientific effects, real 10k eligibility, fresh scheduler admission and new
CPU execution remain unverified at this preparation handoff.

## Final local verification

All **443 tests pass** with warnings treated as errors (55.24s), including 11 new artificial-array tests and the complete 10,000-record fixture. An initial fixture accidentally reused identical native pixels; the production degeneracy gate excluded those groups as designed. The fixture was corrected to use distinct native-source pixels; no gate was relaxed. The first full run also found an out-of-date installed local package; an offline, dependency-free local reinstall corrected it. No network dependency or data download occurred.

Both new Slurm scripts pass shell syntax checks. The read-only preflight correctly reports CPU completion pending and GPU unauthorized. All 69 frozen source/config entries, all 73 archive entries, the entire historical pixel-study freeze, and main commit `bdb13e5ee2fd8f61bf4a1885e0c6771d1ce9f39e` verify unchanged. `git diff --check` passes. No commit, push, merge, remote authentication retry, new scheduler job or actual GPU experiment occurred in this preparation.
