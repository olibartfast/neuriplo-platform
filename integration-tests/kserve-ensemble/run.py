#!/usr/bin/env python3
"""Cross-repository check that server-side ensembles agree with client-side preprocessing.

The premise of an ensemble is that moving preprocessing (and optionally
postprocessing) onto the server does not change the answer. This test is the
only place that can prove it, because it is the only place that runs both paths
against the same image with the same model.

It is deliberately an agreement test rather than a golden-output test. The
defects this class of feature actually produces -- detections ranked before
instead of after the score sort, an output cap applied in the wrong order, a
channel stride hardcoded to one anchor count, a truncated offset array on an
empty frame -- all survive a self-consistent golden file and all fail an
agreement check against the CPU path.

Until the runtime ships the pipeline model kind (ADR 0011), this exits 0 with a
clear "not available" report so it can sit in CI without failing. It never
reports agreement it did not observe.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

# contracts/ensemble-contract.md
ENSEMBLE_PLATFORM = "ensemble"
ENSEMBLE_INPUT = ("IMAGE", "UINT8")
DETECTION_ENVELOPE = {
    "NUM_DETECTIONS": "INT32",
    "BOXES": "INT32",
    "SCORES": "FP32",
    "CLASSES": "INT32",
}
MASK_ENVELOPE = {"MASK_OFFSETS": "INT64", "MASK_DATA": "UINT8"}
POLYGON_ENVELOPE = {
    "INSTANCE_RING_OFFSETS": "INT64",
    "RING_POINT_OFFSETS": "INT64",
    "POLYGON_POINTS": "INT32",
}


def http_json(url: str, timeout: float = 5.0) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def report(status: str, detail: str) -> None:
    print(f"[kserve-ensemble] {status}: {detail}")


def fetch_metadata(base_url: str, model: str) -> dict[str, Any] | None:
    try:
        return http_json(f"{base_url}/v2/models/{model}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        report("unavailable", f"could not read metadata for {model}: {exc}")
        return None


def check_ensemble_metadata(metadata: dict[str, Any]) -> list[str]:
    """Validates the parts of contracts/ensemble-contract.md visible in metadata."""
    problems: list[str] = []

    platform = metadata.get("platform", "")
    if platform != ENSEMBLE_PLATFORM:
        problems.append(f"platform is {platform!r}, expected {ENSEMBLE_PLATFORM!r}")

    inputs = metadata.get("inputs", [])
    if len(inputs) != 1:
        problems.append(f"expected exactly one input, got {len(inputs)}")
    else:
        name = inputs[0].get("name")
        datatype = inputs[0].get("datatype")
        if (name, datatype) != ENSEMBLE_INPUT:
            problems.append(
                f"input is {name}/{datatype}, expected {ENSEMBLE_INPUT[0]}/{ENSEMBLE_INPUT[1]}"
            )

    outputs = {item.get("name"): item.get("datatype") for item in metadata.get("outputs", [])}
    if set(DETECTION_ENVELOPE).issubset(outputs):
        expected = dict(DETECTION_ENVELOPE)
        if set(MASK_ENVELOPE).issubset(outputs):
            expected.update(MASK_ENVELOPE)
        elif set(POLYGON_ENVELOPE).issubset(outputs):
            expected.update(POLYGON_ENVELOPE)
        for name, datatype in expected.items():
            if outputs.get(name) != datatype:
                problems.append(
                    f"output {name} is {outputs.get(name)!r}, expected {datatype!r}"
                )

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--endpoint",
        default="http://127.0.0.1:8080",
        help="KServe V2 endpoint serving the ensemble",
    )
    parser.add_argument(
        "--ensemble-model",
        default="yolo_ensemble",
        help="ensemble model name on the endpoint",
    )
    parser.add_argument(
        "--task-model",
        default="yolo",
        help="inner model whose metadata drives task construction",
    )
    args = parser.parse_args()

    base_url = args.endpoint.rstrip("/")

    metadata = fetch_metadata(base_url, args.ensemble_model)
    if metadata is None:
        report(
            "skipped",
            "no ensemble endpoint reachable; the runtime pipeline model kind is "
            "not implemented yet (ADR 0011)",
        )
        return 0

    problems = check_ensemble_metadata(metadata)
    if problems:
        for problem in problems:
            report("FAIL", problem)
        return 1
    report("ok", f"{args.ensemble_model} metadata conforms to the ensemble contract")

    # The agreement leg needs the neuriplo-infer encoded-image path, which is
    # not implemented yet. Refusing to claim agreement is the point.
    report(
        "pending",
        "detection agreement between the ensemble path and the client-preprocessed "
        f"path against --task-model={args.task_model} is not yet implemented; "
        "it lands with the neuriplo-infer adapter",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
