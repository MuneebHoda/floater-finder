#!/bin/bash
# One-pair, physically resampled, 128-tile CONCH v1 smoke.
#SBATCH --job-name=floater-one-pair
#SBATCH --account=bfqi-delta-gpu
#SBATCH --qos=bfqi-delta-gpu-mhoda
#SBATCH --partition=gpuA100x4
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/floater-one-pair-%j.out
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --gpus-per-node=1
#SBATCH --time=00:10:00

set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?Scheduled GPU job required}"
if [ "$#" -ne 3 ] && [ "$#" -ne 4 ]; then
    printf 'Arguments: project_snapshot existing_environment new_output_directory [verified_pair_config]\n' >&2
    exit 2
fi
project=$1
environment=$2
output=$3
config=${4:-$project/configs/ncsa_one_pair.json}
module load pytorch-conda/2.8
export PYTHONPATH="$project/src"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export OMP_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
srun "$environment/bin/python" "$project/scripts/ncsa_one_pair_smoke.py" \
    --config "$config" \
    --prompts "$project/configs/conch_smoke.yaml" --output "$output"
