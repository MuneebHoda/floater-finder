#!/bin/bash
#SBATCH --job-name=panda-detector-v3
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-detector-v3-%j.out
set -euo pipefail
umask 077
test "$#" -eq 10
project=$1
environment=$2
manifest=$3
directories=$4
encoded=$5
verification=$6
stress=$7
cases=$8
output=$9
source_commit=${10}
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src" OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 FLOATER_SOURCE_COMMIT="$source_commit"
srun /usr/bin/time -v "$environment/bin/python" "$project/scripts/panda_detector_v3_train.py" \
 --manifest "$manifest" --directories "$directories" --encoded "$encoded" --verification "$verification" \
 --stress "$stress" --cases "$cases" --config "$project/configs/panda_detector_v3_train_v1.json" --output "$output"
