# Expert-review worksheet preparation v1

The qualitative worksheet/validator is implemented and **408 software tests pass**
with warnings as errors (33.68s), including 22 new artificial administrative cases.
No dependency or existing runtime was changed. Main, 33 legacy source files and
all five previous runtime freezes remain unchanged. Expert judgments are **not
implemented by software** and must remain blank until a reviewer enters them.

## Fixed administrative scope

Create 24 blank case records linked to the completed original-training paired
audit (24 hosts /16 reused donors). Read only the pinned run/seal/summary, its
24 JSON checkpoints/public JSON and HTML hashes; no PNG, WSI, mask, NPZ or model
is opened. No prediction, annotation analysis, experiment draw, fitting, threshold
selection, final/fresh60/calibration evaluation, download, Slurm or GPU job.

The worksheet is **unblinded**: existing pages reveal source provenance and saved
model outcomes. It supports development critique, not blinded observer accuracy
or independent detector validation. Physical isolation is unevaluable from the
unassembled galleries. Every human judgment starts null. `cannot_assess` is an
accepted completed answer, and requests for more context remain explicit.

The rubric asks about limited-display adequacy, donor consistency with native
and host context, additional review, more context and a written rationale. Reviewers
report a pseudonym, role, prior exposure and human-entry attestation. The validator
checks record completeness and immutable source/case references only; it cannot
verify expertise, actual human entry, correctness or clinical utility. Even all
24 completed records leave detector/clinical validation and final readiness false.
Do not infer expert approval from software verification or automatic preparation.

Frozen protocol: `configs/panda_expert_review_worksheet_v1.json`, SHA256:

`ce0ab94413020d85f2edb3c810b05716f9554334612a13ed2b9bd73094dca68d`.

[Static reviewer guide](../docs/panda_expert_review_v1.md).
Original audit source `24364b4946de211ae8b608f7bf7d710408aca112`, with receipt hashes:

| Existing source | SHA256 |
| --- | --- |
| `run.json` | `24e48eeb8fd550e9b4ac2b0ba3deff2b0e50d7894310fa8e26a58c10e5e78671` |
| `seal.json` | `6064a1c5037d364cc0f3c82848ac24ab76f1c2a173ee06d421a39ae84a182ac4` |
| `checkpoints/summary.json` | `e684f6cc7a7cb36d60f8aa6017fb285077473fb6d9ca0ea8e08ef1bb3555659d` |

Verified new packet path, prepared October 21 at 18:50 UTC:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review/expert-review-worksheet-v1`

Expected files: `worksheet.blank.json`, `review_guide.md`, `preparation.json`.
Preparation refuses an existing/partial output directory. The blank original is
immutable input; reviewers work in a separate response copy. Validation is read-only
and returns recording counts without writing a scored result. Detailed response
files and all images stay on Delta; no local download, server, tunnel, public
sharing or contact with reviewers is included. Browser layout remains unverified.

The latest user “next” advances the stated expert-review need through this
bounded administrative preparation. Exact pushed source, staging and preparation
receipt are recorded below; **no expert assessment is claimed**.
No Slurm command is needed or authorized by this worksheet preparation.

Source-only preflight:

```sh
python scripts/panda_review_worksheet.py \
  --config configs/panda_expert_review_worksheet_v1.json \
  --config-sha256 ce0ab94413020d85f2edb3c810b05716f9554334612a13ed2b9bd73094dca68d
```

The real packet is verified; reviewer availability and expert judgments remain
unverified. Known source labels and cached predictions must never fill reviewer
answers. Existing negative detector results and the final-test gate remain unchanged.
Preparation is a workflow artifact, not a new scientific result.

## Observed preparation and recording status

Local Darwin and shared SSH `mhoda` / `dt-login04.delta.ncsa.illinois.edu` verified.
Pushed source `e29a7a3fa56179451d6d2f123fa6add9ba66f619` was staged read-only at:

`/u/mhoda/floater-finder/releases/panda-expert-review-v1-20261021T184909Z/source`

All **258 source files** verified, protocol source preflight passed, original three
audit receipts matched and destination was absent before preparation. Archive
SHA256 `aad63493b006a4f6354db0c756aa56f09d75b37a6f3b1ea20b7aaf9f2099ea8a`;
source-manifest SHA256 `014d819572f9e5bd74fba88f7d975c1340a4d17951b83f524cc493790a34c9f2`.

The metadata-only command created exactly three files:

| Packet file | Bytes | SHA256 |
| --- | ---: | --- |
| `worksheet.blank.json` | 16,267 | `479ef6f237c378303c72a46a4fd8549aa8136e45720e3192f34de781d56401df` |
| `review_guide.md` | 5,155 | `4d9a070d4bd755d8532f48b29ed5d6caa8e73220e996889a9d378380fb50495d` |
| `preparation.json` | 805 | `cd3dc7edd023b4a26e08ecf4c27f654c0b066575e7be1f249fdcba96e32203af` |

All 24 original host references /16 reused donor identities, sorted review IDs,
public-page/JSON hashes, source receipts and guide bytes match. All judgments and
reviewer identity/role/exposure remain null; human-entry attestation false. Read-only
validation of the blank form reports **0 recorded /24 pending cases**. The zero
recorded requests/cannot-assess counts mean no answers exist, not negative findings.
Detector/clinical validation, correctness/qualifications verification and final
readiness remain false. No reviewer or expert assessment was invented or contacted.

All original source receipt hashes and **48 public audit JSON/HTML files** match;
the sealed registry was verified without opening images. The 33 legacy source
hashes and original final-protocol hash match, and original final output remains
absent. No PNG, WSI, mask, NPZ or model was opened. No images, raw reports or
response files were downloaded; only bounded status/count/hash metadata returned.
No Slurm/GPU job, new prediction, fit, experiment draw, retry or final access.

Independent verification receipt, kept outside the blank packet:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review/expert-review-worksheet-verification-v1.json`

SHA256 `e741fd742ee7d59499753c6e5114a33559569ed344ad556ed1490c6a988850e4`.
This verifies administrative preparation only. All 408 tests passed before source
freeze; subsequent edits are documentation only. Human review, browser layout,
visual validity and a useful foreignness policy remain unverified. This bounded
preparation is complete; no further job was submitted or authorized by it.

Exact executed preparation command on Delta:

```sh
module load pytorch-conda/2.8
PYTHONPATH=/u/mhoda/floater-finder/releases/panda-expert-review-v1-20261021T184909Z/source/src \
  PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z/bin/python \
  /u/mhoda/floater-finder/releases/panda-expert-review-v1-20261021T184909Z/source/scripts/panda_review_worksheet.py \
  --config /u/mhoda/floater-finder/releases/panda-expert-review-v1-20261021T184909Z/source/configs/panda_expert_review_worksheet_v1.json \
  --config-sha256 ce0ab94413020d85f2edb3c810b05716f9554334612a13ed2b9bd73094dca68d \
  --prepare --source-commit e29a7a3fa56179451d6d2f123fa6add9ba66f619
```

Do not repeat preparation: the existing packet is preserved and reruns refuse it.
For read-only recording validation, replace the last line with:

```sh
--responses /work/nvme/bfqi/mhoda/floater-finder/panda-review/expert-review-worksheet-v1/worksheet.blank.json
```

That is the exact blank-form validation performed, returning 0/24 reviewed. After
a reviewer saves a separate response copy, use that filename instead. Do not infer
validated clinical expertise or an approved alert policy from a successful parse.

Exact next command from the Mac, reading the source-authored guide only:

```sh
ssh -o BatchMode=yes ncsa-floater 'cat /work/nvme/bfqi/mhoda/floater-finder/panda-review/expert-review-worksheet-v1/review_guide.md'
```
