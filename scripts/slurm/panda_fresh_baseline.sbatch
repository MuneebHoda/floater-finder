#!/bin/bash
# Draft: clean validation only after fresh input/encoding gates and execution approval.
#SBATCH --job-name=panda-fresh-baseline
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-fresh-baseline-%j.out
set -euo pipefail
umask 077
test "$#" -eq 8
project=$1
runtime=$2
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src"
export OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
srun "$runtime/bin/python" "$project/scripts/panda_fresh_baseline.py" \
 --protocol "$project/configs/panda_fresh_baseline_v1/protocol.json" --protocol-sha256 "$3" \
 --directories "$4" --encoded "$5" --verification "$6" --output "$7" --source-commit "$8" --execute-fresh
