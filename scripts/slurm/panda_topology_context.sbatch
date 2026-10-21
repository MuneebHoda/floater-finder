#!/bin/bash
# Frozen original-development diagnostic, no predictions or policy fitting.
#SBATCH --job-name=panda-topology-context
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu-interactive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/panda-topology-context-%j.out
set -euo pipefail
umask 077
test "$#" -eq 5
project=$1
runtime=$2
config_sha256=$3
output=$4
source_commit=$5
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$project/src"
export OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
srun "$runtime/bin/python" "$project/scripts/panda_topology_context.py" \
  --config "$project/configs/panda_topology_context_v1.json" --config-sha256 "$config_sha256" \
  --output "$output" --source-commit "$source_commit" --execute
