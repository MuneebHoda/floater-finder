# Fresh development-validation proposal v1

This is an outcome-blind **metadata proposal**, not an acquired or validated cohort. No image, mask or checkpoint was downloaded. The existing 24 calibration slides are iterative development; the original 24 final-test predictions remain sealed. The candidate IDs must not be changed in response to future classifier/detector results.

## Verified selection and availability

The original Delta `train.csv` (SHA256 `f67935796d8da5ff9dcb27865968e51f24d297fe7f17e69f4af3ca1b3737f45a`) and the completed official file catalog (`996b0313b76decc70978f46c9f3286035edc40e15738431e04c610ed5eb09f1e`) were inspected as metadata only. The planner excludes the union of all 120 study IDs and the original 12-slide pilot: **129 unique exposed slides**. It prioritizes catalog masks, then ranks by SHA256 of seed/purpose/provider/slide ID, seed **20261021**. No image content, annotation outcome, model score or donor performance enters selection.

| Separate candidate option | Benign / GG1 / ISUP 4–5 | Catalog masks | Exact image + mask TIFF bytes | Acquired candidate files |
| --- | --- | --- | ---: | ---: |
| Primary: fresh Radboud | 20 / 20 / 20 | 60/60 | 1,348,184,402 | 0/120 |
| Optional second-institution Karolinska | 20 / 20 / 20 | 60/60 | 3,512,683,208 | 0/120 |

Both together would require **4,860,867,610 catalog TIFF bytes**, plus transfer packaging and intermediate artifacts. These are alternative/separately approvable scopes, not an acquisition request already granted. A bounded Delta stat check of exactly 240 proposed paths found none present. Available filesystem space at inspection was 4,031,335,342,080 bytes, shared and not reserved. Mask readability, alignment, physical scale and usable annotation coverage are **unknown**, even though every candidate has a catalog mask. Patient IDs are absent from `train.csv`; only slide-ID disjointness is verified. Duplicated specimens and cross-slide patient overlap remain unresolved.

There are 924/809/1,698 remaining Radboud and 1,925/1,814/732 Karolinska catalog candidates in the three groups after exclusions. No ISUP 2/3 slides or labels are invented. Selected manifests, exact per-file availability observations, hashes and provenance are in [reports/fresh_validation_metadata_v1](../reports/fresh_validation_metadata_v1/).

Sixty slides is a feasibility validation size, not clinical validation. Even 0 alerts in 60 slides has a Wilson 95% upper bound of about 6.0%; 0/20 in a single category has an upper bound of about 16.1%. Classwise accuracy and genuinely independent patient-level performance will remain uncertain. Repeated doses/seeds do not increase the number of validation slides. Primary Radboud reduces acquisition/adapter risk; Karolinska tests a different institution but requires a separately verified provider adapter before use.

The [organizers' reader notebook](https://github.com/DIAGNijmegen/panda-challenge/blob/main/notebooks/getting-started-with-the-panda-dataset.ipynb) describes different annotation meanings: Radboud includes Gleason patterns; Karolinska separates background, benign and cancer regions without GP4/5-specific labels. Both use the red mask channel. Its raw notebook SHA256 at inspection is `132f0cf2cc70b283fbce91e1f4e97153b1cd9389ec6b2ffcd67fbc9487572dd7`. Karolinska masks must never be passed through the current Radboud fractions without a new validated mapping. They could support cancer-region controls, not native GP4/5 ground truth. The documentation also cautions that the masks are semi-automatic and noisy.

## Frozen validation design before acquisition

1. Finish training-only predictor/threshold selection and record portable model hashes, prompts, preprocessing, component rule and all abstentions. Retain failed policies. The reused calibration set cannot validate revised hypotheses independently.
2. Fix the acquisition candidate manifest before any outcomes. After explicit download approval, validate every file, alignment, reader support and provider semantics in bounded CPU jobs. Report unusable cases and actual counts; never silently replace them with favorable slides.
3. Use mask-independent representative tiling, the same physical FOV and existing CONCH v1 checkpoint. Keep native masks for diagnostics/donor eligibility only. Freeze a separately approved GPU encoding batch after input gates.
4. Apply frozen predictors and detector once to fresh unmodified slides, genuine annotated cancer controls and predeclared synthetic doses/seeds/donors. Report confusion matrices, class recall/BA, new errors among originally correct hosts, component/tile recall, review burden, hypothetical harm and host-clustered intervals. Treat donor reuse explicitly. No threshold revision on these outcomes may be described as independent validation.
5. Keep the original 24 test slides sealed. A final evaluation remains separately approved and predeclared after development readiness.

## Resource estimates, not executed costs

For either 60-slide option: selective acquisition can reuse the existing 2-CPU/4-GB/one-hour CPU Slurm wrapper after exact-plan approval. Network transfer volume/time is unmeasured; TIFF catalog bytes do not equal ZIP wire bytes. CPU reader/tiling should use six bounded ten-slide chunks, 2 CPUs/8 GB/15-minute cap each (at most 3 requested CPU-hours), serialized under the current one-submitted-job CPU QoS. Larger Karolinska images may cost more; the first chunk is a profiling gate.

At 512 tiles/slide, 60 slides produce at most 30,720 tiles, about 62.9 MB of raw float32 512-dimensional image vectors before compression and metadata, and roughly 2.3 GB of exported PNGs extrapolated from the prior profile. Budget **10 GB** free working space for Radboud or **15 GB** for Karolinska including TIFFs, PNGs, temporary packaging, receipts and safety margin. These are estimates, not quotas or measured new-cohort storage.

The completed CONCH job 23054910 encoded 49,785 tiles on 117 slides in 1,306 seconds (0.363 GPU-hours). Linear scaling to 30,720 tiles suggests about 13.4 minutes; reserve a separately approved one-A100, 4-CPU, 16-GB, 30-minute cap (**0.5 GPU-hour**) for one 60-slide batch, after CPU gates. No new GPU job has been submitted. CPU frozen-scorer/detector application would use 2 CPUs/8 GB/20 minutes, with cost updated from the present research measurements. These are proposals, not approval to consume GPU allocation.

Reproduce the metadata proposal (use a fresh output directory):

```sh
PYTHONPATH=src .venv/bin/python scripts/panda_fresh_validation_plan.py \
  --train /tmp/floater-fresh-validation-metadata/train.csv \
  --catalog /tmp/floater-fresh-validation-metadata/official_catalog-20261020-paced.json \
  --exclude-manifest reports/manifests/panda_candidate_120_20261020.csv \
  --exclude-manifest /tmp/floater-fresh-validation-metadata/pilot.csv \
  --output results/panda/fresh_validation_metadata_v1_reproduction
```

Those three temporary input files were copied from the verified Delta PANDA root; their authoritative remote locations and hashes are recorded in the proposal. This command does not acquire data or submit jobs.
