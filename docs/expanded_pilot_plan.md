# Expanded CONCH v1 feasibility-pilot plan

Acquisition and technical preflight are complete. The [study design is frozen](expanded_pilot_protocol.md) at four × 96-tile windows per patient after an initial 128-tile-window capacity failure. The development runner subsequently produced 3,840 embeddings and completed clean leave-one-patient-out selection. No candidate met the 1% original-host removal budget, so final calibration and held-out evaluation remain stopped. [Development results](../reports/conch_development_results.md). Preflight itself created no embeddings.

The acquisition plan contains **16 new public diagnostic slides, 21,243,276,685 bytes (21.24 GB / 19.78 GiB)**. The user explicitly approved this exact acquisition on 2026-10-18; all 16 downloads are now size/MD5 verified, with completion confirmed after manual reconnection on October 19. There are eight new development patients and eight fresh evaluation patients, four per organ in each split. Retaining the existing two development patients would give ten development and eight evaluation patients. The previous two evaluation patients are retired from this pilot and must not guide parameter selection.

Exact file IDs, filenames, sizes, MD5 checksums, public download URLs, matched shared-coordinate filenames and confirmed personal-storage destinations are recorded in [the machine-readable acquisition plan](../configs/ncsa_expanded_pilot_download_plan.json). The plan records `approved: true`, the explicit acquisition authorization, observed per-file download verification and subsequent scheduled header verification. [GDC metadata and selection evidence](../reports/gdc_pilot_candidates_20261018.json).

## Proposed new patients

| Patient | Organ | Split | Input GB | Public metadata |
| --- | --- | --- | ---: | --- |
| TCGA-G9-6379 | prostate | dev | 1.214 | [GDC](https://api.gdc.cancer.gov/files/3eedf78d-8aa7-4b77-a0c0-d14291415e04) |
| TCGA-FC-A5OB | prostate | dev | 0.758 | [GDC](https://api.gdc.cancer.gov/files/1a9a1a68-750b-402a-89f2-082b65efa593) |
| TCGA-EJ-A46B | prostate | dev | 1.717 | [GDC](https://api.gdc.cancer.gov/files/b5d322a2-461f-4549-9e4c-c272b8188c3e) |
| TCGA-HC-7230 | prostate | dev | 0.145 | [GDC](https://api.gdc.cancer.gov/files/44eb6d7a-a3c2-4023-b068-1c2f50b564db) |
| TCGA-YL-A8SQ | prostate | eval | 2.831 | [GDC](https://api.gdc.cancer.gov/files/0591b150-fe51-4844-a979-40d0246de8e9) |
| TCGA-XK-AAIW | prostate | eval | 0.756 | [GDC](https://api.gdc.cancer.gov/files/6dbcf931-fe34-41e6-8731-93518818a5a2) |
| TCGA-V1-A9ZR | prostate | eval | 0.721 | [GDC](https://api.gdc.cancer.gov/files/dbda78ed-68ba-4c84-80d8-04f8e422672b) |
| TCGA-KK-A7AW | prostate | eval | 0.497 | [GDC](https://api.gdc.cancer.gov/files/f50839b2-5846-42e6-b67b-fbc4034d9717) |
| TCGA-XF-A9SW | bladder | dev | 1.309 | [GDC](https://api.gdc.cancer.gov/files/fb291e7d-cc6b-4169-8be8-fec92dc9cb7d) |
| TCGA-ZF-A9RN | bladder | dev | 1.674 | [GDC](https://api.gdc.cancer.gov/files/ee840357-42d5-4d83-89e7-86869dc9bae4) |
| TCGA-DK-A1A7 | bladder | dev | 1.298 | [GDC](https://api.gdc.cancer.gov/files/6971ceaf-cb55-42b0-9880-effc1010e4a5) |
| TCGA-GV-A3QH | bladder | dev | 1.262 | [GDC](https://api.gdc.cancer.gov/files/8ee271d5-7c0d-4650-965c-e525a6a805f9) |
| TCGA-K4-A5RI | bladder | eval | 3.071 | [GDC](https://api.gdc.cancer.gov/files/227e3588-7740-4941-8966-cd5276564199) |
| TCGA-FD-A5BU | bladder | eval | 1.710 | [GDC](https://api.gdc.cancer.gov/files/8a68864a-187e-4425-9565-709e93d4e794) |
| TCGA-BT-A42F | bladder | eval | 1.352 | [GDC](https://api.gdc.cancer.gov/files/dade7c04-745f-4b74-9d71-a0ba532db9da) |
| TCGA-CF-A3MH | bladder | eval | 0.928 | [GDC](https://api.gdc.cancer.gov/files/9fcfdd36-3608-451b-b391-24d9ab48caa6) |

## Selection and limits

Selection used a frozen SHA-256 patient ranking with seed `floater-pilot-20261018`, one diagnostic slide per patient, and no embedding, score, label-performance or outcome selection. The metadata candidate pool has 64 records matched to existing coordinate filenames in the two relevant shared directories. Selection has no patient overlap and uses one new patient per TCGA source-site prefix. New prefixes are disjoint across splits and exclude the existing development prefixes `2A` and `2F`. A source prefix is **not** a verified normalized institution. This is a feasibility sample, not a representative cohort or an institution-matched study.

Public GDC identity, access, diagnostic-slide status, file size and MD5 are verified. Raw headers, isotropic measured MPP, coordinate-header agreement and revised sampling capacity passed scheduled preflight for all 18 planned patients. Only the two predeclared development patients received pixel-extraction/visual technical QC; full-cohort tissue quality and native floater labels remain unreviewed. No shared CONCH v1.5 feature values may be read or used. Report linkage and normalized institutions remain unavailable.

## Storage and execution gates

1. Scope authorization for these exact 16 files was received on 2026-10-18. The prepared `scripts/slurm/download_inputs.sbatch` requests one CPU, 2 GB and 30 minutes, with no GPU. Download sequentially into the existing personal NVMe project directories, verify exact size/MD5 and preserve partials/errors. No additional checkpoint is needed. No automatic replacement patient or additional download is authorized by this proposal.
2. Storage inspection reported approximately 3.8 TiB filesystem-wide free space. `lfs quota -u mhoda` reported zero user soft/hard block and inode limits; allocation/project quotas remain unverified. Plan at least 35 GB additional working headroom for the 21.24 GB raw inputs, one partial download, and bounded tile exports. Filesystem free space is a snapshot, not a personal quota guarantee.
3. Raw slide/header and coordinate geometry checks passed for all 18 patients in CPU preflight `23005299`. The initial sampling-capacity failure in `23005189` remains recorded. Stop on corruption, model mismatch or an oracle defect.
4. Broader sampling is implemented and validated: four separated connected windows of **96 tiles each, 384 per patient**, with the same 256-micron field and 512-pixel export. The original four × 128 candidate failed capacity on one development slide; the revised uniform size preserves every patient and the 1 mm minimum gap. Independent checks observed at least 1,024 microns across windows, and 768 development QC tiles decoded successfully. No image embeddings or held-out outcomes informed the revision. [Evidence](../reports/conch_pilot_preflight_results.md).
5. Use the patched, verified private runtime for every newly encoded image/text artifact. Preserve the previous environment and artifact provenance. At most one GPU runs at once. Proposed encoding cap: one A100, four CPUs, 16 GB and 30 minutes under the verified hackathon GPU account/QoS. This is a resource cap, not a measured runtime estimate.
6. Implement a cohort runner with the [frozen development-only policy](expanded_pilot_protocol.md): leave one of ten development patients out, fit on the other nine, and choose the smallest predeclared quantile satisfying at most 1% original-host removal on every omitted patient and every variant. Do not use synthetic mixtures for selection. If none passes, stop before evaluation. Freeze the final all-development numerical calibration before held-out scoring. This gives no unseen-patient or clinical false-positive guarantee.
7. Evaluate fresh held-out hosts/donors once with oracle, no-filter and matched random-removal controls. The frozen design has 32 directed pairs × five nonzero levels × five seeds = **800 mixed trials**, plus **eight unique clean-host controls**, 808 trials/2,424 variant rows total. Only eight evaluation patients are independent. Proposed CPU cap: two CPUs, 8 GB, 30 minutes; benchmark before increasing it.

Development encoding and selection have since completed, without a feasible cutoff or final numerical calibration. No held-out encoding/evaluation job has been submitted. The exact read-only next command is:

```sh
cat reports/conch_development_results.md
```

## Acquisition execution

The approved acquisition was submitted as CPU Slurm job `22995881`, requesting one CPU, 2 GB and 30 minutes from `bfqi-delta-cpu`/`cpu`. The exact staged plan and client hashes, authorization and output path are recorded in [the submission record](../reports/ncsa_pilot_download_submission_20261018T225831Z.json). The remote per-file report is `/work/nvme/bfqi/mhoda/floater-finder/acquisitions/expanded-pilot-20261018T225831Z/downloads.json`. Submission is not completion; file verification is recorded only after the client finishes each input. No expanded pilot job was submitted.

At 23:00:24 UTC (6:00:24 pm Central), Slurm reported the job pending with reason `Reservation` and no start estimate. The CPU event reservation `sup-30434-cpu` had ended at 6:00 pm Central and was inactive. No input transfer had started at that observation; the pending request was later cancelled as recorded below.

A dry-run on the documented `cpu-interactive` partition found an available short CPU slot. The still-pending job `22995881` was cancelled and its cancellation verified before replacement job `22995933` was submitted under the same account/QoS and one-CPU/2-GB/30-minute bound. No duplicate downloader was launched. [Replacement submission](../reports/ncsa_pilot_download_submission_20261018T230346Z.json). Its report is `/work/nvme/bfqi/mhoda/floater-finder/acquisitions/expanded-pilot-20261018T225831Z/downloads.cpu-interactive.json`.

The replacement was observed running on `cn096` at 23:05:02 UTC, with four verified files (3,833,864,100 bytes) and no failures. The next shared-SSH check failed with `Permission denied (gssapi-with-mic,password)`. Authentication was not retried. That [partial status](../reports/ncsa_pilot_download_status_20261018.json) remains preserved as history.

After manual reconnection, the single BatchMode identity check confirmed `mhoda` on `dt-login02.delta.ncsa.illinois.edu`. Accounting confirmed **COMPLETED, exit `0:0`, elapsed 00:04:42**, on `cn096`, ending October 18 at 6:08:44 pm Central. The final [per-file report](../reports/pilot_downloads_22995933.json) contains exactly the approved 16 unique files, all verified, totaling **21,243,276,685 bytes**, with no failures or checkpoint download. Every path, byte count and MD5 matches the approved manifest. Retrieved report/log hashes and the staged source hashes match. Lightweight `lstat` checks confirmed final slides are regular, non-symlink files owned by `mhoda`, mode `600`; input directories have no group/other permissions. The queue was empty. [Full verification and accounting](../reports/ncsa_pilot_download_verification_20261019.json).

The download client performed streaming integrity checks on the scheduled CPU node; no redundant whole-file checksum scan occurred on the login node. Headers, MPP, coordinate geometry and broader sampling were still unverified at acquisition completion; they subsequently passed the CPU preflight recorded above. No expanded pilot, new-patient inference or GPU job was submitted during this acquisition.
