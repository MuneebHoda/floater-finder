#!/bin/bash
# DRAFT: requires approval of the exact plan and replacement of acquisition 23030528.
#SBATCH --job-name=panda-selective
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=01:00:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-selective-%j.out
set -euo pipefail
umask 077
test "$#" -eq 5
project=$1
plan=$2
root=$3
receipts=$4
approved_sha256=$5
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src"
srun /u/mhoda/.venvs/kaggle/bin/python "$project/scripts/panda_acquire.py" \
  --plan "$plan" --root "$root" --receipts "$receipts" --approved-plan-sha256 "$approved_sha256"
