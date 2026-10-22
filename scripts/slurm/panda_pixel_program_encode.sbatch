#!/bin/bash
# PREPARED ONLY. CPU dedup receipt, exact range, billing reconciliation and explicit
# user authorization are required before submitting a new GPU scope.
#SBATCH --job-name=panda-pixel10k-profile
#SBATCH --account=bfqi-delta-gpu
#SBATCH --qos=bfqi-delta-gpu-mhoda
#SBATCH --partition=gpuA100x4
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:15:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-pixel10k-encode-%j.out
set -euo pipefail
umask 077
test "$#" -eq 8
project=$1
runtime=$2
config_sha256=$3
preparation_sha256=$4
output=$5
split=$6
offset=$7
limit=$8
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src"
export OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
srun "$runtime/bin/python" "$project/scripts/panda_pixel_program.py" encode \
  --project "$project" --config "$project/configs/panda_gpu_program_v1/protocol.json" \
  --config-sha256 "$config_sha256" --preparation-sha256 "$preparation_sha256" \
  --output "$output" --split "$split" --offset "$offset" --limit "$limit"
