#!/usr/bin/env python3
"""Render Slurm node lines from the untracked operator inventory.

Reads operator-inventory/hosts.env (git-ignored, never commit) and prints
slurm.conf NodeName lines plus partition sketch to stdout. Stdout carries
private addresses: keep it local, never paste it into tracked files.
Profiles: docs/architecture/heterogeneous-placement.md
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV = ROOT / "operator-inventory" / "hosts.env"

SLURM_PROFILES = (
    "P_LNX_NVIDIA",
    "P_LNX_CPU",
    "P_LNX_EDGE_CPU",
    "P_LNX_ARM_EDGE",
    "P_CLD_AMD",
    "P_CLD_BURST",
)

PARTITIONS = (
    ("gpu", ("P_LNX_NVIDIA", "P_CLD_AMD")),
    ("cpu", ("P_LNX_CPU", "P_LNX_EDGE_CPU")),
    ("arm", ("P_LNX_ARM_EDGE",)),
    ("burst", ("P_CLD_BURST", "P_CLD_AMD")),
)


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def main() -> int:
    env_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ENV
    if not env_path.is_file():
        print(f"missing inventory file: {env_path}", file=sys.stderr)
        print("copy ops/slurm/hosts.env.example there and fill it in.", file=sys.stderr)
        return 1
    try:
        values = load_env(env_path)
    except UnicodeDecodeError:
        print(f"inventory file must be ASCII: {env_path}", file=sys.stderr)
        return 1

    lines: list[str] = []
    lines.append("ClusterName=neuriplo-tailnet")
    lines.append("SlurmctldHost=<controller-host>(<controller-addr>)")
    lines.append("SlurmctldPort=6817")
    lines.append("SlurmdPort=6818")
    lines.append("AuthType=auth/munge")
    lines.append("")
    for profile in SLURM_PROFILES:
        host = values.get(f"{profile}_HOST", "")
        addr = values.get(f"{profile}_ADDR", "")
        cpus = values.get(f"{profile}_CPUS", "1")
        gres = values.get(f"{profile}_GRES", "")
        features = values.get(f"{profile}_FEATURES", "")
        if not addr:
            lines.append(f"# {profile}: unassigned (planned/on-demand, not a failure)")
            continue
        node = f"NodeName={host} NodeAddr={addr} CPUs={cpus}"
        if gres:
            node += f" Gres={gres}"
        if features:
            node += f' Feature="{features}"'
        node += " State=UNKNOWN"
        lines.append(node)
    lines.append("# P_WIN_CPU: native runner, no slurmd (see scheduler job contract)")
    lines.append("")
    for name, members in PARTITIONS:
        present = [values.get(f"{p}_HOST", p) for p in members if values.get(f"{p}_ADDR", "")]
        targets = " ".join(m for m in present if m) or "<no online nodes>"
        lines.append(f"PartitionName={name} Nodes={targets} MaxTime=24:00:00 State=UP")
    print("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
