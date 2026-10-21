# Approved dependent pixel GPU submission

The user instructed **“Submit GPU execution and commit the code”** while CPU
preparation23109277 was still pending. This authorizes submission of the
previously proposed one-A100,four-CPU,16GB,five-minute run. It supersedes waiting
for another approval after CPU completion; actual CPU validity,source integrity,
manifest freezing and unchanged-tile drift gates remain mandatory.

Submit exactly one GPU job with `--dependency=afterok:23109277` and
`--kill-on-invalid-dep=yes`. A pending dependency reserves no running GPU
allocation; failed CPU preparation must not launch inference. Do not submit
another CPU preparation,download any input,change pairs/crops/scorers,refit a
model or touch original final-test artifacts. Do not automatically retry a
failed GPU job.

The small launcher is `scripts/panda_pixel_after_cpu.py`, scheduled through
`scripts/slurm/panda_pixel_after_cpu.sbatch`. It uses the already verified
private runtime and source `61959fa148a4a3ae4aadb5ee84b9578933140f6b` at
`/u/mhoda/floater-finder/releases/panda-pixel-contamination-v1-20261021T223344Z/source`.
The original scientific protocol SHA256 remains
`33594b467bdd16c75e3b4835a744bab2e917972266a31e33779ac0be386eefb7`.
The original source-manifest SHA256 remains
`573c26663c3dec96b080c3f186573c513c39ff3408e469dc64f501140e894618`.
No frozen runtime/scientific file is edited.

After the successful CPU dependency, the launcher verifies every original
runtime file against the pinned source manifest, calls the existing input/model
preflight and prepared-image verifier, checks the exact expected CPU job/source/
protocol/pairs and absence of GPU output, and freezes the **actual** image-manifest
SHA256 in a new exclusive receipt. Missing,altered,incomplete or wrong-job
artifacts stop execution. It never substitutes a candidate pair or fabricated
manifest hash. Ground truth remains outside the detector callable.

The launcher then executes the unchanged original
`scripts/slurm/panda_pixel_encode.sbatch` with its seven original arguments and
the verified real manifest hash. The allocated resources come from the new
outer Slurm script with identical caps; the original script's directives are
comments when invoked by Bash inside that allocation. Its module/offline
settings,single-GPU check,checkpoint hash,canonical preprocessing,eight-anchor
drift gate,96-image encoding,48-null drift gate and frozen measurements all
remain unchanged. No CONCH inference occurs in the launcher itself.

The real manifest does **not** exist at queue submission while CPU preparation
is pending. The hash is resolved only from the successful CPU's immutable
receipt,checked before encoder initialization,and passed explicitly to the old
runner. Queue acceptance is not preparation success,GPU execution or a
scientific result. Rectangular seam confounding remains unresolved.

Both wrappers are tested for the same one-GPU/four-CPU/16GB/five-minute caps.
Tests cover missing CPU completion,wrong job/source/scope/pairs,source mutation,
existing GPU outputs,exclusive manifest-freeze receipts and exact forwarding to
the unchanged runner. They use artificial inputs and a fake exec,not real data
or CUDA. The execution report will record the exact staged command,authorization,
job ID,dependency,resources and observed scheduler state.
