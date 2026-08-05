#!/usr/bin/env python3
"""Compare two ensembles that differ only in where preprocessing runs.

The claim a GPU preprocessing path has to earn is that relocating decode,
resize, and normalize does not change the answer. This measures that directly:
both ensembles wrap the *same* inference model, so preprocessing is the only
variable, and any disagreement is attributable to it.

Matching is symmetric and one-to-one. An earlier ad-hoc version of this check
reported only how many CPU detections the GPU path matched, which hides the
opposite error: a preprocessing path that invents detections scores just as well
as one that reproduces them. Both directions are reported, and each detection
can be claimed once.

Output is JSON so results can be diffed across runs and pinned as a baseline,
rather than living as prose in a status document.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

Detection = tuple[int, float, tuple[float, float, float, float]]


def infer(endpoint: str, model: str, image: bytes, timeout: float) -> list[Detection]:
    body = json.dumps(
        {
            "inputs": [
                {
                    "name": "IMAGE",
                    "datatype": "UINT8",
                    "shape": [1, len(image)],
                    "data": list(image),
                }
            ]
        }
    ).encode()
    request = urllib.request.Request(
        f"{endpoint.rstrip('/')}/v2/models/{model}/infer",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read())

    outputs = {item["name"]: item["data"] for item in payload["outputs"]}
    count = int(outputs["NUM_DETECTIONS"][0])
    boxes, scores, classes = outputs["BOXES"], outputs["SCORES"], outputs["CLASSES"]
    return [
        (int(classes[i]), float(scores[i]), tuple(boxes[i * 4 : i * 4 + 4]))
        for i in range(count)
    ]


def iou(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    overlap = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    if overlap <= 0:
        return 0.0
    return overlap / (aw * ah + bw * bh - overlap)


def match(
    left: list[Detection], right: list[Detection], threshold: float
) -> tuple[int, list[Detection], list[Detection]]:
    """Greedy one-to-one match by descending IoU within the same class."""
    pairs = sorted(
        (
            (iou(lb, rb), i, j)
            for i, (lc, _, lb) in enumerate(left)
            for j, (rc, _, rb) in enumerate(right)
            if lc == rc
        ),
        reverse=True,
    )
    used_left: set[int] = set()
    used_right: set[int] = set()
    matched = 0
    for score, i, j in pairs:
        if score < threshold or i in used_left or j in used_right:
            continue
        used_left.add(i)
        used_right.add(j)
        matched += 1
    return (
        matched,
        [d for i, d in enumerate(left) if i not in used_left],
        [d for j, d in enumerate(right) if j not in used_right],
    )


def summarize(unmatched: list[Detection], high_confidence: float) -> dict[str, Any]:
    scores = sorted(score for _, score, _ in unmatched)
    return {
        "count": len(unmatched),
        "high_confidence_count": sum(1 for s in scores if s >= high_confidence),
        "score_min": round(scores[0], 4) if scores else None,
        "score_max": round(scores[-1], 4) if scores else None,
        "high_confidence_examples": [
            {"class": c, "score": round(s, 4), "box": [round(v, 1) for v in b]}
            for c, s, b in sorted(unmatched, key=lambda d: -d[1])
            if s >= high_confidence
        ][:10],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8080")
    parser.add_argument("--reference-model", default="yolo26seg_cpu",
                        help="ensemble whose preprocessing is the reference")
    parser.add_argument("--candidate-model", default="yolo26seg_dali",
                        help="ensemble under test")
    parser.add_argument("--frames", required=True,
                        help="glob for encoded images, e.g. 'frames/*.jpg'")
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--iou", type=float, default=0.5)
    parser.add_argument("--high-confidence", type=float, default=0.5)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--report", type=Path, help="write JSON results here")
    parser.add_argument("--min-match-rate", type=float, default=0.0,
                        help="exit 1 when either direction falls below this rate")
    args = parser.parse_args()

    frames = sorted(glob.glob(args.frames))[:: args.stride]
    if args.limit:
        frames = frames[: args.limit]
    if not frames:
        print(f"no frames matched {args.frames}", file=sys.stderr)
        return 2

    totals = {"reference": 0, "candidate": 0, "matched": 0}
    unmatched_reference: list[Detection] = []
    unmatched_candidate: list[Detection] = []
    errors = 0

    for frame in frames:
        image = Path(frame).read_bytes()
        try:
            reference = infer(args.endpoint, args.reference_model, image, args.timeout)
            candidate = infer(args.endpoint, args.candidate_model, image, args.timeout)
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
            errors += 1
            print(f"[warn] {Path(frame).name}: {exc}", file=sys.stderr)
            continue

        matched, missed, extra = match(reference, candidate, args.iou)
        totals["reference"] += len(reference)
        totals["candidate"] += len(candidate)
        totals["matched"] += matched
        unmatched_reference.extend(missed)
        unmatched_candidate.extend(extra)

    def rate(matched: int, total: int) -> float:
        return round(matched / total, 4) if total else 0.0

    report = {
        "endpoint": args.endpoint,
        "reference_model": args.reference_model,
        "candidate_model": args.candidate_model,
        "frames": len(frames),
        "frames_failed": errors,
        "iou_threshold": args.iou,
        "high_confidence_threshold": args.high_confidence,
        "detections": totals,
        # Both directions: recall misses real detections, precision counts
        # invented ones. A single number hides one of the two failure modes.
        "reference_matched_rate": rate(totals["matched"], totals["reference"]),
        "candidate_matched_rate": rate(totals["matched"], totals["candidate"]),
        "unmatched_reference": summarize(unmatched_reference, args.high_confidence),
        "unmatched_candidate": summarize(unmatched_candidate, args.high_confidence),
    }

    print(json.dumps(report, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")

    if args.min_match_rate:
        worst = min(report["reference_matched_rate"], report["candidate_matched_rate"])
        if worst < args.min_match_rate:
            print(
                f"FAIL: match rate {worst} below required {args.min_match_rate}",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
