# Pixel-study results inspection — October 22, 2026

Observed on Delta at approximately 20:33–20:40 CDT. Local execution is Darwin;
shared SSH verified `mhoda` / `dt-login03.delta.ncsa.illinois.edu`. This was a
read-only remote inspection of scheduler accounting, bounded logs, saved JSON
measurements and receipt hashes. No new prediction, model call, job submission,
retry, download or final-test access occurred. Detailed artifacts remain Delta.

## Scheduler outcomes

| Job | Scope | Actual result | Delta start/end, October 22 CDT |
| --- | --- | --- | --- |
| 23109277 | 96-image CPU preparation | COMPLETED, 0:0, 13 seconds | 08:21:46–08:21:59 |
| 23109340 | 96-image canonical CONCH encoding and frozen measurements | COMPLETED, 0:0, 43 seconds | 08:24:27–08:25:10 |
| 23109667 | 10,000-candidate CPU preparation | FAILED, 1:0, 15 seconds | 09:12:13–09:12:28 |
| 23109849 | Dependent 10k GPU profile | CANCELLED before allocation, zero elapsed | Cancelled 09:12:34; never started |

The user's job queue was empty at inspection. Historical failed CPU 23109222
remains TIMEOUT; its delayed cleanup ended at 06:54:12. No jobs were duplicated.

## Verified pilot artifacts and encoder

Outputs under `/work/nvme/bfqi/mhoda/floater-finder/panda-review/`:

- `pixel-contamination-v1-prepared/`: 96 records, four original-training pairs.
  All 399 files listed in its completion receipt match their recorded SHA256.
- `pixel-contamination-v1-encoded/`: all five files listed in its completion
  receipt match SHA256, including embeddings, anchors and saved measurements.
- Eight unchanged source anchors pass the frozen drift limits; maximum absolute
  feature difference is approximately 3.73e-8. All 48 unchanged/cut-reinsert
  controls have zero maximum absolute feature difference from their saved anchors.
- The successful scheduled runner checked finite, unit-normalized `(96, 512)`
  features, the canonical 448-pixel CONCH preprocessing and pinned checkpoint.
  Its saved timing is 1.12154 seconds for eight anchors and 1.47110 seconds for
  96 composite/control images. These timings exclude startup and measurements;
  the allocated GPU job lasted 43 seconds.

Scientific source commit: `61959fa148a4a3ae4aadb5ee84b9578933140f6b`.
Protocol SHA256: `33594b467bdd16c75e3b4835a744bab2e917972266a31e33779ac0be386eefb7`.
Real manifest SHA256: `07477eb32f8e63207adb93bdba24950413c4e875151f6e65beccef3943730d86`.
CPU completion SHA256: `438c1cfb5e0dcd08284b1face2fe02722beab7696db0dbac3290b89470a3c88c`.
GPU completion SHA256: `4704e953e720f5aeb1b71499249892fc94316336346fa49b8c93f7dddb004ebd`.
Measurements SHA256: `36833ca6a395a0d9146271c9539ef7ae4a60f455a0d7171ebecb19a3a6e5bfd2`.
Verified checkpoint SHA256:
`40a9644b9ba0e83a74576e0a5e5f7313599fa9c9cdaf3c20f8a3e271b0e9ae7c`.

## Descriptive findings; no review threshold selected

There are 24 foreign edits, 24 matched native shams, 24 unchanged controls and
24 identity cut/reinsert controls. Each variant spans four pairs, three nominal
patch sizes and two placements. Repeated edits are not independent slides or
patients. Patient independence remains unverified.

The following summarizes existing saved measurements only. NN5 is the frozen
truth-free embedding anomaly signal; a higher score is not a foreignness label.

| Nominal patch area within one tile | Foreign comparisons | Median foreign distance from host | Median native-sham distance from host | Foreign NN5 greater than paired native sham | Median paired NN5 difference |
| --- | --- | --- | --- | --- | --- |
| 1% | 8 | 0.03334 | 0.03599 | 3/8 | -0.00168 |
| 5% | 8 | 0.10317 | 0.04896 | 8/8 | 0.02290 |
| 10% | 8 | 0.14769 | 0.07388 | 7/8 | 0.03462 |

Larger foreign edits have a descriptive feature/anomaly effect relative to
matched native edits in this small study. Native edits also change embeddings,
and sharp rectangular seams remain confounded with morphology. At 5%, seven
of eight foreign edits are farther from the *full donor tile* than their matched
native sham is; foreign feature movement is not simply movement toward that
full donor vector. No separately encoded donor crop or pixel localization was
evaluated. No sensitivity, calibrated false-alert rate or clinical claim follows.

Both the frozen primary and historical scorer have **0/24 prediction changes**
under foreign mixed-image replacement: 0/12 S1 edits across two benign hosts and
0/12 S2 edits across two low-grade hosts. The four baseline predictions agree
with their host task labels. Thus this pilot induces no new host-label errors;
recovery conditional on an induced error is unevaluable, not 100%. Native,
unchanged and identity controls also have zero changes. Separate whole-donor
append/replacement comparisons have zero changes as well; their repeated scores
must not be counted as independent contamination trials.

Patch area is within one exported tile, not 1–10% of a slide. One edited tile
represents approximately 0.195–0.488% of the host sampled bag by tile count.
Foreign area is approximately 0.00188–0.04901% of that sampled bag's geometric
tile area. Neither denominator estimates complete WSI tissue area.

## 10k preparation failure and bounded metadata diagnosis

CPU log: `/work/nvme/bfqi/mhoda/panda-pixel10k-gate-23109667.out`.
Preserved failure:
`panda-review/pixel-program-10k-v1-prepared/failure.json`, SHA256
`b0eccfa6d32761f19180eefe7d37169a98a1976e45fe620ea102da14c84f8063`.

The exact exception is `ValueError: Original unbiased source provenance differs`
at `_source()` in the frozen `pixel_program.py`. Five source-fact JSON files
exist; the `images/` and `masks/` directories each contain zero files. There is
no successful completion, record manifest, deduplicated image count or GPU
profile output. The dependent GPU cancellation prevented inference and charge.

A read-only metadata audit checked the compound failing guard for all 57
selected sources. Exactly three fail its **metadata SHA256** comparison; the
other eight predicates in that guard pass for these sources. All three use
embedding receipts from profile job 23051673:

| Source image ID | Current cohort metadata SHA256 | Original embedding receipt's metadata SHA256 |
| --- | --- | --- |
| afe7eb15c8438861ca43f2b20dccf260 | 2961d4ab48098ab00519226a841934c33364ecc2577e21c7283183c16b03208d | 5d30dfef7a2650a781dea3717d9e4d58eab7b32ddda92d2c9e732925cba6e795 |
| 55d91c32710982de78a975ed0f45395c | ef65838f2b664c78c1bc330194e8f77553631a919dcf5d01f2e5e4f357cda20c | 904ed2f80059194084212afb814572499154c4404ac70dc29a241a6e5bb8c72b |
| dd1110c6430e3b1ac732be548a089886 | cf36575ffe053b0c7bdd4300e2282b0dbd27d38e6a757f6d066ff186a8d61047 | 1edc94da76e18604c0836755b895c655c3223e7c1c34bed0519386deedc91cd8 |

The first failed source is `afe7eb15c8438861ca43f2b20dccf260`, sixth in the
frozen source CSV. This check did not rehash full TIFFs or open WSI/array payloads.
The exact metadata-field differences and legitimacy of a migration are unresolved;
do not infer pixel corruption or dismiss the mismatch as harmless relabeling.
Do not bypass the guard, rewrite old receipts or overwrite the failed directory.

Next implementation step: reconcile the three original smoke-source receipts
against their actual cohort metadata and verified reuse provenance, then design
a narrowly tested compatibility check and a new versioned preparation output.
No retry or replacement GPU scope has been submitted during this inspection.

Follow-up: the [versioned path correction](../docs/panda_pixel_program_v2.md)
reconciles the exact metadata fields and original input directories. All57
corrected source metadata checks pass; scheduled v2 preparation remains pending.
The preceding failure diagnosis preserves what was known at initial inspection.

## Billing and preserved scope

Live own QoS `bfqi-delta-gpu-mhoda` reports UsageRaw 5,816,000 billing-TRES
seconds against a 600,000-minute limit. This leaves **8.3844444 normal-batch
A100-hour equivalents**. The previous exact total 5,730,000 plus this pilot's
43 seconds × billing TRES 2,000 reconciles exactly to the new usage. The pilot
cost 0.0238889 equivalents; cancelled GPU 23109849 used no allocation. `accounts`
rounds the remaining balance to eight; `jobcharge --detail --all` displays 1.62
used after rounding individual job charges. Credit does not reserve queue time.

No software implementation changed, so tests were not rerun for this inspection.
The previous 453-test result is historical verification, not a newly executed
check. No human judgments, automatic tissue removal, new encoder, threshold
selection or final-test prediction occurred. Existing results remain preserved.

Exact read-only scheduler command:

```sh
ssh -o BatchMode=yes ncsa-floater 'sacct -j 23109277,23109340,23109667,23109849 --format=JobID,State,ExitCode,Start,End,Elapsed -P'
```
