#!/bin/bash
#SBATCH --job-name=panda-review-v2
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-review-v2-%j.out
set -euo pipefail
umask 077
test "$#" -eq 5
project=$1
environment=$2
cases=$3
output=$4
commit=$5
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src" OMP_NUM_THREADS=2
srun "$environment/bin/python" "$project/scripts/panda_review_v2.py" --cases "$cases" \
 --config "$project/configs/panda_review_v2_development.json" --output "$output" --source-commit "$commit"
