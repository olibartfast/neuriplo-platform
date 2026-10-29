# Slurm Binding Helper (local-only)

This directory holds tracked, data-free tooling. Real addresses live only
in `operator-inventory/hosts.env` (git-ignored, never commit).

## Files

- `hosts.env.example`: placeholder inventory. Copy to
  `operator-inventory/hosts.env` and fill in real values.
- `render_bindings.py`: reads the untracked inventory and prints
  `slurm.conf` NodeName lines plus a partition sketch.

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
