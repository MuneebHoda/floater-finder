# Floater Finder: NCSA setup

Verified on 2026-10-17 (America/Chicago). First milestone: CONCH only.
No Slurm job, inference, whole-slide processing, or dataset/model download was performed during setup. GPU access is not yet verified.

## Latest implementation-session status

The single new connection check used `ssh -o BatchMode=yes -o ConnectTimeout=8 ncsa-floater 'whoami && hostname'`, bounded by a 15-second local process timeout. It timed out with no identity output. NCSA is temporarily unavailable for this implementation session; no authentication retry or SSH configuration edit was made. The successful identity/allocation/storage observations below are from the earlier setup session and were not reverified after this timeout.

Local development proceeded independently. A second, unsubmitted draft at [`scripts/slurm/conch_encode.sbatch`](../scripts/slurm/conch_encode.sbatch) requests account `bfqi-delta-gpu`, QoS `bfqi-delta-gpu-mhoda`, partition `gpuA100x4`, one GPU, four CPUs, 16 GB memory and five minutes for at most 128 already-tiled images. It needs a verified remote checkout, checkpoint, tile manifest, slide metadata and new output path. The documented module remains unverified. The existing two-minute driver-visibility smoke test remains separate. Neither draft has been copied, submitted, or run.

## Local execution and SSH

- Execution environment: the user's local Mac, macOS 26.6.2, local user `muneebhoda`.
- Local checkout: `/Users/muneebhoda/Documents/Masters - Fall 2026/Ashby Hackathon`.
- Repository: <https://github.com/MuneebHoda/floater-finder>.
- SSH alias: `ncsa-floater`; configured host: `login.delta.ncsa.illinois.edu`; configured user: `mhoda`.
- The user completed password/Duo authentication in their own Mac Terminal. Connection sharing subsequently succeeded with:

  ```sh
  ssh -o BatchMode=yes ncsa-floater 'whoami && hostname'
  ```

- Observed remote identity: `mhoda` on `dt-login04.delta.ncsa.illinois.edu` (Delta). The login hostname is a service name; the observed backend may change.
- Host-key verification remains enabled (`StrictHostKeyChecking ask`); agent forwarding is disabled. The control-socket directory is `~/.ssh/cm`, mode `700`; SSH configuration is mode `600`.
- Existing SSH entries were preserved and backed up outside this repository before adding the alias.
- If a batch-mode SSH command needs authentication again, stop and have the user reconnect manually with `ssh ncsa-floater`. Never request credentials or repeatedly retry authentication.

## Allocations and Slurm

The site's `accounts` command returned these balances. The user confirmed that **both allocations belong to the hackathon**. Balances are a snapshot, not a guarantee of future availability.

| Slurm account | Balance (hours) | Deposited (hours) | Site description | Default QoS from Slurm association |
| --- | ---: | ---: | --- | --- |
| `bfqi-delta-cpu` | 9,377 | 11,039 | `2025 ashby prize in...` (truncated by the site command) | `bfqi-delta-cpu` |
| `bfqi-delta-gpu` | 10 | 10 | Sub-allocation `mhoda`; marked `*` by `accounts` | `bfqi-delta-gpu-mhoda` |

`sacctmgr -n -P show assoc where user=mhoda format=Cluster,Account,User,Partition,QOS,DefaultQOS` confirmed both account names on cluster `delta`. It also listed `noalloc`, which is not selected for project work. The username `mhoda` is not the Slurm account name.

The [official hackathon compute guide](https://github.com/ncsa/ashby-hackathon-2026/blob/main/HACKATHON_COMPUTE.md#5-gpu-jobs) specifies `bfqi-delta-gpu` with partition `gpuA100x4` for event GPU jobs, one GPU per team at a time, and no explicit reservation flag. The smoke-test proposal follows these instructions. The site's `gpuA100x4` partition being the default does not remove the need to specify the intended account.

`squeue --me` returned a header with no jobs. `sinfo -o "%P|%a|%l|%D|%G"` reported the following partitions as `up`:

| Partition family | Observed variants | Time limit |
| --- | --- | --- |
| `cpu` | base, `-interactive`, `-preempt` | 48 hours; interactive 1 hour |
| `gpuA100x4` | base (site default), `-interactive`, `-preempt` | 48 hours; interactive 1 hour |
| `gpuA100x8` | base, `-interactive` | 48 hours; interactive 1 hour |
| `gpuA40x4` | base, `-interactive`, `-preempt` | 48 hours; interactive 1 hour |
| `gpuH200x8` | base, `-interactive` | 48 hours; interactive 1 hour |
| `gpuMI100x8` | base, `-interactive` | 48 hours; interactive 1 hour |
| `full` | base | 24 hours |

Listed partitions and account associations do not establish that a particular job can be scheduled, that a GPU has been allocated, or that CUDA/CONCH works.

## Verified directories and documentation

Directory checks were limited to the user's home, the hackathon allocation roots, and relevant shared directories. No filesystem-wide search, model-file read, or dataset-content inspection was performed.

| Location | What was verified |
| --- | --- |
| `/u/mhoda` | Remote home and initial working directory; no non-hidden entries at inspection time. |
| `/projects/bfqi` | Exists and is a directory; relevant top-level entries inspected. |
| `/projects/bfqi/shared` | Exists; its only non-hidden entry was `datasets`. |
| `/projects/bfqi/shared/datasets` | Exists; its non-hidden entries were the three directories listed below. The listing was slow but completed; no cancellation signal was sent. |
| `/projects/bfqi/shared/datasets/NCT-CRC-HE-100K` | Directory listed; contents, provenance, and suitability for this milestone were not checked. |
| `/projects/bfqi/shared/datasets/pathgen_dataset` | Directory listed; contents, provenance, and suitability for this milestone were not checked. |
| `/projects/bfqi/shared/datasets/pathmmu` | Directory listed; contents, provenance, and suitability for this milestone were not checked. |
| `/projects/bfqi/shared/datasets/NCT-CRC-HE-100K/data-samples` | Exists and is a directory; permission checks report readable and not writable. Tile contents were not opened. |
| `/projects/bfqi/mhoda` | Exists; no non-hidden entries at inspection time. |
| `/work/nvme/bfqi` | Exists; permission checks report readable and writable. |
| `/work/nvme/bfqi/mhoda` | Exists; no non-hidden entries; permission checks report readable and writable. The event guide designates this personal NVMe area for data and outputs. No write was attempted. |
| `/work/hdd/bfqi` | Exists and is a directory; relevant top-level entries inspected. |
| `/work/hdd/bfqi/mhoda` | Exists; no non-hidden entries at inspection time. |
| `/projects/bfqi/data_test_simple` | Exists and is a directory; contents and intended use were not checked. |
| `/projects/bfqi/data_test_difficult` | Exists and is a directory; contents and intended use were not checked. |

`WORK`, `SCRATCH`, `PROJECT`, and `PROJECTS` were unset in the inspected remote shell. The smoke-test proposal uses the verified personal NVMe directory for its working directory and small log. Persistent Floater Finder output organization and any shared team directory remain undecided. No remote write was attempted.

The local `2026_Ashby_Hackathon_Welcome.pdf` was checked, including pages 21-24. It states that pretrained weights and datasets are preloaded but supplies no concrete shared-repository, CONCH-weight, or output paths. Its Box resources link could not be accessed by the web tool. The user subsequently clarified that no compute README was available and requested a search.

That search located the **official toolkit repository**, <https://github.com/ncsa/ashby-hackathon-2026>. Its [README](https://github.com/ncsa/ashby-hackathon-2026/blob/main/README.md) points students to [HACKATHON_COMPUTE.md](https://github.com/ncsa/ashby-hackathon-2026/blob/main/HACKATHON_COMPUTE.md). The inspected compute-guide blob SHA was `97d44f539c379b4591e8f93fec85dd91b6cba693`.

Verified from that guide and kept distinct from execution checks:

- Use the existing shared datasets in place; use `/work/nvme/bfqi/mhoda` for personal data and outputs. The guide reports filesystem problems with `/work/hdd` this weekend; its existence above is not a recommendation to use it.
- The documented environment is `pytorch-conda/2.8`, with `open_clip_torch` and CONCH packages for self-hosted inference. Module/package availability was not tested, and nothing was installed.
- The guide documents individual gated CONCH access and first-use weight downloads. It does not identify a concrete preloaded CONCH checkpoint path. This setup did not inspect credential files, authenticate to Hugging Face, load a model, or download weights.
- Hosted pathology services are described, but no credentials or connection files were read and no service inference request was made.

A bounded, filename-only README search under `/projects/bfqi` stopped at depth three and excluded datasets, model directories, environments, and hidden directories. Some directories were inaccessible; other teams' documents were not opened. No official toolkit checkout or Floater Finder deployment path has been designated for this user, and no remote clone was created.

Official references checked:

- [Delta job and partition documentation](https://docs.ncsa.illinois.edu/systems/delta/en/latest/user_guide/running_jobs.html).
- [Delta storage documentation](https://docs.ncsa.illinois.edu/systems/delta/en/latest/user_guide/data_mgmt.html), which documents allocation-specific storage under `/projects` and `/work/hdd`.

## Proposed smoke test: not submitted

Review [`scripts/ncsa_smoke.sbatch`](../scripts/ncsa_smoke.sbatch). It proposes one NVIDIA GPU on the event's documented `gpuA100x4` partition, one CPU, 2 GB memory, and a two-minute limit, charged to the verified GPU account and QoS. It prints a compute-node hostname and queries GPU identity/driver information through `srun`. It loads no models and reads no datasets.

The proposed working directory is the verified `/work/nvme/bfqi/mhoda`; the proposed new log file is `floater-smoke-<job-id>.out` there. These are draft job settings, not evidence of a completed write. Obtain explicit user approval before copying/submitting the job. Bash syntax checking passed locally; Slurm scheduling was not tested. No remote copy or submission has been performed.

A successful scheduled run would verify Slurm GPU allocation and driver visibility only. CUDA/PyTorch execution and CONCH inference would still require separate approved checks.

## Unresolved inputs

- Intended remote Floater Finder/toolkit checkout path; the official upstream repository is now identified above.
- Exact existing CONCH checkpoint path/version, if any; actual Python/module availability and individual gated-access status. Do not trigger a download while checking.
- Which dataset(s) and subset belong to the CONCH milestone, and their verified paths.
- Actual write success/quota on the documented personal NVMe area, plus the persistent Floater Finder output layout and any shared team location.
- Whether the proposed smoke job is schedulable and runs successfully; GPU access remains unverified.

Next command, from the local checkout, reviews the draft without running it:

```sh
cat scripts/ncsa_smoke.sbatch
```

Keep `AGENTS.md` safeguards in force. Do not submit jobs or make large downloads without asking. Do not commit or publish local setup details or supplied project documents without authorization.
