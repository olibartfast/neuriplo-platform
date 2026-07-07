#!/usr/bin/env python3
"""Validate benchmark baseline references declared in versions.yaml."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised only on missing dep
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="ascii") as handle:
        return yaml.safe_load(handle)


def main(argv: list[str]) -> int:
    versions_path = Path(argv[0]).resolve() if argv else ROOT / "versions.yaml"
    versions = load_yaml(versions_path)
    errors: list[str] = []

    for compat in versions.get("compatibility_sets", []):
        name = compat.get("name", "<unnamed>")
        baselines = compat.get("benchmark_baselines", [])
        if not isinstance(baselines, list):
            errors.append(f"{name}: benchmark_baselines must be a list")
            continue
        seen: set[str] = set()
        for index, baseline in enumerate(baselines):
            if not isinstance(baseline, dict):
                errors.append(f"{name}: benchmark_baselines[{index}] must be an object")
                continue
            scenario = baseline.get("scenario")
            file_name = baseline.get("file")
            if not scenario:
                errors.append(f"{name}: benchmark_baselines[{index}] missing scenario")
            elif scenario in seen:
                errors.append(f"{name}: duplicate benchmark scenario {scenario}")
            else:
                seen.add(str(scenario))
            if not file_name:
                errors.append(f"{name}: benchmark_baselines[{index}] missing file")
                continue
            baseline_path = (versions_path.parent / str(file_name)).resolve()
            try:
                baseline_path.relative_to(versions_path.parent)
            except ValueError:
                errors.append(f"{name}: baseline file escapes repository: {file_name}")
                continue
            if not baseline_path.is_file():
                errors.append(f"{name}: baseline file not found: {file_name}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("benchmark baseline references ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
