#!/bin/bash
# Versioned source-path correction; preserves all v1 outputs and hash guards.
#SBATCH --job-name=panda-pixel10k-v2
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-pixel10k-v2-%j.out
set -euo pipefail
umask 077
test "$#" -eq 4
project=$1
runtime=$2
config_sha256=$3
output=$4
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src"
export OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
srun "$runtime/bin/python" "$project/scripts/panda_pixel_program.py" prepare \
  --project "$project" --config "$project/configs/panda_gpu_program_v2/protocol.json" \
  --config-sha256 "$config_sha256" --output "$output"
