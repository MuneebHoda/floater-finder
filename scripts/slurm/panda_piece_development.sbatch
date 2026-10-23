#!/bin/bash
#SBATCH --job-name=panda-piece-dev
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-piece-dev-%j.out
set -euo pipefail
umask 077
test "$#" -eq 8
project=$1
environment=$2
manifest=$3
directories=$4
encoded=$5
verification=$6
stress=$7
output=$8
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src" OMP_NUM_THREADS=2
srun "$environment/bin/python" "$project/scripts/panda_piece_development.py" \
  --manifest "$manifest" --tiling-directories "$directories" --encoded-root "$encoded" \
  --verification "$verification" --stress "$stress" --output "$output"
