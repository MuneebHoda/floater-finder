#!/bin/bash
#SBATCH --job-name=panda-final-v1
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-final-v1-%j.out
set -euo pipefail
umask 077
test "$#" -eq 4
project=$1
environment=$2
protocol=$3
expected=$4
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src" OMP_NUM_THREADS=2
srun "$environment/bin/python" "$project/scripts/panda_review_final.py" --protocol "$protocol" \
 --expected-sha256 "$expected" --source-root "$project" --execute-final
