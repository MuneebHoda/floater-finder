#!/bin/bash
#SBATCH --job-name=panda-probe-adapter
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-probe-adapter-%j.out
set -euo pipefail
umask 077
test "$#" -eq 9
project=$1
runtime=$2
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export FLOATER_SOURCE_COMMIT
FLOATER_SOURCE_COMMIT=$(cat "$project/../commit.txt")
srun "$runtime/bin/python" "$project/scripts/panda_predictor_adapter_verify.py" --manifest "$3" --directories "$4" --encoded "$5" --verification "$6" --baseline "$7" --previous "$8" --output "$9"
