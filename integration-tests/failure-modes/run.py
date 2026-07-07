#!/usr/bin/env python3
"""Validate the platform failure-mode contract matrix."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised only on missing dep
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc

ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = Path(__file__).resolve().parent / "cases.yaml"

REQUIRED_CASES = {
    "model-not-found": ("MODEL_NOT_FOUND", 404, "NOT_FOUND"),
    "model-load-failure": ("MODEL_LOAD_FAILED", 500, "INTERNAL"),
    "backend-unavailable": ("BACKEND_UNAVAILABLE", 503, "UNAVAILABLE"),
    "invalid-tensor-shape": ("INVALID_TENSOR_SHAPE", 400, "INVALID_ARGUMENT"),
    "queue-full": ("QUEUE_FULL", 429, "RESOURCE_EXHAUSTED"),
    "request-timeout": ("REQUEST_TIMEOUT", 504, "DEADLINE_EXCEEDED"),
    "gpu-oom": ("GPU_OOM", 503, "RESOURCE_EXHAUSTED"),
    "unsupported-dtype": ("UNSUPPORTED_DTYPE", 400, "INVALID_ARGUMENT"),
    "version-mismatch": ("VERSION_MISMATCH", 409, "FAILED_PRECONDITION"),
}

ALLOWED_OWNERS = {
    "neuriplo-platform",
    "neuriplo",
    "neuriplo-tasks",
    "neuriplo-infer",
    "neuriplo-kserve-client",
    "neuriplo-kserve-runtime",
}

COMMON_OBSERVABILITY = {"request_id", "model", "error_code"}


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="ascii") as handle:
        return yaml.safe_load(handle)


def main() -> int:
    errors: list[str] = []
    data = load_yaml(CASES_PATH)
    if not isinstance(data, dict):
        print(f"ERROR: {CASES_PATH.relative_to(ROOT)} top level must be a mapping", file=sys.stderr)
        return 1

    cases = data.get("cases")
    if not isinstance(cases, list):
        print(f"ERROR: {CASES_PATH.relative_to(ROOT)} cases must be a list", file=sys.stderr)
        return 1

    by_id: dict[str, dict[str, Any]] = {}
    for index, case in enumerate(cases):
        where = f"cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{where}: must be an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"{where}: id must be a non-empty string")
            continue
        if case_id in by_id:
            errors.append(f"{case_id}: duplicate case id")
            continue
        by_id[case_id] = case

    missing = sorted(set(REQUIRED_CASES) - set(by_id))
    extra = sorted(set(by_id) - set(REQUIRED_CASES))
    for case_id in missing:
        errors.append(f"missing required failure case: {case_id}")
    for case_id in extra:
        errors.append(f"unknown failure case: {case_id}")

    for case_id, (code, http_status, grpc_status) in REQUIRED_CASES.items():
        case = by_id.get(case_id)
        if not case:
            continue
        if case.get("code") != code:
            errors.append(f"{case_id}: code must be {code}")
        if case.get("http_status") != http_status:
            errors.append(f"{case_id}: http_status must be {http_status}")
        if case.get("grpc_status") != grpc_status:
            errors.append(f"{case_id}: grpc_status must be {grpc_status}")
        if not isinstance(case.get("retryable"), bool):
            errors.append(f"{case_id}: retryable must be boolean")
        if case.get("owner") not in ALLOWED_OWNERS:
            errors.append(f"{case_id}: owner must be one of {sorted(ALLOWED_OWNERS)}")

        runbook = case.get("runbook")
        if not isinstance(runbook, str) or not runbook:
            errors.append(f"{case_id}: runbook is required")
        else:
            runbook_path = (ROOT / runbook).resolve()
            try:
                runbook_path.relative_to(ROOT)
            except ValueError:
                errors.append(f"{case_id}: runbook escapes repository: {runbook}")
            else:
                if not runbook_path.is_file():
                    errors.append(f"{case_id}: runbook not found: {runbook}")

        observability = case.get("observability", {})
        fields = observability.get("required_fields") if isinstance(observability, dict) else None
        if not isinstance(fields, list) or not all(isinstance(item, str) for item in fields):
            errors.append(f"{case_id}: observability.required_fields must be a list of strings")
            continue
        missing_fields = sorted(COMMON_OBSERVABILITY - set(fields))
        if missing_fields:
            errors.append(f"{case_id}: missing observability fields: {', '.join(missing_fields)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("failure-mode contract matrix ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
