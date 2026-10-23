# Bounded training PNG galleries: verified export

CPU **23102636 completed 0:0 in 23 seconds**, from pushed source `ec5a71d`.
The new bundle covers **72 original training slides /389 cached RGB components**,
with **1,638 unique unchanged PNG assets** shown through **2,605 gallery references**.
PNG copies total **101,466,949 bytes (96.77 MiB)**, below the frozen 512 MiB cap.
All **1,783 output files**, 73 checkpoints and 76 registry events verify.
All **363 software tests passed** before submission, including 13 new colored-PNG
fixture checks. All actual images and detailed reports remain on Delta.

## What the galleries show

Each component retains its original saved baseline/counterfactual predictions,
geometry, numeric-context gate and component order. Up to four component tiles
and four outside tiles are selected using physical x/y/index order alone, with
equally spaced order positions. The selector uses no annotations, labels, image
features, scores, decision changes or influence. Every original component remains
represented, not only the previously observed decisive ones.

The HTML galleries show **separate saved examples, not spatial reconstructions**.
They do not establish physical fragment boundaries, whole-slide coverage, whether
tissue is foreign, or an appropriate biological comparison reference. They do not
replace full NN5 reference context with the displayed subset. Empty outside context
has text and no invented image; unknown RGB assignments remain explicitly unknown.
Review/foreignness decisions remain null, tissue action none, and hidden annotation
controls stay outside reviewer JSON/HTML.

PNG bytes match the original encoding-input checksums exactly. No crop, contrast
change, color edit, generated tissue or pixel normalization was applied. HTML may
display an image smaller; physical captions use recorded coordinates and field size.
The observed field is **111.82315650205668 µm on both axes** in all verified training
sources, not an assumed exactly-112-µm field. Each selected PNG passed format/RGB,
recorded-dimension, checksum, path and byte-bound checks inside the Slurm job.
Original PNGs, metadata and old reports were never overwritten.

| Artifact check | Verified count |
| --- | ---: |
| Original training slides /RGB components | 72 /389 |
| Reviewer JSON /HTML pages /index | 72 /72 /1 |
| Unique source PNG copies | 1,638 |
| Display references, including repeated images | 2,605 |
| References with unknown RGB assignment | 176/2,605 |
| Total output files, including PNGs | 1,783 |
| Source completion/CSV/metadata receipt groups | 72 |
| Copied PNG bytes | 101,466,949 |

These counts describe exported artifacts. Repeated references are not new slides,
patients, trials or independent observations. Unknown assignments are neither
reclassified nor silently dropped. Patient independence and physical piece
boundaries remain unverified.

## Preserved evidence and scientific limits

The old reports' fields, predictions, gates, separate controls and all 145 old
rendered-file hashes remain unchanged. The saved historical CONCH v1 zero-shot
`top5pct` evidence is still **25 decision-changing components on 23 training slides**,
with **20 numeric-context abstentions**, five supported comparisons, and ten decisive
components containing native cancer annotation. These are unchanged descriptions
of old counterfactuals, not new errors, independent performance, prevented harm or
successful foreign-tissue detection.

No classifier/encoder, new embedding, new class score, threshold fit, segmentation,
WSI, mask or NPZ read occurred. The existing PNGs were decoded only for bounded
format/dimension validation and copied byte-for-byte; integrity inspection afterward
used file hashes and PNG headers. No source pixels changed, and no datasets,
weights, images or reports were downloaded to the Mac. There was no GPU job,
duplicate, retry, original final-test prediction, fresh60 or calibration evaluation.
Alert rate and foreign-fragment recall remain unmeasured/null, not zero. The rejected
final evaluation gate remains closed; a useful floater detector is not validated.

This completes the bounded gallery integration. The reports now contain actual
saved tissue examples, but there has been no pathologist assessment or validation
of visual inconsistency. **Browser layout remains unverified** under the previously
observed local-file URL policy; no alternate surface or URL workaround was attempted.
Static HTML checks confirm all image references resolve to bound local PNG assets,
all component disclosures and research captions are present, and no active controls,
remote asset, script or deletion action was introduced.

## Access and reproducibility

New remote index:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review/dependence-previews-v1/index.html`

Reviewer pages/JSON are in `reports/`; selected source PNG copies are in `tiles/`.
Each slide checkpoint records original source receipts, asset hashes and the old
separate native controls. The sealed summary binds all PNG/report/index hashes.
The prior `dependence-report-v1` bundle is preserved in full. Nothing is served
publicly, no local download or tunnel was started, and no further job was submitted.

Account/QoS `bfqi-delta-cpu`, partition `cpu-interactive`, node `cn099`;
2 CPUs, 4 GB, five-minute cap, zero GPUs. Elapsed 23 seconds, Python task 14 seconds,
MaxRSS 316,776 KiB; **0.012778 allocated CPU-hours**. Own queue empty after completion.
All 1,783 output files have observed mode **0660**, retained as project-group
read/write. Local execution is Darwin; shared SSH `mhoda` / `dt-login04` verified.

Source `ec5a71dde4b566393ddfa4b53b5e1b6a8eec3d6d` was pushed and separately staged
read-only; all 267 files, six pinned input receipts, 33 legacy source hashes and
prior runtime freezes verify. Protocol SHA256:
`5024779111434c188f6a2d486acff1203db4969f337c1875dfb9481bfd61859c`.
[Full fixed design, exact source, resource limits and command](../docs/panda_preview_export_v1.md).
Main, original120/fresh60, TCGA, all prior experiments and original test seal remain
preserved, with the original final output absent. Subsequent edits are documentation only.

Remote artifact root:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review`

| Preserved artifact | SHA256 |
| --- | --- |
| `dependence-previews-v1/run.json` | `261bd5a081d170e23614c25cf68a949427acd96dda3489dbf0efb41e3a2f4f80` |
| `dependence-previews-v1/seal.json` | `2431a745be1a7af169d1b612064c175df2a98436cdd871ab7c25d6b811e5ebae` |
| `dependence-previews-v1/checkpoints/summary.json` | `12c952f15e0983bc71d7ff662d12f16892942171ef643b9cba49f21c443c6570` |
| `dependence-previews-v1/index.html` | `3a3336fc3e27414c91586fe732881a91a90a8776aaaf8c9062cd093894b7963f` |
| `preview-export-authorization-v1.json` | `604b7b9931374f7555f7417c0d88cd4274bae8300461d33757fb43d582b877bc` |
| `preview-export-completion-v1.json` | `05c148adb417d907673d5fd8d099960690a5e78a9a00e9ef05deb20246344c02` |

The index is byte-identical to the old index because its links and dependence
counts are unchanged; in the new directory those links open the new gallery pages.
Independent inspection checked every geometry selection, caption coordinate/field,
PNG asset hash/header, reviewer JSON, HTML asset link, control preservation and
registry seal, without extracting image payloads to the local machine. All output
and status claims here come from observed receipts; no visual/clinical result is inferred.

Read-only next command:

```sh
cat reports/panda_preview_export_results_v1.md
```
