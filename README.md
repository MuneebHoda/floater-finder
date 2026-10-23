<p align="center">
  <img src="docs/assets/readme/hero.png" alt="Floater Finder: which tissue piece drives the AI prediction? Read tissue, encode with CONCH, test piece influence, review evidence. Concept illustration." width="100%">
</p>

<p align="center">
  <a href="https://www.python.org/"><img alt="Python 3.11–3.12" src="https://img.shields.io/badge/Python-3.11–3.12-17313b?style=flat-square&logo=python&logoColor=white"></a>
  <a href="docs/panda_integration.md"><img alt="CONCH v1" src="https://img.shields.io/badge/Encoder-CONCH_v1-087f8c?style=flat-square"></a>
  <a href="tests/"><img alt="455 tests passed at the October 22 checkpoint" src="https://img.shields.io/badge/Tests-455_passed-087f8c?style=flat-square"></a>
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/License-MIT-607981?style=flat-square"></a>
</p>

<p align="center">
  <a href="#start-with-the-tissue">The idea</a> ·
  <a href="#what-the-experiments-show">Results</a> ·
  <a href="#try-it-without-a-gpu">Try it</a> ·
  <a href="docs/panda_integration.md">Technical guide</a>
</p>

Floater Finder explores whether a small tissue fragment can disproportionately
influence a prostate-biopsy AI prediction. It combines real pathology images,
CONCH embeddings and **leave-one-piece-out analysis** to trace that influence.
Built by [Muneeb Hoda](https://github.com/MuneebHoda) for the **2026 Ashby Hackathon**.

> **Research prototype.** A decisive fragment may be genuine cancer. The system
> preserves tissue and reports evidence; a useful foreign-tissue detector has
> not yet been established.

## Start with the tissue

<table>
  <tr>
    <td align="center" width="50%"><img src="submission/ashby_20261021_v2/media/benign_native.png" width="224" alt="Real PANDA tile from a benign slide, with benign epithelium and stroma annotations"><br><b>Native tissue from a benign slide</b></td>
    <td align="center" width="50%"><img src="submission/ashby_20261021_v2/media/gp4_native.png" width="224" alt="Real PANDA tile containing native Gleason pattern 4 annotation"><br><b>Native tissue containing annotated cancer</b></td>
  </tr>
</table>

These are real PANDA reference tiles, not detected floaters.
[Image provenance](submission/ashby_20261021_v2/media/provenance.json).

The pipeline reads spatial tissue tiles, encodes them with **CONCH**, and asks:
**“Does the prediction change if this piece is excluded?”** It then checks native
cancer controls and known synthetic insertions to separate decision influence
from evidence of foreignness. An empty counterfactual is reported as unevaluable.

## What the experiments show

<table>
  <tr>
    <td align="center" width="33%"><b>120</b><br>PANDA slides in the initial cohort</td>
    <td align="center" width="34%"><b>50,729</b><br>verified CONCH embeddings</td>
    <td align="center" width="33%"><b>455</b><br>passing software tests</td>
  </tr>
</table>

![Two measured experiments: a 60-slide cancer-classification confusion matrix and contamination-induced errors among five initially correct development hosts. These are separate cohorts and scorers.](docs/assets/readme/evidence.png)

**A working pipeline, with an important limit.** Classification and fragment
influence are measurable, but influence alone does not identify foreign tissue.
The fixed-support review candidate detected **3/24** foreign fragments while
alerting on **8/72** unmodified slides—failing its predefined utility targets.

[Baseline results and uncertainty](reports/panda_fresh_baseline_results_v1.md) ·
[Contamination experiment](reports/panda_s1_and_piece_results_20261020.md) ·
[Detector findings](reports/panda_stable_context_results_v1.md)

<details>
<summary><b>See why automatic tissue removal would be unsafe</b></summary>

![Measured tile footprints: both genuine native cancer and a known synthetic donor component change cancer to benign when excluded.](reports/figures/panda_piece_development_23065744/piece_examples.png)

These are sampled tile footprints, not complete tissue boundaries. Both native
annotated cancer and a known synthetic insertion can drive the same decision
change. **The counterfactual explains dependence; it does not diagnose a floater.**
[Measured examples and reproduction](reports/panda_s1_and_piece_results_20261020.md#real-leave-one-piece-out-diagnostic).

</details>

## Under the hood

**Python · PyTorch / CONCH · OpenSlide · NumPy · scikit-learn · Slurm**

- **Spatial processing:** bounded TIFF-pyramid reads, mask alignment, physical
  coordinates and annotation fractions. [Tiler](src/floater_finder/panda.py)
- **Model-independent analysis:** saved embeddings plus a supplied prediction
  callable. [Counterfactual engine](src/floater_finder/fragment_dependence.py)
- **Reproducible experiments:** frozen scorers, source-separated controls, exact
  oracle recovery and checksummed Slurm runs on NCSA Delta.
  [Research modules](src/floater_finder/research/) · [Job scripts](scripts/slurm/)

## Try it without a GPU

This small **artificial fixture** demonstrates the JSON output without pathology
data or model weights. Requires Python 3.11–3.12 and `uv`.

```sh
git clone https://github.com/MuneebHoda/floater-finder.git
cd floater-finder
uv sync --locked --no-editable --reinstall-package floater-finder
.venv/bin/python scripts/fragment_dependence_demo.py \
  --output results/fixtures/my-first-run
```

Open `results/fixtures/my-first-run/alert.fixture.json` for the baseline,
counterfactual predictions and piece geometry. Use a fresh output directory.
Fixture alerts are software examples, not research results.

<details>
<summary><b>Tests, full evidence and current research status</b></summary>

```sh
uv sync --locked --no-editable --reinstall-package floater-finder \
  --extra test --extra panda --extra research
.venv/bin/python -m pytest -q -W error
```

- [96-image pixel pilot](reports/panda_pixel_results_20261022.md): canonical
  CONCH re-encoding passed; no slide-prediction changes in 24 foreign edits.
- [10,000-candidate benchmark](docs/panda_pixel_program_v2.md): source-path
  correction passes 57/57 metadata checks; replacement CPU/GPU execution is pending.
- The original 24 final-test slides remain unscored. Patient independence and
  clinical utility are unverified; no pathologist review is claimed.
- [Progress log](reports/progress.md) · [Delta setup](docs/ncsa_setup.md) ·
  [Historical workflows](docs/research_history.md).
- Rebuild the two overview panels with `python scripts/build_readme_assets.py`
  using the optional `plots` dependencies. [Figure inputs and hashes](docs/assets/readme/provenance.json).

</details>

---

[MIT License](LICENSE) · Code by [Muneeb Hoda](https://github.com/MuneebHoda) ·
Research execution on **NCSA Delta**. PANDA data and CONCH weights retain their
own access and licensing terms. Full datasets and checkpoints are not bundled.
