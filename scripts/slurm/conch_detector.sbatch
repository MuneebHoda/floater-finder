#!/bin/bash
# Patient-separated calibration and detector controls; no model inference.
#SBATCH --job-name=floater-detector
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/floater-detector-%j.out
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:05:00

set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?Scheduled CPU job required}"
if [ "$#" -ne 5 ]; then
    printf 'Arguments: project_snapshot existing_environment development_encoding evaluation_encoding new_output_directory\n' >&2
    exit 2
fi
project=$1
environment=$2
development=$3
evaluation=$4
output=$5
module load pytorch-conda/2.8
export PYTHONPATH="$project/src"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export OMP_NUM_THREADS=2
export MPLBACKEND=Agg MPLCONFIGDIR="$output-matplotlib"
srun "$environment/bin/python" "$project/scripts/ncsa_detector_smoke.py" \
    --development "$development" --evaluation "$evaluation" \
    --config "$project/configs/ncsa_detector_smoke.json" --output "$output"
