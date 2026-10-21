# Qualitative review of the saved PANDA controls

This worksheet supports **unblinded development critique** of the existing 24
training control pairs. The pages disclose native/synthetic provenance and saved
model outcomes. They cannot support blinded observer performance, independent
validation, a calibrated alert policy or a claim that a human can detect floaters.
There is no new inference, sampling, model fit, threshold selection or test access.

## Review procedure

Keep all images and detailed response files on Delta. No local image download,
server, tunnel, data sharing or reviewer contact is part of this preparation.
Do not change the original blank worksheet, source audit or any prior result.
Work in a separate response copy under the prepared review-packet directory.
Use a pseudonym instead of personal contact details; never enter credentials.

The packet path is:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review/expert-review-worksheet-v1`

The existing paired-page index is:

`/work/nvme/bfqi/mhoda/floater-finder/panda-review/paired-control-audit-v1/index.html`

Each worksheet record provides its relative audit-page path and source hashes.
Native and synthetic panels contain the **same selected donor PNG examples**.
Native comparison images come from the donor slide; host comparison images come
from the benign host. Other tile examples are geometry-selected, not a complete
piece or a representative morphologic survey. These pages are not mosaics and
do not establish physical boundaries, isolation or a contaminated WSI.

Record reviewer pseudonym, self-reported role (`pathologist`, `pathology_trainee`
or `other`), prior exposure (`has_seen_source_truth_or_predictions` or `unknown`),
and the human-entry attestation. Software does not verify credentials, expertise
or truthfulness of the attestation. Do not have an agent fill in expert judgments.

For each case, fill all six judgment fields and change `review_status` to
`reviewed`. Leave every judgment null for cases not yet reviewed. Do not interpret
missing judgments as negative findings. `cannot_assess` is a completed answer,
not a failure; use it whenever the limited images do not support the judgment.

| Field | Allowed answers / meaning |
| --- | --- |
| `display_adequacy` | `sufficient_for_limited_tile_comparison` or `insufficient`; never whole-slide adequacy |
| `native_context_consistency` | `compatible`, `discordant`, `cannot_assess`; selected donor examples versus the other native donor examples |
| `host_context_consistency` | Same three answers; selected donor examples versus displayed host examples |
| `review_recommendation` | `additional_review`, `no_additional_review`, `cannot_assess`; a qualitative request, not a cancer diagnosis or tissue-removal decision |
| `needs_more_context` | JSON `true` or `false`; identify missing context in the rationale |
| `rationale` | Nonempty text, at most 4,000 characters; cite displayed source tile indices and describe uncertainty |

Consider tissue class, glandular/stromal appearance and apparent preparation
differences only to the extent visible. State uncertainty about stain, scanner,
focus and limited field of view. A different cancer morphology can be genuine
native disease; a decision-changing region is not necessarily foreign. Known
source labels and saved predictions must not be restated as visual findings.
Request surrounding tissue or whole-slide context when needed. Physical isolation
is fixed as unevaluable from these unassembled tile galleries.

Preserve all tissue. A reviewer recommendation does not set the algorithm's
review/foreignness outputs or authorize filtering, retuning or final evaluation.
If available expert review is absent, leave all records unreviewed and report it.

## Recording checks and next use

The CLI verifies frozen source receipts, case order/identity, original blank-form
hashes, required fields and enums, rationale, reviewer metadata and attestation.
It reports completed/pending records and context requests only. It does **not**
verify judgment correctness, reviewer qualifications, clinical utility or detector
recall. Even 24 completed records leave clinical/detector validation and final-test
readiness false. Reused donor slides are not independent cases or patients.

From the verified staged source/runtime, validate a response copy with:

```sh
python scripts/panda_review_worksheet.py \
  --config configs/panda_expert_review_worksheet_v1.json \
  --config-sha256 PROTOCOL_SHA256 \
  --responses /work/nvme/bfqi/mhoda/floater-finder/panda-review/expert-review-worksheet-v1/worksheet.REVIEWER.json
```

Replace placeholders using the preparation report and your response filename.
Validation is read-only and writes no scored result. Do not submit a Slurm job for
blank-form preparation/field validation; these are small administrative JSON checks.
No expert assessment has occurred merely because a packet or validator exists.
Browser layout remains unverified. Any later study needs a separately declared
design, adequate context and independent validation; these exposed training pages
cannot be made blind retrospectively.
