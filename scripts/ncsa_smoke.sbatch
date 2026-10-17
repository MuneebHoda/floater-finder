#!/bin/bash
# Draft only: obtain user approval before copying or submitting this job.
#SBATCH --job-name=floater-smoke
#SBATCH --account=bfqi-delta-gpu
#SBATCH --qos=bfqi-delta-gpu-mhoda
#SBATCH --partition=gpuA100x4
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/floater-smoke-%j.out
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --gpus-per-node=1
#SBATCH --time=00:02:00

set -euo pipefail
: "${SLURM_JOB_ID:?Run only as an approved Slurm job}"

printf 'Slurm job: %s\n' "$SLURM_JOB_ID"
srun --ntasks=1 hostname
srun --ntasks=1 nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
