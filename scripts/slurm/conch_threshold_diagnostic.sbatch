#!/bin/bash
# Reuse development embeddings only; no model inference or evaluation patients.
#SBATCH --job-name=floater-threshold
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/floater-threshold-%j.out
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:05:00

set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?Scheduled CPU job required}"
if [ "$#" -ne 4 ]; then
    printf 'Arguments: project_snapshot existing_environment development_encoding new_output_directory\n' >&2
    exit 2
fi
project=$1
environment=$2
development=$3
output=$4
module load pytorch-conda/2.8
export PYTHONPATH="$project/src"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export OMP_NUM_THREADS=2
export MPLBACKEND=Agg MPLCONFIGDIR="$output-matplotlib"
srun "$environment/bin/python" "$project/scripts/ncsa_threshold_diagnostic.py" \
    --development "$development" --config "$project/configs/ncsa_threshold_diagnostic.json" --output "$output"
