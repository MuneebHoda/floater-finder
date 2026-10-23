# Approved Stage B GPU scope — October 21

The user's “Okay I approve it” authorizes the bounded CONCH GPU stage for the
10,000-candidate pixel benchmark described immediately beforehand. It covers
the profile and the remaining exact deduplicated ranges after successful
inspection and billing reconciliation. It does not authorize the full expanded
research program, additional encoders, external acquisition or larger cohorts.

The scientific protocol remains frozen at SHA256
`8e4f4b6683d1647b94b7e5168205ce30e2ff6fcd4aa78fcb4ae95357d9ef85a9`.
The unchanged 73-file source manifest is
`479238282837d51818b72a612118dc999e0a85b9f2082a5896968d7f6b5da00a`.
The actual CPU completion/manifest hashes and exact inference count are still
unknown while CPU job `23109667` is pending. The new resolver freezes those
actual hashes before any inference; it supplies no placeholder receipt hash.

[Versioned authorization receipt](../configs/panda_gpu_program_v1/approval_gpu_benchmark_v1.json)
SHA256: `7693dbf2a9e45d8bd46525a817a91a5cd5392fec58b6b2a9e6ca3436eec39a3e`.

## Resource ceiling and order

- Profile: up to 512 unique **fit-source** images, one A100, four CPUs, 16 GiB,
  15-minute limit on `bfqi-delta-gpu` / `bfqi-delta-gpu-mhoda` / `gpuA100x4`.
- Remaining encoding: at most three sequential nonoverlapping ranges (fit
  remainder, calibration, validation), 10 minutes each on the same resources.
  Total profile plus remainder ceiling: **45 batch-A100 minutes = 0.75 billed
  equivalents** at the verified 1× GPU weight.
- Maximum scope: the eligible subset of 10,000 candidate records, no more than
  6,155 unique RGB images; record per-job unchanged-anchor overhead separately.
- Run at most one GPU at a time. The profile's scheduler dependencies require
  `afterok:23109667` and `afterany:23109340`, combined with AND. It cannot overlap
  the already approved pilot GPU job. Request cancellation for invalid CPU
  dependency. Leave the two original pilot jobs and CPU preparation untouched.

The queue submission uses a separate launcher snapshot. The 73-file scientific
runtime and its frozen encode script are unchanged. The resolver requires the
exact CPU job, real source kind, verified checkpoint hash, 57 source facts,
45/12 study split, passing eligibility gate, aligned actual dedup denominators,
all output-manifest hashes and no prior GPU profile output. It then writes an
exclusive launch receipt and invokes the unchanged canonical CONCH encoder on
fit range `[0,min(512,actual_fit_unique_count))`.

If CPU preparation fails, Slurm cancels the dependent profile. If preparation
exits successfully but the scientific feasibility gate fails, the resolver
stops before a model call; that allocated check can still incur a small charge.
Preserve failures and inspect them before any retry. Identity/anchor drift,
checkpoint or preprocessing mismatch also stops encoding. No hidden download,
new text space, new cancer model, prediction scoring or final-test execution.

## Required inspection before scaling

After the profile succeeds, verify feature shape/norms, RGB/record correspondence,
unchanged-anchor drift, exact source/model/preprocessing/CPU pins, wall time and
throughput. Reconcile `sacct` root-job billing TRES × elapsed seconds against
`jobcharge --detail --all` and live own-QoS usage. Include any pilot use and
allocated failures in the updated balance. Forecast all remaining ranges and
anchor overhead against the **remaining** approved 30-minute ceiling. Stop on
an unexplained billing difference, invalid artifacts or a forecast above the
ceiling. Do not silently enlarge wall time, change partitions/charge factors,
relax validity gates, add images or rerun failed work.

The existing read-only command can materialize exact remainder ranges after
successful CPU preparation; its static `GPU_authorized:false` and phase labels
reflect the earlier pre-approval preparation. Current authorization comes from
the user and the separate versioned receipt above. No repeated approval is
needed within this unchanged conditional Stage B scope. Remaining jobs are
not submitted until the profile inspection and billing gate pass.

The 6.4167-equivalent expanded-program allowance remains provisional. Dense
study C, learned-window GPU stage D, Karolinska and the second encoder remain
outside this approval. CPU eligibility, actual image count, current model rehash,
profile success and measured charges are observations still to establish.

The execution report records the literal staged launcher paths, all source
hashes, exact submitted command, job ID and scheduler state. Batch queue delays
remain separate from the 45-minute compute ceiling; no completion date is
guaranteed by this authorization.
