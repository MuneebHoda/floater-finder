#!/bin/bash
#SBATCH --job-name=panda-probes-v1
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-probes-v1-%j.out
set -euo pipefail
umask 077
test "$#" -eq 8
SOURCE=$1
RUNTIME=$2
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$SOURCE/src"
export FLOATER_SOURCE_COMMIT
FLOATER_SOURCE_COMMIT=$(cat "$SOURCE/../commit.txt")
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
srun "$RUNTIME/bin/python" "$SOURCE/scripts/panda_predictor_research.py" --manifest "$3" --directories "$4" --encoded "$5" --verification "$6" --config "$7" --output "$8"
