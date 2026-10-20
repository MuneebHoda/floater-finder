#!/bin/bash
# DRAFT: submit only after the new PANDA smoke scope is approved.
#SBATCH --job-name=floater-panda-tiles
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/floater-panda-tiles-%j.out
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:10:00

set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?Approved Slurm job required}"
if [ "$#" -ne 3 ]; then
    printf 'Arguments: project_snapshot prepared_environment new_tiling_output\n' >&2
    exit 2
fi
project=$1
environment=$2
output=$3
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONPATH="$project/src" PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=2
srun "$environment/bin/python" "$project/scripts/ncsa_panda_smoke.py" --stage tile --output "$output"
