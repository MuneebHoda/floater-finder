# Fresh Radboud60 — verified Delta-only CPU intake

The approved acquisition and all six serialized CPU chunks completed successfully
with exit `0:0`. **60 slides / 25,915 tiles / 60 masks** passed the full metadata
verification gate. No fresh GPU encoding or prediction job has run. All dataset
payloads and detailed generated verification artifacts remain on Delta; no files
were copied to the Mac. These notes record bounded status metadata only.

| Group | Slides | Tiles | Usable masks | Slides with sampled annotated cancer |
| --- | ---: | ---: | ---: | ---: |
| Benign | 20 | 8,733 | 20 | 0 |
| GG1 | 20 | 8,583 | 20 | 20 |
| ISUP 4–5 | 20 | 8,599 | 20 | 20 |

All 20 high-grade slides contain sampled Gleason 4/5 annotation, on **4,209
distinct tiles** (pattern 4 or 5, counted once per tile). No case with native-mask
cancer lacked sampled annotated cancer. These are annotation/intake observations,
not classifier predictions or cancer/floater detection results. Sampling remained
representative and mask-independent. Slide disjointness from all 129 exposed IDs
is verified by the frozen protocol; patient independence remains unknown.

## Executed jobs and resources

Acquisition `23070667`: 110 seconds, 2 CPUs, 4 GB cap; exactly 120 files and
1,348,184,402 catalog TIFF bytes. PNG export storage is 1,935,563,023 bytes,
excluding small sidecars. Acquisition streamed full TIFF SHA256 and packaged ZIP
CRC; these are not externally supplied official checksums.

Each tiling chunk requested 2 CPUs, 8 GB and 15 minutes on account/QoS
`bfqi-delta-cpu`, partition `cpu-interactive`.

| Manifest rows (zero-based) | Job | Elapsed seconds | Tiles |
| --- | --- | ---: | ---: |
| 0–9 | 23070755 | 241 | 4,697 |
| 10–19 | 23070937 | 153 | 4,036 |
| 20–29 | 23071013 | 289 | 3,908 |
| 30–39 | 23073158 | 211 | 4,675 |
| 40–49 | 23073380 | 146 | 3,962 |
| 50–59 | 23081800 | 213 | 4,637 |

Root-job elapsed time × allocated CPUs totals **0.7572 CPU-hours**, including
acquisition, within the approved five-hour maximum. This is scheduler accounting,
not a billing reconciliation. No duplicate acquisition/tiling job was submitted.

The first ten-slide profiling gate passed before continuation. One local driver
bookkeeping error was repaired after verification, without repeating imaging.
Shared SSH expired twice during monitoring; the driver stopped each time and the
user reauthenticated privately. Jobs 23071013 and 23073380 were inspected and
verified after reconnection before any remaining chunk was submitted. Slurm
execution continued independently of SSH. The final job 23081800 is verified,
and no approved CPU chunk remains unsubmitted.

## Provenance and verification limits

Immutable pipeline source is `bfd4416936d2c35d764d6fd46e1017f110ef48db`:

`/u/mhoda/floater-finder/releases/panda-fresh-baseline-v1-20261021T023142Z/source`

All 226 staged source files were verified before execution. The exact frozen
manifest and acquisition plan are unchanged. Slurm jobs opened actual pyramid
TIFFs/masks, checked dimensions/alignment, recorded TIFF-derived physical scale,
streamed native-mask audits and generated spatial tile exports/checksums. Bounded
post-job inspection verified small metadata/CSV hashes, coordinates, areas, label
fractions, input/source identity and recorded PNG hash membership. It did not
decode or rehash payloads on login nodes. Pyramid alignment does not prove
histological registration. Future encoding must recheck PNG and checkpoint hashes
inside its scheduled job.

Remote output root:

`/work/nvme/bfqi/mhoda/floater-finder/panda-fresh-baseline/radboud60-v1`

Detailed reports remain there:

- `reports/acquisition-metadata-v1.json` — SHA256 `6972dafa2016ce3d09fb57a5fcf66658f87444e2c1002ccfb1efb9966e533fa6`.
- `reports/tiling-metadata-start0-count60-v1.json` — SHA256 `2b57b50c3b1fac749dfb129fa95d343c086a25dd7da7086ad71a68acb5b44d0c`; exact 60-slide metadata audit.
- `reports/cpu-readiness-v1.json` — SHA256 `2547519afadbb0615cd0691bf550ec4c0db117b32069ab360641bd7447654790`; counts, resource ledger and proposed commands.
- `tiling-directories.json` — SHA256 `fd504540c7b90ff241248edb4b14dedf7478b5993c483f7766086cc2e7442bc8`; exact 60 directories in frozen manifest order.
- Per-chunk metadata reports retain every slide and native/sample annotation audit.
- `reports/encoding-readiness-v1.json` records the matching canonical adapter/runtime contract; it does not claim a fresh GPU run.

Metadata helper SHA256: `25d605b18291a3525f8e7ac15b6de04ff3ff9dfc48a270413a121dffe3378d71`.
Future post-encoding wrapper SHA256: `ac7cb4062cd1474494b66d47967815430131ba664f081eaf32ee609e6988299b`.
The helper/wrapper live under the remote root's `scripts/`; they are distinct from
the frozen pipeline source snapshot. No payload/report file was downloaded.

The old 120 cohort, 50,729 embeddings and all previous results are preserved. The
33 frozen legacy source hashes, original final-test protocol and local main were
rechecked unchanged. The original 24 final-test predictions remain sealed. The
last unchanged software suite passed 284 tests with warnings treated as errors;
this execution changes documentation only, so it does not rerun that suite.

## Proposed next scope — not approved or submitted

At the final lightweight recheck, the user queue was empty; `cpu-interactive` and
`gpuA100x4-interactive` were up with one-hour partition limits. Site `accounts`
reported 5,287 rounded CPU hours and 8 GPU hours in the previously selected
allocations. These are shared snapshots, not reservations.

One CONCH v1 encoding job: **60 slides / 25,915 tiles**, one A100, 4 CPUs, 16 GB,
30 minutes maximum (**0.5 GPU-hour**), account `bfqi-delta-gpu`, QoS
`bfqi-delta-gpu-mhoda`, partition `gpuA100x4-interactive`. Uses only the existing
checkpoint (802,235,437 bytes; pinned SHA256
`40a9644b9ba0e83a74576e0a5e5f7313599fa9c9cdaf3c20f8a3e271b0e9ae7c`).
No weights/data download. The earlier 49,785-tile run took 1,306 seconds; a simple
tile-count projection is about 11.3 minutes, excluding queue/startup effects.
The 30-minute cap is the resource bound, not a completion guarantee.

After successful encoding and inspection, one CPU verification/frozen-baseline
job: 2 CPUs, 8 GB, 20 minutes, account/QoS `bfqi-delta-cpu`, partition
`cpu-interactive`. It verifies all 60 saved artifacts before any prediction, then
uses the four frozen predictors without fitting or retuning. Cancer classification
uses 60 slides; low/high uses 40 nonbenign slides. This is a separate fresh baseline,
not the original sealed final test or a floater-policy validation. Failures stop
execution; no automatic rerun, replacement or exclusion is authorized.

Exact commands below run **on Delta, only after separate approval**, in sequence;
the second waits for successful GPU completion and inspection:

```sh
sbatch --parsable --time=00:30:00 /u/mhoda/floater-finder/releases/panda-fresh-baseline-v1-20261021T023142Z/source/scripts/slurm/panda_encode_cohort.sbatch /u/mhoda/floater-finder/releases/panda-fresh-baseline-v1-20261021T023142Z/source /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z /work/nvme/bfqi/mhoda/floater-finder/panda-fresh-baseline/radboud60-v1/tiling-directories.json /work/nvme/bfqi/mhoda/floater-finder/panda-fresh-baseline/radboud60-v1/embeddings
```

```sh
sbatch --parsable /work/nvme/bfqi/mhoda/floater-finder/panda-fresh-baseline/radboud60-v1/scripts/postencode_v1.sbatch /u/mhoda/floater-finder/releases/panda-fresh-baseline-v1-20261021T023142Z/source /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z /work/nvme/bfqi/mhoda/floater-finder/panda-fresh-baseline/radboud60-v1 bfd4416936d2c35d764d6fd46e1017f110ef48db
```

Expected new outputs: `embeddings/<image_id>/{slide.npz,text.npz,timing.json,completion.json}`,
`embeddings-verified-v1.json`, then `clean-baseline-v1/` with frozen raw predictions
and metrics. Those destinations were absent at readiness inspection. All outputs
remain under the remote fresh root. No fresh predictive accuracy or clinical
validity is known yet; no new floater review policy is established.
