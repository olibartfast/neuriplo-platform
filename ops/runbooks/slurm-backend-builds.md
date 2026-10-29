# Slurm Backend Builds Runbook

Use this when building different `neuriplo` backend Docker images in
parallel on the Slurm cluster. Validation sessions follow
`scheduled-validation-session.md`; this runbook covers build
orchestration only. Job identity and evidence rules come from
`contracts/scheduler-job-contract.md`; profiles come from
`docs/architecture/heterogeneous-placement.md`. Name profiles, never
machines: no hostnames, addresses, credentials, or private paths in
tracked files.

## Prerequisites

- One Slurm controller plus at least one worker, all on the same Slurm
  major/minor release. A version mismatch (for example a 23.11 worker
  against a 25.11 controller) cannot join the cluster.
- A shared munge key on controller and every worker, mode 0400,
  owned by the munge user. Workers with different keys fail with a
  protocol authentication error at task launch.
- A minimal `slurm.conf` (see step 1). The helper
  `ops/slurm/render_bindings.py` renders node lines from the untracked
  operator inventory; its stdout stays local and is never committed.
- Docker usable by the job user on every build worker. The base
  `Dockerfile.<backend>` files live in the `neuriplo` repo; a job
  clones them at a pinned `develop` commit, so no source is copied by
  hand.

## Procedure

1. Bring up the cluster (controller, workers, daemons, verification).
2. Dispatch one `sbatch` job per backend on the routed profiles.
3. Collect one evidence record per job.
4. Stop session-scoped activity and verify nothing is left running.

### Step 1: bring-up (once per session)

1. Install matching `slurmctld` (controller) and `slurmd` plus `munge`
   packages on the assigned nodes. Do not mix distribution packages
   across OS releases to force a version match.
2. Install the shared munge key on each worker (`install -o munge
   -g munge -m 0400`) and restart the munge daemon everywhere.
3. Install the rendered `slurm.conf` on controller and workers.
   Distribution packages run the controller as an unprivileged
   service user, so the config must set `SlurmUser`/`SlurmdUser` to
   match the unit files; otherwise `slurmctld` refuses to start.
4. Start `slurmctld` on the controller, (re)start `slurmd` on the
   workers, then verify with `sinfo` and a two-node `srun hostname`.
   A node that stays down is left down; it is not a failure, and no
   job is routed to it.

### Step 2: dispatch

- One `sbatch` job per backend, pinned with `--nodelist` so parallel
  builds land on different workers. Example binding only (identity
  fields per the scheduler job contract):
  `sbatch --nodelist <worker> build.sh ggml`, where the script clones
  the pinned `neuriplo` commit and runs
  `docker build --target builder -f docker/Dockerfile.<backend> .`
- Backend-to-profile routing follows the placement doc: CPU-only
  backends (GGML, OpenVINO, LibTensorFlow, LibTorch CPU, ExecuTorch,
  llama.cpp CPU) on `P-LNX-CPU` / `P-LNX-EDGE-CPU`; TensorRT only on
  `P-LNX-NVIDIA`; MIGraphX only on `P-CLD-AMD` when that profile is
  online. Offline profiles are skipped, never failed.
- ARM edge workers without a version-matched `slurmd` (for example a
  Tegra image where the package feed only offers an older Slurm and
  the image must not take foreign upgrades) do NOT join the cluster.
  They still build natively with Docker over SSH in parallel with the
  Slurm jobs; record that routing explicitly in the evidence.
- Evidence per job: job identity echo, image tag plus digest,
  `BUILD_OK` (or failure) line from the job log, log reference,
  session ID. A `BUILD_OK` line alone is not a semantic pass; it only
  proves the builder image compiled.

### Step 3: known operational notes

- Slurm task launch can drop supplementary groups that are present in
  interactive logins (observed: the docker group missing inside the
  job while present over SSH). Prefix docker commands in the job
  script with `sg docker -c` to re-resolve membership from the group
  database.
- The renderer emits a partition sketch, not a validated config:
  unassigned profiles render as literal placeholder tokens that
  `slurmctld` rejects. For bring-up, hand-check a minimal config
  (controller, one partition, assigned nodes only) before scaling up.
- Building Slurm from source is a last resort for version-locked
  workers: it needs the full toolchain plus dev headers on the
  worker. Prefer distribution packages with matching versions.
- The SlurmUser UID/GID must be identical on controller and workers.
  Check `id slurm` everywhere: a mismatch surfaces as
  "Security violation ... uid X != Slurm uid" and cross-node jobs
  fail even when munge keys match. Remap with usermod/groupmod and
  chown the spool, log, key and config trees.
- Locked-down ARM workers (no foreign apt, no SDK headers) can run
  an extracted matching-version Slurm without touching the package
  database: unpack the backend and daemon debs with `dpkg-deb -x`
  under a prefix such as `/opt`, bind-mount or symlink the
  `slurm-wlm` plugin dir where the configured Plugindir expects it,
  create the slurm user, and launch munged/slurmd from the prefix
  with `LD_LIBRARY_PATH` pointed at it. Never install foreign
  packages on images where that risks the boot chain.

### Step 4: stop and verify

`squeue` empty, no `slurm-build` clones left behind unless kept as
evidence, daemons left running only when an always-available queue is
recorded with an owner. Never stop unrelated services or change
drivers as part of a build session.
