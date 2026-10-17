#!/bin/bash
# Draft only. Approve the job and verify all four input/output paths before submission.
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
: "${SLURM_JOB_ID:?Run only as an approved Slurm GPU job}"
: "${FLOATER_PROJECT_DIR:?Set to the verified remote Floater Finder checkout}"
if [ "$#" -ne 4 ]; then
    printf 'Arguments: existing_checkpoint tile_manifest slide_metadata new_output_directory\n' >&2
    exit 2
fi
module load pytorch-conda/2.8
unset PYTHONNOUSERSITE
export PYTHONPATH="$FLOATER_PROJECT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
srun python -m floater_finder encode \
    --checkpoint "$1" --tile-manifest "$2" --metadata "$3" --output "$4" \
    --prompts "$FLOATER_PROJECT_DIR/configs/conch_smoke.yaml" --max-tiles 128 --batch-size 16
