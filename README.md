# Floater Finder

A [numeric-context eligibility contract](docs/panda_context_safety_v1.md) is prepared for training-only native-control accounting. It separates unsupported comparisons from review decisions, retains uncertain topology, and never labels an eligible cancer component foreign. Real coverage accounting is pending; no review-policy validity follows.

The [original-training topology/context audit completed](reports/panda_topology_context_results_v1.md): **72 slides, 2,160 planned context records, 315 passing software tests**. Sampled components disagree substantially with cached RGB membership. Sparse comparison context causes large morphology-score sensitivity without inserted foreign tissue; six outside tiles supplies NN5 neighbor counts but does not validate a review cutoff. No classifier predictions, GPU, downloads or final-test access. The floater review policy remains unsupported.

The [S3 conservative review-transfer diagnostic completed](reports/panda_fresh_review_transfer_results_v1.md): 140 saved bags /9800 model-policy records, **306 passing software tests**. The primary combined rule detects **0/20 foreign fragments per edit mode** while flagging four genuine cancer-containing carriers and hypothetically damaging 4/46 initially correct unmodified predictions. Its apparent one-case label recovery retains all foreign tissue. No useful review policy follows; topology/native-context feasibility needs further development. All data/raw results stay on Delta and original final-test predictions remain sealed.

The [frozen CPU S1 follow-up completed](reports/panda_fresh_s1_results_v1.md): **1,191 interventions /2,382 exact oracle passes**, nine capacity exclusions and 140 counterfactual bags. At 5% requested contamination, the fixed primary changes 9/54 initially correct host-trial decisions per edit mode (four unique hosts). Genuine cancer-containing pieces also influence predictions: excluding them changes primary cancer to benign in 14 component tests across 13 slides. This does not validate foreignness or a review alert. **297 software tests pass**; all raw artifacts stay on Delta and the original 24 test predictions remain sealed.

Fresh Radboud60 [CONCH encoding and frozen baseline evaluation are complete](reports/panda_fresh_baseline_results_v1.md): **60 slides / 25,915 verified 512D embeddings**. The frozen primary reaches **80.0% benign/cancer balanced accuracy** (cancer recall 28/40) and **72.5% low/high** (high-grade recall 11/20); both have wide slide-bootstrap intervals. All files remain on Delta. No refitting, threshold changes or original 24 final-test predictions; no floater-policy validity follows. [CPU intake evidence](reports/panda_fresh_cpu_execution_v1.md); unchanged software suite 284 tests.

The latest [paired-placement CPU audit](reports/panda_detector_placement_v1.md) is complete: the frozen primary detects **0/607 foreign-fragment instances**, recovers **0/39 induced-error instances**, and detects 0/59 in each common paired placement mode. This four-host training-only study does not establish a useful review policy. **272 software tests pass**; all final-test predictions remain sealed.

Research now uses training-only frozen-CONCH linear probes, a shared intervention/registry engine and context-aware detector v3. Grade prediction has promising development point estimates but no established independent improvement; v3 remains ineffective at low review burden. The [research checkpoint](reports/panda_research_checkpoint_v1.md) records all candidates, failures, S2 v2 engineering scope, fresh-cohort metadata and resource gates. Historical evidence below is retained; all 24 final-test predictions remain sealed.

The **[19-slide submission package](submission/ashby_20261021_v2/)** contains the standalone PowerPoint/PDF, abstract, eight-minute script, Q&A and checklist. Completed CPU S2 stress preserves **760/760 exact oracle recoveries**; its preselected mean scorer has **0/8 calibration low-to-high errors at every primary dose**. Ranked detector v2 also remains unsupported: **0/40 calibration fragment hits**, with **1/24 unmodified slides alerted**. [Current execution checkpoint](reports/submission_execution_checkpoint_20261020.md), [S2 results](reports/panda_s2_results_v1.md), [ranked v2 results](reports/panda_review_v2_results.md). All 24 final-test slides remain unscored; **204 software tests pass**.

PANDA has **120 slides / 50,729 verified CONCH embeddings**. Development review-policy v1 is now **frozen and rejected**: the combined policy flags 0/24 unmodified calibration slides but detects 0/40 injected fragments. Decision dependence alone detects more but exceeds the clean-alert/harm targets. The 24 final-test slides remain unscored; CPU preflight verified 10,988 input files without decoding labels or computing predictions. [Current scientific findings](reports/panda_review_results_v1.md), [presentation figures and outline](reports/panda_presentation_v1.md), [frozen protocol and blocked final command](docs/panda_final_test_v1.md).

Floater Finder now targets a CONCH-only **prostate-biopsy fragment-dependence safety check**: identify pieces whose exclusion changes a supplied slide scorer's decision, while preserving all tissue and the original prediction. The immediate target is benign-versus-cancer S1. A decisive piece may be genuine small cancer; this check does not establish foreign tissue.

The PANDA adapter provides bounded pyramid-region tiling, physical coordinates and native-mask label fractions with the existing CONCH encoder. Real clean development scoring, 192 connected-fragment S1 trials and component-review comparisons have run; all original 192 oracle checks pass. The earlier [implementation status](reports/panda_implementation_status.md) and [artifact audit](docs/panda_integration.md) preserve the initial smoke-stage history. The current software suite passes **192 tests**. These development observations do not establish a clinically useful cancer or floater detector.

```sh
uv sync --locked --no-editable --reinstall-package floater-finder --extra test
.venv/bin/python scripts/fragment_dependence_demo.py --output results/fixtures/fragment-dependence/new-run
```

The demo saves/reloads artificial embeddings and emits baseline/counterfactual predictions, piece geometry and [fixture alert JSON](examples/fragment_dependence/alert.fixture.json). Its scorer and thresholds are artificial and uncalibrated. `analyze_saved_slide()` now accepts saved NPZ artifacts plus a prediction callable and requires recorded physical geometry. Existing CLI commands and the CONCH/NCSA pipeline remain available below; the earlier TCGA experiments are historical **organ-classification evidence only**, not evidence of cancer detection.

For PANDA TIFF integration tests, install the optional region-reader dependencies:

```sh
uv sync --locked --no-editable --reinstall-package floater-finder --extra test --extra panda
.venv/bin/python -m pytest tests/test_panda.py tests/test_fragment_dependence.py -q -W error
```

This is a research prototype. Synthetic contamination is not verified real contamination; image-text similarity is not a clinically validated diagnosis. The historical CONCH v1 organ workflow passed a four-patient smoke through patient-separated detector calibration and evaluation. The fixed detector threshold missed most injected tiles; the subsequent development cutoff gate failed. Those observations are preserved below and in the experiment reports.

## Run locally

From this checkout, install the locked CPU/test dependencies into the project environment:

```sh
uv sync --locked --no-editable --reinstall-package floater-finder --extra test
.venv/bin/python -m pytest -q -W error
.venv/bin/floater-finder --help
bash scripts/run_fixture_checks.sh results/fixtures/new-run
```

Use a fresh output directory for each run. Commands refuse to overwrite existing artifacts. The normal installation avoids an observed local editable-install import problem; use the reinstall command above after source changes. Tests check that the installed package matches the source.

The fixture command creates artificial arrays and independent fixture development/evaluation identities. It exercises scoring, all requested contamination levels, oracle recovery, detector calibration, detector ablations, random-removal and clean-control comparisons. All outputs remain labeled `fixture`; they support software checks only.

## Inspect and inventory

```sh
.venv/bin/floater-finder inspect
.venv/bin/floater-finder inventory --root data --manifest configs/cohort_manifest.example.csv --output results/inventory/new-run
```

Supply only relevant accessible roots. If a root is missing, the inventory records an error rather than claiming that data exists. CSV templates are header-only; fill them with verified records. An inventory is not an extraction or download operation. The current local inventory found zero slides.

`configs/cohort_manifest.example.csv` includes participant/project, source site, diagnostic status/provenance, organ, label, split, report linkage and spatial metadata. `configs/institution_map.example.csv` requires verified normalized institution mapping provenance. `configs/tile_manifest.example.csv` expects `tile_id,path,x,y`. Unknown metadata must stay unknown.

## Real CONCH workflow

1. Verify patient-attributed PRAD/BLCA diagnostic slides or existing tile exports, report linkage and coordinate scale. Assign disjoint development/evaluation patients.
2. Confirm an already-local, authorized CONCH checkpoint and an installed compatible environment. The encoder uses an existing local checkpoint and performs no automatic model download or credential read.
3. Review the resource request and use the recorded authorization for bounded CONCH plan jobs. Encode tiles with `encode` inside a CUDA allocation. The command requires a tile CSV, slide-metadata JSON, prompt YAML, local checkpoint and new output directory; see `encode --help`.
4. Validate resulting `slide.npz`/`text.npz`. Populate the null paths and empty pairs in `configs/conch_smoke.yaml`; keep the fixed prompts. Start with one pair before populating `conch_pilot.yaml`.
5. Run `stress --config <populated-config> --output <new-results-directory>`. Oracle verification runs for every successful trial. Raw scores, exclusions, denominators, configuration and input/source hashes are saved.
6. Calibrate on unmodified development artifacts with `calibrate`, then evaluate independent held-out hosts/donors with `detect`. Use `plot` only when sufficient real observations exist; install the locked `plots` extra then.

A scheduled one-pair wrapper now extracts raw pixels at verified existing tissue coordinates, resampling both scanners to common 256-micron tiles before encoding. The encoder also accepts pre-extracted tiles. A 128-tile cap is recorded as a subset, not a full-slide experiment. The pinned checkpoint, real image/text encoding and capped throughput are now verified on a scheduled A100. These measurements are not a full-slide throughput benchmark.

## Commands

| Command | Purpose |
| --- | --- |
| `inspect`, `inventory` | Local package/cache availability and bounded cohort inventory. |
| `validate`, `encode` | Artifact checks and optional scheduled real CONCH tile/text encoding. |
| `score`, `inject` | Mean/top-1%/top-5% scoring and connected synthetic contamination. |
| `stress`, `oracle` | Reproducible sweeps, explicit eligibility denominators and mandatory recovery. |
| `calibrate`, `detect` | Separate-patient clean calibration, organ/visual/combined scores and controls. |
| `summarize`, `plot` | Recompute metrics or export a real-data contamination curve. |
| `fixture` | Artificial-array software checks, never research evidence. |

## NCSA and resource approval

Use SSH alias `ncsa-floater`. Heavy processing and GPU inference belong in approved Slurm jobs. Approved job `22957101` completed on an A100 node with exit code `0:0` in five seconds, verifying scheduled GPU allocation and driver visibility. Hosted two-tile CONCH image-encoding tests passed on October 17 and 18; both runs' saved outputs have now been retrieved and independently validated. See the [GPU smoke evidence](reports/gpu_smoke_22957101.json) and [NCSA setup](docs/ncsa_setup.md).

| Job script | Account / partition | GPU / CPU / memory | Wall time |
| --- | --- | --- | --- |
| [Driver visibility](scripts/ncsa_smoke.sbatch) | `bfqi-delta-gpu` / `gpuA100x4` | 1 / 1 / 2 GB | 2 minutes |
| [Pre-extracted tile draft](scripts/slurm/conch_encode.sbatch) | `bfqi-delta-gpu` / `gpuA100x4` | 1 / 4 / 16 GB | 5 minutes |
| [Physical WSI pair encoding](scripts/slurm/conch_one_pair.sbatch) | `bfqi-delta-gpu` / `gpuA100x4` | 1 / 4 / 16 GB | 10 minutes |
| [Patient-separated detector](scripts/slurm/conch_detector.sbatch) | `bfqi-delta-cpu` / `cpu` | 0 / 2 / 4 GB | 5 minutes |

The driver-visibility script completed as job `22957101`; the CONCH encoding draft remains unsubmitted. Both use the verified GPU sub-allocation QoS. Password/Duo prompts belong in your own Terminal. Do not put credentials or private keys in project files or logs.

The next-stage preflight verified the hosted CONCH service's health and located 208 existing prostate tiles with public GDC project/patient metadata. After initial 401 responses, authenticated tests produced two finite, unit-normalized, 512-dimensional image embeddings, with identical vectors across both runs. The latest two-image HTTP round trip took about 0.14 seconds; this is not a GPU throughput benchmark. See the [latest smoke evidence](reports/conch_service_smoke_20261018T205624Z.json) and [setup notes and limitations](docs/ncsa_setup.md#next-stage-conch-service-preflight). This is a connectivity check; the hosted API does not supply all vectors/provenance required by the full experiment.

A subsequent search found full shared PRAD/BLCA feature cohorts, but their sampled headers identify **CONCH v1.5 / 768 dimensions**. They cannot be mixed with the tested v1 service. The user approved the 4.80 GB CONCH v1 input plan: both diagnostic WSIs and the pinned original checkpoint are now checksum-verified in personal Delta storage. The [next-experiment plan](docs/next_experiment.md) records paths and evidence. CPU job `22994404` prepared the runtime and verified input checksums, measured slide calibration and the tokenizer. GPU smoke `22994635` completed successfully, reproducing the first run after a provenance fix; 128 tiles per slide yield matched 512-dimensional vectors and pass six oracle checks. See the [verified result](reports/conch_one_pair_smoke_22994635.json).

## Real-data smoke outcome

Six initial Delta jobs completed successfully. The [contamination results](reports/conch_smoke_results.md) and [detector results](reports/conch_detector_results.md) include verified plots, raw metrics and explicit denominators. There are two development and two evaluation patients, each represented by a connected 128-tile subset, for **512 real image embeddings with 512 features each**, plus matched text prototypes. The local suite passes **91 tests**.

The combined detector ranks synthetic donor tiles with mean AUROC 0.949 at 10% requested contamination, but its frozen 99th-percentile development threshold detects only 3.85% of donor tiles in that descriptive stratum. The next study needs representative calibration and a fresh held-out cohort. These observations do not establish clinical floater detection or population performance.

A subsequent [development-only cutoff diagnostic](reports/conch_threshold_results.md) completed as CPU job `22995268`, reusing existing vectors with no new inference or download. It reports five cutoff levels, 60 oracle passes and 900 rows. It shows the detection/original-host-removal tradeoff on reused calibration patients; no revised cutoff or new evaluation claim follows from it. [Next study and dependency maintenance](docs/next_experiment.md).

New image work uses Pillow 12.3.0 and records that version in artifact provenance; local tests use pytest 9.0.3. A separate private Delta runtime passed scheduled A100 compatibility job `22995434`: all 256 regenerated development tiles and image/text vectors exactly matched the preserved baseline. The generic pre-extracted-tile wrapper now takes the private environment as its first argument. [Verified setup](docs/ncsa_setup.md).

The [expanded feasibility-pilot plan](docs/expanded_pilot_plan.md) contains 16 new public slides totaling 21.24 GB, with eight new development and eight fresh evaluation patients. Acquisition and all-18-patient technical preflight passed; the [study design is frozen](docs/expanded_pilot_protocol.md) at four × 96 tiles per patient. GPU job `23028013` then produced **3,840 development embeddings** from the ten development patients. CPU job `23028265` completed all ten leave-one-patient-out folds, but **no frozen candidate satisfied the 1% removal budget**; the most conservative candidate's worst case removed 19/384 original-host tiles. No final numerical calibration or held-out evaluation followed. [Observed development results and evidence](reports/conch_development_results.md). The local suite passes **105 tests**.

## Evidence and outputs

- [Progress and executed commands](reports/progress.md).
- [Methodology, schemas, scientific limits and source references](docs/methodology.md).
- [NCSA CONCH preflight](reports/ncsa_preflight_20261017.json) and [public PathGen metadata inventory](reports/ncsa_pathgen_inventory_20261017.csv).
- Local environment snapshot: `reports/environment.json`.
- Local inventory/missing data: `results/inventory/local/`.
- Validated fixture run: `results/fixtures/final_validation/` (ignored by git).

Real-data smoke, pilot and benchmark results must use separate directories and explicit categories. Requests to relabel fixture artifacts as real results are rejected. No MUSK/PathGen adapter, clinical validation, or real-slide floater claim is included.

## License

This project is licensed under the [MIT License](LICENSE).
