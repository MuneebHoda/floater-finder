# Eight-minute presentation script

19 total slides: 18 spoken slides and one reference slide. **908 spoken words**, **480 seconds**. The pace leaves time to point to figures and pause at major findings. Do not read source citations aloud.

## Slide 1: Floater Finder
**00:00–00:20 (20 seconds)**

Floater Finder measures whether a pathology model depends on a small tissue fragment, and whether that evidence supports useful review. We completed a real-data pipeline and controlled stress experiments. We also rejected two review policies when they failed our development targets. This is a safety experiment with explicit failure gates.

## Slide 2: The specimen-consistency problem
**00:20–00:50 (30 seconds)**

Extraneous tissue can create diagnostic discrepancies. A disease classifier can recognize cancer without establishing that it belongs to the specimen. These are actual PANDA tiles with native benign and pattern-four annotations. Neither is a verified natural floater. The intended output is evidence for pathologist review, while preserving the tissue.

## Slide 3: CONCH and the review question
**00:50–01:10 (20 seconds)**

CONCH provides reusable histology representations. Frozen morphology prompts supply our engineering disease scorer. Specimen consistency is a separate task. We therefore examine visual inconsistency, prediction influence and physical context separately. A piece can influence the cancer prediction and still be entirely genuine.

## Slide 4: 120 real slides and 50,729 embeddings
**01:10–01:35 (25 seconds)**

Our cohort contains one hundred twenty Radboud biopsies and fifty thousand seven hundred twenty-nine verified embeddings. Slides split seventy-two, twenty-four and twenty-four across training, calibration and held-out test. Patient identities are unavailable. Clean sampling ignores cancer masks. Delta Slurm handled WSI processing and GPU encoding. Subsequent experiments reuse cached features on CPU.

## Slide 5: Clean benign/cancer baseline
**01:35–02:05 (30 seconds)**

The clean top-five-percent scorer is correct on twenty of twenty-four calibration slides, with seventy-eight-point-one percent balanced accuracy. It identifies fifteen of sixteen cancer slides, but only five of eight benign slides. Those five originally correct benign hosts define the new-error denominator. The three initial false positives cannot become new contamination errors.

## Slide 6: S1: a controlled cancer-fragment stress test
**02:05–02:35 (30 seconds)**

S1 inserts connected, annotated cancer-positive donor features into benign hosts at six doses. We use thirty-two host slides and twenty-one reused donor slides. Dose means donor tiles divided by original host tiles, rounded up. A new error conflicts with the original host label. The mixture truly contains donor cancer, so this does not prove misrecognition of its pixels.

## Slide 7: Small fragments can change the prediction
**02:35–03:10 (35 seconds)**

Pooling changes sensitivity. For our primary top-five-percent scorer, positive-dose new errors are one, one, two, two and two out of five originally correct calibration hosts. These are eight error instances involving two unique hosts, rather than eight patients. Every original S1 trial passes exact oracle restoration. That validates pipeline integrity, not detector performance.

## Slide 8: Known synthetic donor component
**03:10–03:35 (25 seconds)**

This known synthetic insertion contains three cancer-positive donor tiles in a four-hundred-twenty-eight-tile host. Excluding the red-outlined fragment changes cancer back to benign. The measured footprint is zero-point-zero-three-seven-five square millimeters. This plot shows saved coordinates, not natural contamination or a microscopy composite.

## Slide 9: Genuine cancer can also change the decision
**03:35–04:05 (30 seconds)**

The genuine-cancer counterexample produces the same decision change. Excluding this unmodified four-hundred-thirty-five-tile component changes cancer to benign. It contains zero-point-one-seven-one square millimeters of native cancer annotation inside a five-point-four-three-nine-square-millimeter sampled footprint. The component is not a tiny tumor focus or a confirmed whole piece. Influence alone cannot establish foreignness.

## Slide 10: Observed tissue geometry has limits
**04:05–04:25 (20 seconds)**

Sparse sampled cells can misrepresent physical pieces. We use observed RGB foreground at pyramid factor sixteen without filling gaps. This worst-mapping training example maps only seventy-six percent of tiles, so review abstains. Four of six formerly single-component calibration cases become multiple components. RGB boundaries remain proxies and empty exclusions stay unevaluable.

## Slide 11: Review utility conflicts with reviewer burden
**04:25–05:00 (35 seconds)**

The detector comparison reveals a burden tradeoff. Spatial rules hit thirty-two of forty fragments but alert on nineteen of twenty-four clean slides. Decision dependence hits eight fragments and recovers eight induced-error instances, but alerts on four clean slides. Hypothetical filtering damages three of twenty initially correct clean predictions and flags a genuine cancer component.

## Slide 12: The combined v1 policy failed its utility gate
**05:00–05:30 (30 seconds)**

The combined policy misses every calibration fragment. Five mixtures pass its visual criterion, but none also passes influence. Those five mixtures are nested doses from one host. No useful candidate emerges among eighty-one preregistered rules. Zero clean alerts cannot rescue zero recall. We froze the rejection and blocked its final-test job.

## Slide 13: S2: clean grade scorer before contamination
**05:30–05:55 (25 seconds)**

S2 now tests low-versus-high predictions using pattern-four-or-five donor material and same-grade controls. We chose mean pooling before stress outcomes. Its clean calibration baseline gets all eight low-grade slides correct, but only four of eight high-grade slides. That limited sensitivity remains explicit. All seven hundred sixty trial records pass exact oracle restoration.

## Slide 14: S2 primary result: no calibration label flips
**05:55–06:30 (35 seconds)**

The primary S2 result is negative: zero of eight new calibration errors at every tested requested dose. Training has one of twenty-two at ten percent. Secondary top pooling flips two of two or three of three correct hosts, but misclassifies most clean low-grade slides. Same-grade tissue also causes a flip. Eight pattern-five cases lack capacity. These are binary engineering endpoints, not clinical upgrades.

## Slide 15: Detector v2: a separately versioned ranking study
**06:30–06:50 (20 seconds)**

Version two tests ranked review instead of requiring every signal to pass a strict conjunction. Training selects thresholds and review caps. Visual, influence and geometry features enter the ranking. Injection truth, donor identity and native annotation remain evaluation-only. Previously seen calibration outcomes make this iterative development, not independent validation.

## Slide 16: Ranked review still fails useful calibration recall
**06:50–07:20 (30 seconds)**

The selected rank detects twenty-two of one hundred twenty training fragments, but zero of forty on known calibration. Its one clean calibration alert contains native cancer. An unbudgeted ranking hits twenty-one fragments but alerts on every clean slide and flags fourteen native cancer components. That exceeds the burden targets. We found no useful validated improvement over version one.

## Slide 17: What the experiment demonstrates
**07:20–07:45 (25 seconds)**

We demonstrate a verified pipeline, S1 sensitivity, a negative primary S2 result and two rejected review policies. We do not establish natural-floater detection or clinical usefulness. Reused donors, unknown patient overlap and representative sampling limit inference. Artificial edge placement also simplifies geometry. The twenty-four final slides remain unscored.

## Slide 18: Next evidence requires a new scientific gate
**07:45–08:00 (15 seconds)**

Next research needs useful review that preserves native cancer, followed by external institutional and model testing. New resources need separate approval. Any final evaluation requires a scientifically useful, newly frozen protocol and explicit authorization. Original tissue remains intact.

## Slide 19: Sources and reproducibility
**Reference slide, no planned speaking time**

Reference slide for questions. Sources, media provenance and version hashes accompany the submission. No final-test prediction appears in the deck.
