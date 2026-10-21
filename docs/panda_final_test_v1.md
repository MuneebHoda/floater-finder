# Frozen PANDA final-test preparation v1

**Protocol frozen; operating point rejected; final execution blocked.** No final-test prediction has run. Do not submit the prepared command merely because all input checks pass. The code checks measured selection evidence and refuses unsupported readiness before loading held-out labels or arrays. A future useful development policy needs a separately versioned protocol, rather than changing this one.

- Protocol: `configs/panda_frozen_protocol_v1.json`, SHA256 `695e2097aa0916bdd03b9b0721fc1f58dd5fda338e9c4975c171d64d2d36c881`.
- Final runtime source: `cde0e4a257898c6abe93d6a4df6ad52c744f31cc`, separate verified Delta snapshot. Measurement source `cb1cddc12dde114140958b97d93474a7e5761059`; corrected reporting source `e200aa08713a2f893f776f08b31955f42b0232e1`.
- Account/QoS `bfqi-delta-cpu`; partition `cpu-interactive`; one node, two CPUs, 4 GB, ten minutes, no GPUs. Prepared runtime verifies numpy 2.0.2, Pillow 12.3.0, openslide-python 1.4.6 and tifffile 2025.5.10. This performs no encoding or downloads.
- Inputs: all 24 test IDs, tile exports, normalized saved CONCH image/text vectors and measured geometry; exact source/data paths and hashes are in the protocol and blinded index. Test labels are not in the blinded index. Hash-only preflight does not decode the label-bearing originals.
- Read-only preflight job 23066843 completed 0:0, 31 seconds, 10,988 files verified, zero predictions and no label decoding. Input integrity and scientific readiness are separate outputs.

The exact prepared final command, **not submitted**, from the local Mac:

```sh
ssh -o BatchMode=yes ncsa-floater 'sbatch --parsable /u/mhoda/floater-finder/releases/panda-final-prep-20261021T001051Z/source/scripts/slurm/panda_review_final.sbatch /u/mhoda/floater-finder/releases/panda-final-prep-20261021T001051Z/source /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z /work/nvme/bfqi/mhoda/floater-finder/panda-review/final-preparation-v1-20261021T000114Z/panda_frozen_protocol_v1.json 695e2097aa0916bdd03b9b0721fc1f58dd5fda338e9c4975c171d64d2d36c881'
```

The safe verification command uses the read-only preflight script (already executed successfully; rerun only if input state needs rechecking):

```sh
ssh -o BatchMode=yes ncsa-floater 'sbatch --parsable /u/mhoda/floater-finder/releases/panda-final-prep-20261021T001051Z/source/scripts/slurm/panda_review_preflight.sbatch /u/mhoda/floater-finder/releases/panda-final-prep-20261021T001051Z/source /work/nvme/bfqi/mhoda/floater-finder/envs/panda-cpu-1598f9b-20261020T040441Z /work/nvme/bfqi/mhoda/floater-finder/panda-review/final-preparation-v1-20261021T000114Z/panda_frozen_protocol_v1.json 695e2097aa0916bdd03b9b0721fc1f58dd5fda338e9c4975c171d64d2d36c881'
```

Expected final output directory, currently absent:

```text
/work/nvme/bfqi/mhoda/floater-finder/panda-review/final-preparation-v1-20261021T000114Z/final-test-v1
```

If a future supported protocol permits one explicit evaluation, its runner atomically creates a single-use output lock before reading test labels/arrays. It evaluates the frozen top-5% benign/cancer scorer on all 24 slides, fixed observed-RGB components, and deterministic same-provider/same-test-split S1 donor assignments at 0/0.5/1/2/5/10%. It does not use training/calibration donors or replace capacity exclusions. Native cancer masks select donor material and quantify controls; slide grades are not tile annotations. Every successful injection requires exact oracle recovery.

Expected artifacts: `execution_lock.json`, `classifier_predictions.json`, `component_cases.json`, `topology_audit.json` plus bounded RGB previews, `trials.json`, `exclusions.json`, `metrics_by_case.json`, `matched_controls.json`, `summary.json`, and checksum `completion.json`. Summaries include clean confusion/balanced accuracy, per-dose original-correct error denominators, tile/fragment recall, clean alerts/burden, genuine-cancer flags, hypothetical filtering damage/recovery and slide/host uncertainty. All tissue remains intact.

The frozen statistical plan uses per-dose distinct-slide Wilson intervals, stratified slide bootstrap for clean balanced accuracy and host-cluster bootstrap retaining doses for aggregate detector/recovery metrics. Random draws are not patients. Donor reuse and unavailable patient identity constrain interpretation. There is one predeclared final execution, no parameter revision after test outcomes, and no clinical validation claim. A crash or oracle defect preserves its partial outputs and lock; inspect it without automatically resubmitting.

The exact next scientific action is to review the failed development policy and present it honestly; no held-out launch is justified by v1. [Measured findings](../reports/panda_review_results_v1.md).
