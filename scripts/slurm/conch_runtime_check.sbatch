#!/bin/bash
# Regenerate only the two existing development subsets with the patched runtime.
#SBATCH --job-name=floater-runtime
#SBATCH --account=bfqi-delta-gpu
#SBATCH --qos=bfqi-delta-gpu-mhoda
#SBATCH --partition=gpuA100x4
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/floater-runtime-%j.out
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --gpus-per-node=1
#SBATCH --time=00:05:00

set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?Scheduled GPU job required}"
if [ "$#" -ne 4 ]; then
    printf 'Arguments: project_snapshot new_environment legacy_development_encoding new_output_directory\n' >&2
    exit 2
fi
project=$1
environment=$2
baseline=$3
output=$4
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONPATH="$project/src"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export OMP_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
srun "$environment/bin/python" "$project/scripts/ncsa_one_pair_smoke.py" \
    --config "$project/configs/ncsa_calibration.json" \
    --prompts "$project/configs/conch_smoke.yaml" --output "$output"
srun "$environment/bin/python" "$project/scripts/ncsa_runtime_compatibility.py" \
    --baseline "$baseline" --current "$output"
