#!/usr/bin/env python3
"""Prepare the local Triton-style model repository layout for EdgeCrafter ecdet.

All integration-test backends read artifacts from a single version directory:

  ${NEURIPLO_MODEL_REPOSITORY}/ecdet/1/
    model.onnx      # onnx_runtime (and OpenVINO import source)
    model.engine    # tensorrt
    model.xml       # openvino IR (optional; generated from model.onnx)
    model.bin       # openvino IR weights

Run once before the e2e runners when artifacts are missing.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPOS_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPO = Path(os.environ.get("NEURIPLO_MODEL_REPOSITORY", Path.home() / "model_repository"))
ECDET_DIR = DEFAULT_REPO / "ecdet" / "1"

ONNX_SOURCES = [
    DEFAULT_REPO / "ecdet_s_onnx" / "1" / "model.onnx",
    REPOS_ROOT / "edgecrafter-cpp-inference" / "models" / "ecdet_s.onnx",
    REPOS_ROOT / "neuriplo-infer" / "models" / "e2e" / "ecdet_s.onnx",
]

TRT_SOURCES = [
    REPOS_ROOT / "edgecrafter-cpp-inference" / "models" / "ecdet_s.trt.engine",
]


def first_existing(candidates: list[Path]) -> Path | None:
    for path in candidates:
        if path.is_file():
            return path
    return None


def copy_if_missing(source: Path, dest: Path, label: str) -> None:
    if dest.is_file():
        print(f"ok: {label} already present at {dest}")
        return
    if not source.is_file():
        raise RuntimeError(f"missing source for {label}: {source}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    print(f"copied {label}: {source} -> {dest}")


def convert_openvino_ir(onnx_path: Path, xml_path: Path) -> None:
    if xml_path.is_file() and xml_path.with_suffix(".bin").is_file():
        print(f"ok: OpenVINO IR already present at {xml_path}")
        return
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    output_stem = xml_path.with_suffix("")
    cmd = [
        "ovc",
        str(onnx_path),
        "--output_model",
        str(output_stem),
        "--input",
        "images[1,3,640,640]",
        "--input",
        "orig_target_sizes[1,2]",
    ]
    print("running:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "ovc failed (install openvino-dev or set PATH):\n"
            + (result.stdout or "")
            + (result.stderr or "")
        )
    if not xml_path.is_file():
        raise RuntimeError(f"ovc did not produce {xml_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-repository",
        type=Path,
        default=DEFAULT_REPO,
        help="Root model repository directory (default: $NEURIPLO_MODEL_REPOSITORY or ~/model_repository)",
    )
    parser.add_argument("--skip-openvino", action="store_true", help="Do not run ovc IR conversion")
    args = parser.parse_args()

    global ECDET_DIR
    ECDET_DIR = args.model_repository / "ecdet" / "1"

    onnx_dest = ECDET_DIR / "model.onnx"
    if not onnx_dest.is_file():
        source = first_existing(ONNX_SOURCES)
        if source is None:
            raise RuntimeError(
                "no ecdet ONNX found; export per neuriplo-tasks/export/detection/edgecrafter/README.md "
                "or place model.onnx under ~/model_repository/ecdet/1/"
            )
        copy_if_missing(source, onnx_dest, "ONNX")

    trt_dest = ECDET_DIR / "model.engine"
    if not trt_dest.is_file():
        source = first_existing(TRT_SOURCES)
        if source is None:
            print(f"warn: no TensorRT engine source found; {trt_dest} still missing")
        else:
            copy_if_missing(source, trt_dest, "TensorRT engine")

    if not args.skip_openvino:
        convert_openvino_ir(onnx_dest, ECDET_DIR / "model.xml")

    print(f"model repository ready under {ECDET_DIR}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
