# Slurm Binding Helper (local-only)

This directory holds tracked, data-free tooling. Real addresses live only
in `operator-inventory/hosts.env` (git-ignored, never commit).

## Files

- `hosts.env.example`: placeholder inventory. Copy to
  `operator-inventory/hosts.env` and fill in real values.
- `render_bindings.py`: reads the untracked inventory and prints
  `slurm.conf` NodeName lines plus a partition sketch.

## Daemon Prerequisites

The renderer only produces node and partition lines. A working cluster also
needs the Slurm daemons installed and running:

- `slurmctld` on the controller and `slurmd` on every worker, from the same
  Slurm major/minor release. Version-mismatched workers cannot join.
- `munge` on every node with one shared key, installed mode 0400 and owned by
  the munge user. A different key fails task launch with a protocol
  authentication error.
- `SlurmUser` and `SlurmdUser` matching the distribution unit files, with the
  same UID/GID on controller and workers. A mismatch surfaces as
  `Security violation ... uid X != Slurm uid`.
- Docker usable by the job user on build workers. Slurm task launch can drop
  supplementary groups, so prefix Docker commands with `sg docker -c`.

Start `slurmctld` first, then `slurmd` on each worker, and verify with `sinfo`
and a two-node `srun hostname`. Workers without a version-matched `slurmd`
(for example locked-down ARM images) do not join the cluster; they build
natively over SSH and record that routing in the evidence. See the
[Slurm backend builds runbook](../runbooks/slurm-backend-builds.md) for
bring-up, dispatch, and teardown.

## Use

```bash
cp ops/slurm/hosts.env.example operator-inventory/hosts.env
# fill in real hosts/addresses in operator-inventory/hosts.env
python3 ops/slurm/render_bindings.py --controller P_LNX_NVIDIA > /tmp/slurm.conf
```

Stdout carries private addresses: keep it on the local machine, never
paste it into tracked files, evidence attachments, or chat. Profiles are
defined in `docs/architecture/heterogeneous-placement.md`; job identity
follows `contracts/scheduler-job-contract.md`.
