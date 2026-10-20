#!/bin/bash
# Bounded existing-data CPU profiling authorized by the October 20 scale-up request.
#SBATCH --job-name=panda-profile
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:15:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-profile-%j.out
set -euo pipefail
umask 077
test "$#" -eq 3
project=$1
environment=$2
output=$3
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src" OMP_NUM_THREADS=2
srun "$environment/bin/python" "$project/scripts/ncsa_panda_profile.py" \
  --root /work/nvme/bfqi/mhoda/panda --output "$output"
