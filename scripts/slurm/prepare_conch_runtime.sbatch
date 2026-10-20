#!/bin/bash
# Runtime preparation and header/checksum inspection only; no model inference.
#SBATCH --job-name=floater-prepare
#SBATCH --account=bfqi-delta-cpu
#SBATCH --qos=bfqi-delta-cpu
#SBATCH --partition=cpu
#SBATCH --chdir=/work/nvme/bfqi/mhoda
#SBATCH --output=/work/nvme/bfqi/mhoda/floater-prepare-%j.out
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:10:00

set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?Scheduled job required}"
if [ "$#" -ne 3 ]; then
    printf 'Arguments: project_snapshot new_environment new_output_directory\n' >&2
    exit 2
fi
project=$1
environment=$2
output=$3
module load pytorch-conda/2.8
export OMP_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
test ! -e "$environment"
python -m venv --system-site-packages "$environment"
pillow_requirement=$(python -c 'import sys,tomllib; print(next(v for v in tomllib.load(open(sys.argv[1], "rb"))["project"]["dependencies"] if v.startswith("Pillow==")))' "$project/pyproject.toml")
"$environment/bin/python" -m pip --isolated --disable-pip-version-check install \
    --no-input --no-cache-dir --no-deps --only-binary=:all: \
    --index-url https://pypi.org/simple \
    "$pillow_requirement" ftfy==6.3.1 openslide-python==1.4.6 openslide-bin==4.0.1.2
"$environment/bin/python" -m pip --isolated --disable-pip-version-check install \
    --no-input --no-deps --no-build-isolation \
    "$project/vendor/CONCH-141cc09c7d4ff33d8eda562bd75169b457f71a62"
export PYTHONPATH="$project/src"
srun "$environment/bin/python" "$project/scripts/ncsa_runtime_preflight.py" \
    --config "$project/configs/ncsa_one_pair.json" --output "$output"
