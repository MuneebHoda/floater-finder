#!/bin/bash
# Raw inputs and spatial sampling only; no model load or GPU request.
#SBATCH --job-name=floater-preflight
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/floater-preflight-%j.out
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:15:00

set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?Scheduled CPU job required}"
if [ "$#" -ne 3 ]; then
    printf 'Arguments: project_snapshot existing_environment new_output_directory\n' >&2
    exit 2
fi
project=$1
environment=$2
output=$3
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONPATH="$project/src" PYTHONUNBUFFERED=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export OMP_NUM_THREADS=2
srun "$environment/bin/python" "$project/scripts/ncsa_pilot_preflight.py" \
    --config "$project/configs/ncsa_expanded_pilot_protocol.json" --output "$output"
