#!/bin/bash
# User authorized GPU submission; scheduler dependency and CPU receipt gate remain mandatory.
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
launcher=$1
project=$2
runtime=$3
config_sha256=$4
source_manifest_sha256=$5
cpu_job=$6
source_commit=$7
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src"
export OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
exec "$runtime/bin/python" "$launcher/scripts/panda_pixel_after_cpu.py" \
  --project "$project" --runtime "$runtime" --config-sha256 "$config_sha256" \
  --source-manifest-sha256 "$source_manifest_sha256" --cpu-job "$cpu_job" --source-commit "$source_commit"
