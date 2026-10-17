# Floater Finder progress

2026-10-17, America/Chicago. No real experimental results yet.

## Environment and sources

- Local Mac confirmed: macOS 26.6.2. System Python 3.9.6; isolated project environment uses Python 3.11.15.
- Preserved the existing MIT license, SSH setup notes, AGENTS.md, smoke-job draft, and supplied PDF.
- Read the 30-page welcome PDF and the current master instruction. The separate October 16 updated proposal was not found in this checkout or the supplied attachment (the attachment is the master instruction).
- No local slides/embeddings or cached CONCH model directory were found. PyTorch, CONCH, and TRIDENT were absent from the inspected system environment.
- One requested SSH test used `BatchMode=yes`, `ConnectTimeout=8` and a 15-second total process timeout. It timed out; no retry or SSH configuration edit was made. Prior NCSA observations remain historical facts in `docs/ncsa_setup.md`.
- Created `.venv` with NumPy 2.0.2, PyYAML 6.0.2, Pillow 11.3.0, pytest 8.3.5. No system-wide package changes or model downloads.

## Milestones

| Milestone | Status | Evidence |
| --- | --- | --- |
| Validated image/text NPZ artifacts | COMPLETE | Normalization, dimensions, IDs, provenance, source-kind and projection checks; pickle-free loading. |
| Pooling and zero-shot scoring | COMPLETE | Hand-computed tests, per-class top 1%/5%, ceil K, deterministic ties. |
| Connected contamination and oracle recovery | COMPLETE | Repeatability, integer rounding, patient separation, spatial validity and exact host restoration tests. |
| Data inventory and stress runner | COMPLETE | Bounded discovery, provenance/missing-data report, patient-split checks, raw scores, exclusions, source/input hashes and eligibility metrics; CLI exercised. |
| Real CONCH inference / PRAD-BLCA pilot | BLOCKED | No real patient-attributed slides/checkpoint/environment; NCSA unavailable this session; job authorization required. |
| Detector and calibration software | COMPLETE | Organ-only, distant-neighbor visual, combined, oracle, no-filter and matched random-removal comparisons; separate-patient calibration and clean-control tests. Fixture validation only. |
| Real detector evaluation and scientific charts | BLOCKED | No actual target-cohort embeddings or independent real development/evaluation cases. No research chart produced. |
| Raw WSI tiling integration | NOT STARTED | Current encoder requires pre-extracted tiles with verified positions/scale. TRIDENT installed version/access remains unknown. |
| Additional models and secondary cohorts | NOT STARTED | CONCH-first scope. |

## Implemented files

- `src/floater_finder/artifacts.py`: validated image/text artifacts, stable IDs, masks, metadata and pickle-free NPZ I/O.
- `scoring.py`, `injection.py`, `experiments.py`: fixed prompt ensembling, mean/top-K, deterministic connected fragments, exact oracle recovery, reproducible runs and explicit eligible/raw metrics.
- `inventory.py`: bounded candidate discovery, TCGA participant/source-site parsing, missingness, report provenance, verified institution mapping and cohort pairing.
- `conch.py`: lazy optional official-model adapter, installed API checks, encoder-weight coverage, shared-space projection, local-checkpoint-only scheduled CUDA encoding and actual timing hooks. **Not exercised with real CONCH.**
- `detection.py`: physical-distance-aware double-blocked reference scoring, clean-development calibration, leakage checks and held-out control evaluation.
- `cli.py`, `fixtures.py`, `reporting.py`: 13 discoverable commands, isolated fixture generation and a real-observation-gated Matplotlib chart command.
- `configs/`: fixed four-phrase organ ensembles, incomplete real smoke/pilot templates, empty manifest headers and explicit null metadata template.
- `tests/`: 54 tests; `scripts/run_fixture_checks.sh`: repeatable installed-CLI integration check; `scripts/inspect_environment.py`: local inventory wrapper.
- `scripts/slurm/conch_encode.sbatch`: new unsubmitted five-minute CONCH draft; earlier driver-only smoke draft preserved.
- `pyproject.toml`, `.python-version`, `uv.lock`, `.gitignore`: isolated locked environment, Python 3.11/3.12 scope, artifact/build/credential-file exclusions.
- README, methodology and NCSA setup notes updated; existing AGENTS guidance preserved and extended with scientific safeguards. MIT license and supplied PDF preserved. No commit or push made.

## Commands and checks executed

```sh
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python numpy==2.0.2 PyYAML==6.0.2 Pillow==11.3.0 pytest==8.3.5
.venv/bin/python -m pytest -q
uv pip install --python .venv/bin/python --no-deps -e .
uv pip install --python .venv/bin/python --reinstall --no-deps --config-settings editable_mode=compat -e .
uv pip install --python .venv/bin/python --reinstall --no-deps .
uv lock --python .venv/bin/python
uv sync --locked --no-editable --reinstall-package floater-finder --extra test
.venv/bin/python -m pytest -q -W error
bash -n scripts/ncsa_smoke.sbatch scripts/slurm/conch_encode.sbatch scripts/run_fixture_checks.sh
.venv/bin/floater-finder inspect --output reports/environment.json
.venv/bin/floater-finder inventory --root . --manifest configs/cohort_manifest.example.csv --output results/inventory/local
bash scripts/run_fixture_checks.sh results/fixtures/final_validation
```

The fixture script contains the exact validated `fixture`, `validate`, `score`, `stress`, `inject`, `oracle`, `calibrate`, `detect` and `summarize` commands. Earlier manual CLI runs under `results/fixtures/` and `results/fixtures/validated/` were retained; `final_validation/` uses the final installed source. Reproduction must choose a new output directory, such as `results/fixtures/reproduce`.

Test history: 29 core checks first passed. One interface-error test then failed (AttributeError versus the intended validation error); fixed, followed by 37 passing checks. The first 46-test run exposed numerical warnings in finite-array matrix operations. Explicit blocked/einsum operations removed those warnings, and all subsequent suites passed with warnings treated as errors. An editable installation imported inconsistently across shell commands; a normal installation plus explicit package reinstall and isolated-interpreter source-freshness tests resolved the executable workflow.

**Final result: 54 passed, zero failed, zero warnings** (`pytest -q -W error`, observed final run 0.58 seconds). Both Slurm drafts and the fixture script pass Bash syntax checking. Syntax checking is not a Slurm scheduling test. An attempted patch context mismatch was corrected before any final source validation.

## Actual outputs

| Output | Observed result |
| --- | --- |
| `reports/environment.json` | Local Python/package snapshot; project has no PyTorch, CONCH or TRIDENT installation. |
| `results/inventory/local/cohort_inventory.csv` | Header-only: zero local candidate slides found. |
| `results/inventory/local/missing_data.json` | Zero candidates, bounded scan and missing-data accounting; not evidence that target TCGA data exists. |
| `results/fixtures/final_validation/inputs/` | Artificial 100-tile host/donor/development/clean-control NPZs, fixture text and reproducible YAML. No real images/model. |
| `results/fixtures/final_validation/stress/results.csv` | 36 **fixture** rows: one host/donor pair, six requested percentages, two seeds, three pooling rules. All successful rows have oracle verification. |
| `results/fixtures/final_validation/stress/` | `summary.json`, `failures.json` (empty) and `experiment.json` with config/prompts/model/input/source hashes. |
| `results/fixtures/final_validation/mixed.npz`, `restored.npz` | Five synthetically injected rows and verified exact host recovery. |
| `results/fixtures/final_validation/calibration.json` | Clean development-fixture calibration with stored parameters, provenance and patient exclusions. |
| `results/fixtures/final_validation/detection/` | Fixture-only tile scores/flags, detection/control metrics and recovery comparisons. |
| `results/fixtures/final_validation/clean_control/` | Separate held-out fixture clean-control evaluation. |
| `results/fixtures/final_validation/recomputed_summary.json` | Recomputed eligibility and raw-change summary. |

These are software checks only. There are **no real-data smoke, pilot or benchmark results**, no measured CONCH inference throughput, no real-tile montage, and no scientific contamination-versus-flip plot. Do not quote fixture AUROC or flip rates as research findings.

## Remaining inputs and approvals

1. Restore manual NCSA access when ready. This session's one batch-mode SSH check was exhausted; no repeated authentication attempt was made. Earlier CPU/GPU allocation and storage facts remain historical, not newly verified.
2. Identify patient-attributed PRAD/BLCA diagnostic slides or existing tile manifests, including project/label/report provenance, split and spatial metadata. The separate updated proposal remains unavailable; the master specification was sufficient for this implementation.
3. Identify an already-local authorized CONCH checkpoint and verify the installed module/model interface. The upstream source was inspected at CONCH commit `141cc09c7d4ff33d8eda562bd75169b457f71a62` and TRIDENT commit `bdeeb74b7eaad8d48bda232bde7de66cae980918`; those are not claims about a remote installation.
4. Explicitly approve any Slurm execution before submission. Driver smoke: `bfqi-delta-gpu`, QoS `bfqi-delta-gpu-mhoda`, `gpuA100x4`, 1 GPU, 1 CPU, 2 GB, 2 minutes. Separate CONCH draft: same account/QoS/partition, 1 GPU, 4 CPUs, 16 GB, 5 minutes, at most 128 existing tiles. No reservation name invented.

No credentials were requested, no SSH config was changed, and no job, model/dataset download, remote copy, remote package installation or actual inference was performed. GPU access remains unverified.
