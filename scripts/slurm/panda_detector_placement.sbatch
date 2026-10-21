#!/bin/bash
#SBATCH --job-name=panda-placement-v1
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-placement-v1-%j.out
set -euo pipefail
umask 077
test "$#" -eq 11
project=$1
environment=$2
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
srun "$environment/bin/python" "$project/scripts/panda_detector_placement.py" \
 --manifest "$3" --directories "$4" --encoded "$5" --verification "$6" \
 --engine-run "$7" --cases "$8" --predictor "$9" --output "${10}" --source-commit "${11}" \
 --protocol "$project/configs/panda_detector_placement_v1.json"
