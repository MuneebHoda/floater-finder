#!/bin/bash
# Reuse encoded arrays; no GPU request and no new inference.
#SBATCH --job-name=floater-two-way
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/floater-two-way-%j.out
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:05:00

set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?Scheduled CPU job required}"
if [ "$#" -ne 4 ]; then
    printf 'Arguments: project_snapshot existing_environment passing_gpu_output new_output_directory\n' >&2
    exit 2
fi
project=$1
environment=$2
input=$3
output=$4
module load pytorch-conda/2.8
export PYTHONPATH="$project/src"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export OMP_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false MPLBACKEND=Agg
export MPLCONFIGDIR="$output-matplotlib"
srun "$environment/bin/python" "$project/scripts/ncsa_bidirectional_smoke.py" \
    --input "$input" --prompts "$project/configs/conch_smoke.yaml" --output "$output"
