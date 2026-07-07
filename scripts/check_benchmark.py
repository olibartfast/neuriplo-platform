#!/usr/bin/env python3
"""Validate benchmark result JSON against contracts/benchmarking-contract.md.

Checks structural conformance only. A field may be null when the source run did
not measure it (the contract allows unmeasured fields to be reported as null
rather than omitted), but the key must be present so consumers can rely on the
shape.

Usage:
  scripts/check_benchmark.py [PATH ...]

With no PATH, validates every *.json under integration-tests/**/results/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

TOP_LEVEL_REQUIRED = [
    "benchmark_version",
    "compatibility_set",
    "timestamp",
    "hardware",
    "backend",
    "model",
    "results",
]

HARDWARE_REQUIRED = ["device_name", "driver_version", "memory_mib"]
BACKEND_REQUIRED = ["name", "version"]
MODEL_REQUIRED = ["name", "sha256"]
RESULT_REQUIRED = ["scenario", "batch_size", "metrics"]
METRICS_REQUIRED = [
    "requests_per_second",
    "latency_p50_ms",
    "latency_p95_ms",
    "latency_p99_ms",
    "gpu_utilization_pct",
    "gpu_memory_used_mib",
]

ALLOWED_CATEGORIES = {"single_stream", "batched_throughput", "max_throughput"}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def require_keys(
    errors: list[str], where: str, obj: Any, keys: list[str]
) -> bool:
    if not isinstance(obj, dict):
        fail(errors, f"{where}: expected object, got {type(obj).__name__}")
        return False
    ok = True
    for key in keys:
        if key not in obj:
            fail(errors, f"{where}: missing required field '{key}'")
            ok = False
    return ok


def validate_result(errors: list[str], where: str, result: Any) -> None:
    if not require_keys(errors, where, result, RESULT_REQUIRED):
        return
    scenario = result["scenario"]
    if not isinstance(scenario, str) or not scenario:
        fail(errors, f"{where}: scenario must be a non-empty string")
    category = result.get("category")
    if category is not None and category not in ALLOWED_CATEGORIES:
        fail(errors, f"{where}: category '{category}' not in {sorted(ALLOWED_CATEGORIES)}")
    batch = result["batch_size"]
    if not isinstance(batch, int) or batch < 1:
        fail(errors, f"{where}: batch_size must be an integer >= 1")
    require_keys(errors, f"{where}.metrics", result["metrics"], METRICS_REQUIRED)


def validate_document(errors: list[str], rel: str, doc: Any) -> None:
    if not require_keys(errors, rel, doc, TOP_LEVEL_REQUIRED):
        return
    require_keys(errors, f"{rel}.hardware", doc["hardware"], HARDWARE_REQUIRED)
    require_keys(errors, f"{rel}.backend", doc["backend"], BACKEND_REQUIRED)
    require_keys(errors, f"{rel}.model", doc["model"], MODEL_REQUIRED)

    results = doc["results"]
    if not isinstance(results, list) or not results:
        fail(errors, f"{rel}.results: must be a non-empty array")
        return
    for index, result in enumerate(results):
        validate_result(errors, f"{rel}.results[{index}]", result)


def discover_paths() -> list[Path]:
    return sorted(ROOT.glob("integration-tests/**/results/*.json"))


def main(argv: list[str]) -> int:
    if argv:
        paths = [Path(arg).resolve() for arg in argv]
    else:
        paths = discover_paths()

    if not paths:
        print("no benchmark result files found")
        return 0

    errors: list[str] = []
    for path in paths:
        try:
            rel = str(path.relative_to(ROOT))
        except ValueError:
            rel = str(path)
        if not path.is_file():
            fail(errors, f"{rel}: file not found")
            continue
        try:
            doc = json.loads(path.read_text(encoding="ascii"))
        except UnicodeDecodeError:
            fail(errors, f"{rel}: non-ASCII content")
            continue
        except json.JSONDecodeError as exc:
            fail(errors, f"{rel}: invalid JSON: {exc}")
            continue
        validate_document(errors, rel, doc)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"benchmark results ok ({len(paths)} file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
