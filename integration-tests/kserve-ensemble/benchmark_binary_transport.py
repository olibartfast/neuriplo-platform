#!/usr/bin/env python3
"""Benchmark ensembles over the HTTP binary tensor extension.

The sibling benchmark_preprocessing.py sends the encoded image as a JSON number
array. For a 98 KB JPEG that encoding dominates the measurement -- it moved the
three-way comparison by roughly 150 ms per request, more than the pipeline work
being compared. This sends the image as binary and keeps only the header as
JSON, so what is left is server-side time plus a thin transport.

Reports the client round trip. The server's own per-request timing is in its
structured logs under `infer_latency_ns`.

Interleaves the models frame by frame so drift falls on all of them equally,
and discards warmup iterations.
"""

from __future__ import annotations

import argparse
import glob
import json
import statistics
import sys
import time
import urllib.request
from pathlib import Path


def infer_once(endpoint: str, model: str, image: bytes, timeout: float) -> float:
    # Binary tensor extension: JSON header first, raw tensor bytes appended,
    # with the header length in Inference-Header-Content-Length.
    header = json.dumps(
        {
            "inputs": [
                {
                    "name": "IMAGE",
                    "datatype": "UINT8",
                    "shape": [1, len(image)],
                    "parameters": {"binary_data_size": len(image)},
                }
            ]
        }
    ).encode()
    request = urllib.request.Request(
        f"{endpoint.rstrip('/')}/v2/models/{model}/infer",
        data=header + image,
        headers={
            "Content-Type": "application/octet-stream",
            "Inference-Header-Content-Length": str(len(header)),
        },
    )
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        response.read()
    return (time.perf_counter() - start) * 1000.0


def stats(samples: list[float]) -> dict[str, float]:
    ordered = sorted(samples)
    return {
        "count": len(ordered),
        "mean_ms": round(statistics.fmean(ordered), 1),
        "median_ms": round(statistics.median(ordered), 1),
        "p95_ms": round(ordered[int(len(ordered) * 0.95) - 1], 1),
        "min_ms": round(ordered[0], 1),
        "fps": round(1000.0 / statistics.fmean(ordered), 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8080")
    parser.add_argument("--models", nargs="+", required=True,
                        help="ensemble model names to compare, in order")
    parser.add_argument("--labels", nargs="+",
                        help="display label per model (defaults to model names)")
    parser.add_argument("--frames", required=True, help="glob for encoded images")
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    labels = args.labels or args.models
    if len(labels) != len(args.models):
        print("--labels must match --models", file=sys.stderr)
        return 2

    frames = sorted(glob.glob(args.frames))
    if not frames:
        print(f"no frames matched {args.frames}", file=sys.stderr)
        return 2
    needed = args.iterations + args.warmup
    images = [Path(f).read_bytes() for f in frames[:needed]]
    while len(images) < needed:
        images += images
    images = images[:needed]

    samples: dict[str, list[float]] = {m: [] for m in args.models}
    for index, image in enumerate(images):
        for model in args.models:  # interleaved, so drift hits every model
            elapsed = infer_once(args.endpoint, model, image, args.timeout)
            if index >= args.warmup:
                samples[model].append(elapsed)

    report = {
        "endpoint": args.endpoint,
        "transport": "http-binary-tensor-extension",
        "frames": len(frames),
        "iterations": args.iterations,
        "warmup": args.warmup,
        "results": {
            label: stats(samples[model]) for label, model in zip(labels, args.models)
        },
    }

    baseline_label = labels[0]
    baseline = report["results"][baseline_label]["mean_ms"]
    for label in labels[1:]:
        mean = report["results"][label]["mean_ms"]
        report["results"][label]["speedup_vs_" + baseline_label.replace(" ", "_")] = (
            round(baseline / mean, 2) if mean else None
        )

    print(json.dumps(report, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
