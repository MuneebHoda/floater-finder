#!/bin/bash
# DRAFT: submit only after CPU tile inspection and new GPU-scope approval.
#SBATCH --job-name=floater-panda-conch
#SBATCH --account=bfqi-delta-gpu
#SBATCH --qos=bfqi-delta-gpu-mhoda
#SBATCH --partition=gpuA100x4
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/floater-panda-conch-%j.out
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --gpus-per-node=1
#SBATCH --time=00:05:00

set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?Approved Slurm GPU job required}"
if [ "$#" -ne 4 ]; then
    printf 'Arguments: project_snapshot prepared_environment completed_tiling_output new_encoding_output\n' >&2
    exit 2
fi
project=$1
environment=$2
tiles=$3
output=$4
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONPATH="$project/src" PYTHONUNBUFFERED=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export OMP_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
srun "$environment/bin/python" "$project/scripts/ncsa_panda_smoke.py" --stage encode --tiles "$tiles" --output "$output"
