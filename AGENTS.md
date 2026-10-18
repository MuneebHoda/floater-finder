# Floater Finder

- The first Ashby Hackathon milestone uses CONCH only. Keep work within this scope.
- Access NCSA Delta through the local SSH alias `ncsa-floater`; the supplied login is `mhoda` at `login.delta.ncsa.illinois.edu`. Verify the remote identity after connecting.
- Run all heavy processing, CONCH inference, whole-slide processing, and GPU workloads through Slurm, never directly on a login node. Login nodes are for lightweight inspection and job preparation.
- Do not invent Slurm allocations/accounts, model paths, dataset paths, shared repository paths, or output locations. Record verified facts and unresolved inputs in `docs/ncsa_setup.md`.
- Never fabricate scientific results. Report only observed outputs, and claim GPU access is verified only after a scheduled GPU job succeeds.
- On 2026-10-18 the user authorized continuing this CONCH plan without repeated permission requests, including needed Delta jobs. This covers bounded public diagnostic inputs for separate calibration patients; do not expand into bulk cohorts or additional models without authorization. Use verified allocations and at most one GPU at a time; keep runs bounded and inspect failures before resubmitting. Do not download datasets or model weights during connection setup.
- Never read, print, or store passwords, tokens, or private keys in repository files or logs. Authentication and Duo prompts must be completed by the user in their own Mac Terminal; never automate or bypass them.
- Keep SSH host-key verification enabled and agent forwarding disabled. Ask before editing local SSH configuration; back it up first, preserve existing entries, and avoid duplicate host entries.
- After the user confirms manual authentication, test once with `ssh -o BatchMode=yes ncsa-floater 'whoami && hostname'`. If authentication is needed again, stop and ask the user to reconnect manually; never retry repeatedly or request credentials.
- Inspect only relevant remote directories. Run the site's `accounts` command and inspect available Slurm partitions and the user's queue. If multiple allocations are available, ask which belongs to the hackathon before selecting one.
- Preserve existing work and do not commit or publish local connection details or project documents without user authorization.
- Keep fixture, real-data smoke, pilot, and benchmark outputs distinct. Artificial arrays are software checks, never scientific results; freeze prompts before evaluation and keep calibration patients separate from evaluation hosts and donors.
- Treat any oracle-removal failure as a pipeline defect that stops the experiment. Record exact configuration, model/checkpoint provenance, requested/realized contamination, raw scores, exclusions, and metric denominators.
