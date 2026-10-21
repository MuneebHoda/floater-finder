# Finished Ashby submission package

The [editable PowerPoint](floater_finder_ashby_v2_final.pptx) and [standalone PDF](floater_finder_ashby_v2_final.pdf) contain **19 total slides**, including a reference slide. The [eight-minute script](presentation_script_8min.md) has **908 spoken words** timed to **480 seconds**, with room for pointing and pauses. [Q&A preparation](qa_4min.md), the [abstract](abstract.md) and the [submission checklist](submission_checklist.md) complete the package.

The deck presents observed development evidence: the verified 120-slide / 50,729-embedding pipeline, S1 sensitivity, the genuine-cancer counterexample, rejected v1, the negative primary S2 calibration outcome and a separately versioned ranked v2 that also fails useful calibration recall. S3/S4 remain future research. The 24-slide final test stays unscored and scientifically blocked.

## Provenance

[Evidence identities](evidence_manifest.json) pin source reports, protocols and runtime commits. [Media identities](media_manifest.json) and [individual microscopy/crop provenance](media/provenance.json) distinguish actual source tiles from measured coordinate plots. Figure-panel crops preserve the original source content and record their exact pixel bounds. No generated histology, speculative performance number or final-test outcome appears.

The source files are [slide content](slide_content.json), [native authoring script](build_submission.py), [documented crop reconstruction](prepare_media.py) and [read-only package checks](verify_package.py). Charts and tables remain native editable objects. Microscopy and preserved scientific plots remain raster evidence.

Native Keynote 14.4 authored/exported the files on macOS because the supplied artifact-tool runtime and dependency-loader tool were unavailable. No substitute authoring package was installed. The exported PPTX was reopened in Keynote and exported to a separate check PDF. This is a Keynote round-trip check, not a claim of inspection in Microsoft PowerPoint. The [delivery manifest](delivery_manifest.json) records the actual validation and file identities. Recheck on the presenter’s machine before the talk.

## Reproduction

Run the read-only checks from the repository root, without model inference or test-data access:

```sh
.venv/bin/python submission/ashby_20261021_v2/verify_package.py
```

Reconstruct the documented crops from the immutable committed source figures, then verify their hashes:

```sh
.venv/bin/python submission/ashby_20261021_v2/prepare_media.py
```

For a new native export, copy this package into a fresh sibling submission folder and run that copy’s `build_submission.py` on macOS with Keynote and Pillow. The authoring script refuses to replace an existing PPTX/PDF. Relative source paths refer to the original committed evidence. Keep a new revision separate and repeat native import, PDF rendering and visual inspection before using it.

The project’s full regression suite passed **204 tests** with warnings treated as errors before this presentation commit, as independently run by the parent integration agent. Presentation generation performs no disease prediction and consumes no Delta/GPU allocation.

## Primary literature

Clinical context comes from a documented diagnostic discrepancy in [Sapp et al. (2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8126555/), with no prevalence claim drawn for this experiment. The representation model is [CONCH, Lu et al. (2024)](https://www.nature.com/articles/s41591-024-02856-4). The dataset source is [PANDA, Bulten et al. (2022)](https://www.nature.com/articles/s41591-021-01620-2). External context is separate from our measured development findings.

The upload URL, exact October 21 deadline time/timezone, team roster/affiliations and live availability remain unverified. No submission upload has occurred. The checklist also calls out publication of the new source/result commits if the organizers will use the GitHub link.
