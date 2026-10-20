#!/bin/bash
# DRAFT: full-cohort GPU resources require explicit approval after profiling/CPU validation.
#SBATCH --job-name=panda-cohort-encode
#SBATCH --account=bfqi-delta-gpu
#SBATCH --qos=bfqi-delta-gpu-mhoda
#SBATCH --partition=gpuA100x4-interactive
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:45:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-cohort-encode-%j.out
set -euo pipefail
umask 077
test "$#" -eq 4
project=$1
environment=$2
directories=$3
output=$4
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src" OMP_NUM_THREADS=4
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
srun "$environment/bin/python" "$project/scripts/panda_encode_batch.py" \
  --tiling-directories "$directories" --prompts "$project/configs/panda_morphology_v1.yaml" \
  --checkpoint /work/nvme/bfqi/mhoda/floater-finder/inputs/models/conch_v1/pytorch_model.bin \
  --checkpoint-sha256 40a9644b9ba0e83a74576e0a5e5f7313599fa9c9cdaf3c20f8a3e271b0e9ae7c \
  --output "$output"
