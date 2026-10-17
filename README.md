# Floater Finder

Stress-testing pathology vision-language models against synthetic tissue contamination and detecting suspicious foreign tissue without model fine-tuning. The first milestone is CONCH on TCGA-PRAD versus TCGA-BLCA.

This is a research prototype. Synthetic contamination is not verified real contamination; image-text similarity is not a clinically validated diagnosis. **No real-data CONCH experiment has run yet.**

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
2. Confirm an already-local, authorized CONCH checkpoint and an installed compatible environment. No model downloads or credential reads are performed by this project.
3. Review the resource request and explicitly approve a Slurm job before submission. Encode tiles with `encode` inside a CUDA allocation. The command requires a tile CSV, slide-metadata JSON, prompt YAML, local checkpoint and new output directory; see `encode --help`.
4. Validate resulting `slide.npz`/`text.npz`. Populate the null paths and empty pairs in `configs/conch_smoke.yaml`; keep the fixed prompts. Start with one pair before populating `conch_pilot.yaml`.
5. Run `stress --config <populated-config> --output <new-results-directory>`. Oracle verification runs for every successful trial. Raw scores, exclusions, denominators, configuration and input/source hashes are saved.
6. Calibrate on unmodified development artifacts with `calibrate`, then evaluate independent held-out hosts/donors with `detect`. Use `plot` only when sufficient real observations exist; install the locked `plots` extra then.

Raw WSI tiling is a remaining integration task; the current encoder consumes verified pre-extracted tiles. A 128-tile cap is recorded as a subset, not a full-slide experiment. Real checkpoint/model/environment compatibility and throughput remain untested.

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

Use SSH alias `ncsa-floater`. Heavy processing and GPU inference belong in approved Slurm jobs. The latest single SSH check timed out; local development continued. Earlier allocation/path observations and current unknowns are in [NCSA setup](docs/ncsa_setup.md).

| Unsubmitted draft | Account / partition | GPU / CPU / memory | Wall time |
| --- | --- | --- | --- |
| [Driver visibility](scripts/ncsa_smoke.sbatch) | `bfqi-delta-gpu` / `gpuA100x4` | 1 / 1 / 2 GB | 2 minutes |
| [Capped CONCH encoding](scripts/slurm/conch_encode.sbatch) | `bfqi-delta-gpu` / `gpuA100x4` | 1 / 4 / 16 GB | 5 minutes |

Neither job has been submitted. Both use the previously verified GPU sub-allocation QoS; installed GPU/model access remains unverified. Password/Duo prompts belong in your own Terminal. Do not put credentials or private keys in project files or logs.

## Evidence and outputs

- [Progress and executed commands](reports/progress.md).
- [Methodology, schemas, scientific limits and source references](docs/methodology.md).
- Local environment snapshot: `reports/environment.json`.
- Local inventory/missing data: `results/inventory/local/`.
- Validated fixture run: `results/fixtures/final_validation/` (ignored by git).

Real-data smoke, pilot and benchmark results must use separate directories and explicit categories. Requests to relabel fixture artifacts as real results are rejected. No MUSK/PathGen adapter, clinical validation, or real-slide floater claim is included.

## License

This project is licensed under the [MIT License](LICENSE).
