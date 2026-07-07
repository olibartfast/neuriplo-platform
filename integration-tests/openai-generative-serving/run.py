#!/usr/bin/env python3
"""Validate the OpenAI-compatible generative serving smoke metadata."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised only on missing dep
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc

ROOT = Path(__file__).resolve().parents[2]
SCENARIO = Path(__file__).resolve().parent
CONTRACT = SCENARIO / "contract.yaml"


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="ascii") as handle:
        return yaml.safe_load(handle)


def main() -> int:
    errors: list[str] = []
    data = load_yaml(CONTRACT)
    if not isinstance(data, dict):
        print(f"ERROR: {CONTRACT.relative_to(ROOT)} top level must be a mapping", file=sys.stderr)
        return 1

    if data.get("track") != "generative":
        errors.append("track must be generative")
    if data.get("protocol") != "openai-compatible":
        errors.append("protocol must be openai-compatible")
    if data.get("endpoint") != "/v1/chat/completions":
        errors.append("endpoint must be /v1/chat/completions")

    example = data.get("example")
    if not isinstance(example, str) or not example:
        errors.append("example is required")
    else:
        example_path = (ROOT / example).resolve()
        try:
            example_path.relative_to(ROOT)
        except ValueError:
            errors.append(f"example escapes repository: {example}")
        else:
            if not example_path.is_file():
                errors.append(f"example not found: {example}")
            else:
                text = example_path.read_text(encoding="ascii")
                required_text = [
                    "/v1/chat/completions",
                    "llama-server",
                    "No V2 tensor shapes",
                    "choices[0].message.content",
                    "choices[0].delta.content",
                ]
                for needle in required_text:
                    if needle not in text:
                        errors.append(f"{example}: missing required text: {needle}")

    dependency = data.get("serving_dependency")
    if not isinstance(dependency, dict):
        errors.append("serving_dependency must be a mapping")
    else:
        if dependency.get("version_matrix_member") is not False:
            errors.append("serving_dependency.version_matrix_member must be false")

    fields = data.get("required_response_fields", {})
    if not isinstance(fields, dict):
        errors.append("required_response_fields must be a mapping")
    else:
        if "choices[0].message.content" not in fields.get("non_streaming", []):
            errors.append("non_streaming response must require choices[0].message.content")
        if "choices[0].delta.content" not in fields.get("streaming", []):
            errors.append("streaming response must require choices[0].delta.content")

    forbidden = set(data.get("forbidden_protocols", []))
    for item in ("kserve-v2-tensor", "float-cast-bytes"):
        if item not in forbidden:
            errors.append(f"forbidden_protocols missing {item}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("openai generative serving smoke metadata ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
