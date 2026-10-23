#!/bin/bash
# PREPARED ONLY: explicit user approval required before submitting this GPU job.
#SBATCH --job-name=panda-pixel-encode
#SBATCH --account=bfqi-delta-gpu
#SBATCH --qos=bfqi-delta-gpu-mhoda
#SBATCH --partition=gpuA100x4-interactive
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:05:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-pixel-encode-%j.out
set -euo pipefail
umask 077
test "$#" -eq 7
project=$1
runtime=$2
config_sha256=$3
preparation=$4
manifest_sha256=$5
output=$6
source_commit=$7
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src"
export OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
srun "$runtime/bin/python" "$project/scripts/panda_pixel_study.py" \
  --config "$project/configs/panda_pixel_contamination_v1.json" --config-sha256 "$config_sha256" \
  --preparation "$preparation" --manifest-sha256 "$manifest_sha256" \
  --output "$output" --source-commit "$source_commit" --encode
