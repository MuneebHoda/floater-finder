#!/bin/bash
#SBATCH --job-name=panda-engine-v1
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:15:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-engine-v1-%j.out
set -euo pipefail
umask 077
test "$#" -ge 9
test "$#" -le 10
project=$1
environment=$2
manifest=$3
directories=$4
encoded=$5
verification=$6
receipts=$7
output=$8
source_commit=$9
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src" OMP_NUM_THREADS=2 FLOATER_SOURCE_COMMIT="$source_commit"
arguments=(--manifest "$manifest" --tiling-directories "$directories" --encoded-root "$encoded" --verification "$verification"
 --acquisition-receipts "$receipts" --protocol "$project/configs/research_engine_acceptance_v3.json" --source-commit "$source_commit" --output "$output")
if [ "$#" -eq 10 ]; then arguments+=(--predictor "${10}"); fi
srun "$environment/bin/python" "$project/scripts/research_engine_acceptance.py" "${arguments[@]}"
