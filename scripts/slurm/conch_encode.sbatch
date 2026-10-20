#!/bin/bash
# Verify the private runtime and all input/output paths before submission.
#SBATCH --job-name=floater-conch
#SBATCH --account=bfqi-delta-gpu
#SBATCH --qos=bfqi-delta-gpu-mhoda
#SBATCH --partition=gpuA100x4
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/floater-conch-%j.out
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --gpus-per-node=1
#SBATCH --time=00:05:00

set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?Run only as an approved Slurm GPU job}"
: "${FLOATER_PROJECT_DIR:?Set to the verified remote Floater Finder checkout}"
if [ "$#" -ne 5 ]; then
    printf 'Arguments: existing_environment existing_checkpoint tile_manifest slide_metadata new_output_directory\n' >&2
    exit 2
fi
module load pytorch-conda/2.8
export PYTHONNOUSERSITE=1
export PYTHONPATH="$FLOATER_PROJECT_DIR/src"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
srun "$1/bin/python" -m floater_finder encode \
    --checkpoint "$2" --tile-manifest "$3" --metadata "$4" --output "$5" \
    --prompts "$FLOATER_PROJECT_DIR/configs/conch_smoke.yaml" --max-tiles 128 --batch-size 16
