#!/bin/bash
#SBATCH --job-name=panda-dev-baseline
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:05:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-dev-baseline-%j.out
set -euo pipefail
umask 077
test "$#" -eq 5
project=$1
environment=$2
manifest=$3
encoded=$4
output=$5
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src" OMP_NUM_THREADS=2
srun "$environment/bin/python" "$project/scripts/panda_clean_baseline.py" \
  --manifest "$manifest" --encoded-root "$encoded" --output "$output"
