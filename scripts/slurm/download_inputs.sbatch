#!/bin/bash
# Sequential public inputs only; the Python client requires an approved plan.
#SBATCH --job-name=floater-download
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/floater-download-%j.out
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:30:00

set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?Scheduled CPU job required}"
if [ "$#" -ne 3 ]; then
    printf 'Arguments: project_snapshot approved_plan new_download_report\n' >&2
    exit 2
fi
project=$1
plan=$2
report=$3
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1
srun python "$project/scripts/download_approved_inputs.py" --plan "$plan" --report "$report"
