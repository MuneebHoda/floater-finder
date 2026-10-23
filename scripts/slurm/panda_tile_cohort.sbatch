#!/bin/bash
#SBATCH --job-name=panda-cohort-tiles
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:15:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-cohort-tiles-%j.out
set -euo pipefail
umask 077
test "$#" -eq 6
project=$1
environment=$2
manifest=$3
output=$4
start=$5
count=$6
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src" OMP_NUM_THREADS=2
srun "$environment/bin/python" "$project/scripts/panda_tile_cohort.py" \
  --root /work/nvme/bfqi/mhoda/panda --manifest "$manifest" --output "$output" --start "$start" --count "$count"
