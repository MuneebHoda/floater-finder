#!/bin/bash
# Pending explicit approval of the exact 60-slide acquisition plan hash.
#SBATCH --job-name=panda-fresh-acquire
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=01:00:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-fresh-acquire-%j.out
set -euo pipefail
umask 077
test "$#" -eq 3
project=$1
plan=$2
approved_sha256=$3
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src"
srun /u/mhoda/.venvs/kaggle/bin/python "$project/scripts/panda_acquire.py" \
 --plan "$plan" --root /work/nvme/bfqi/mhoda/panda \
 --receipts /work/nvme/bfqi/mhoda/panda/acquisition-receipts/fresh-radboud60-v1 \
 --approved-plan-sha256 "$approved_sha256"
