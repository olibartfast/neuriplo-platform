#!/usr/bin/env python3
"""Real local KServe runtime E2E for EdgeCrafter detection across backends.

Mirrors the YOLO ``kserve-runtime-e2e`` runner but exercises the EdgeCrafter
``ecdet`` dual-input contract (``images`` FP32 + ``orig_target_sizes`` INT64 ->
``labels`` INT64, ``boxes``/``scores`` FP32). It also asserts the advertised
datatypes, which is the regression guard for the metadata dtype-propagation fix:
without it the INT64 tensors were reported (and served) as FP32.

Select the serving backend with ``--backend`` (``onnx_runtime`` or
``tensorrt``); the matching runtime binary and model artifact are chosen by
default and can be overridden.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPOS_ROOT = ROOT.parent

# Per-backend defaults: (runtime build dir, model artifact candidates).
BACKEND_DEFAULTS = {
    "onnx_runtime": {
        "build": "real-onnx",
        "models": [
            REPOS_ROOT / "neuriplo-infer" / "models" / "e2e" / "ecdet_s.onnx",
            REPOS_ROOT / "edgecrafter-cpp-inference" / "models" / "ecdet_s.onnx",
        ],
    },
    "tensorrt": {
        "build": "real-trt",
        "models": [
            REPOS_ROOT / "edgecrafter-cpp-inference" / "models" / "ecdet_s.trt.engine",
        ],
    },
}


def processed_image_name(model: str, backend: str) -> str:
    # Mirror neuriplo-infer CLICommands.cpp: non-alphanumeric characters in the
    # model/backend tags are replaced with '-'. The app reports the "kserve"
    # backend for all remote inference regardless of the runtime's backend.
    def sanitize(value: str) -> str:
        return "".join(c if c.isalnum() else "-" for c in value)

    return f"processed_{sanitize(model)}_{sanitize(backend)}.png"


def http_json(url: str, timeout: float = 5.0) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def wait_until_ready(base_url: str, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error = "runtime did not answer"
    while time.monotonic() < deadline:
        try:
            live = http_json(f"{base_url}/v2/health/live", timeout=2.0)
            ready = http_json(f"{base_url}/v2/health/ready", timeout=2.0)
            if live.get("live") is True and ready.get("ready") is True:
                return
            last_error = f"live={live!r} ready={ready!r}"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        time.sleep(0.5)
    raise RuntimeError(f"runtime did not become ready before timeout: {last_error}")


def require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"missing {label}: {path}")


def default_model(backend: str) -> Path:
    candidates = BACKEND_DEFAULTS[backend]["models"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def default_runtime_bin(backend: str) -> Path:
    build = BACKEND_DEFAULTS[backend]["build"]
    return REPOS_ROOT / "neuriplo-kserve-runtime" / "build" / build / "neuriplo-kserve-runtime"


def find_infer_binary(neuriplo_infer: Path, build_dir: Path | None, explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    candidates: list[Path] = []
    if build_dir is not None:
        candidates.append(build_dir / "app" / "neuriplo-infer")
    candidates.extend([
        neuriplo_infer / "build-kserve-codex" / "app" / "neuriplo-infer",
        neuriplo_infer / "build-kserve" / "app" / "neuriplo-infer",
        neuriplo_infer / "build" / "app" / "neuriplo-infer",
    ])
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise RuntimeError("missing neuriplo-infer app binary; checked: " + ", ".join(str(p) for p in candidates))


def runtime_env(backend: str, tensorrt_lib_dirs: list[Path]) -> dict[str, str]:
    env = dict(os.environ)
    if backend == "tensorrt":
        existing = env.get("LD_LIBRARY_PATH", "")
        extra = os.pathsep.join(str(d) for d in tensorrt_lib_dirs if d.is_dir())
        env["LD_LIBRARY_PATH"] = os.pathsep.join(p for p in (extra, existing) if p)
    return env


def run_checked(cmd: list[str], cwd: Path, timeout: float) -> str:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError("command failed (exit %d): %s\n%s" % (result.returncode, " ".join(cmd), result.stdout))
    return result.stdout


def metadata_datatypes(metadata: dict[str, Any]) -> dict[str, str]:
    types: dict[str, str] = {}
    for item in metadata.get("inputs", []) + metadata.get("outputs", []):
        types[item.get("name")] = item.get("datatype")
    return types


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=sorted(BACKEND_DEFAULTS), default="onnx_runtime")
    parser.add_argument("--port", type=int, default=19094)
    parser.add_argument("--model-name", default="ecdet")
    parser.add_argument("--task-type", default="ecdet")
    parser.add_argument("--runtime-bin", type=Path, default=None)
    parser.add_argument("--infer-build-dir", type=Path, default=None)
    parser.add_argument("--infer-bin", type=Path, default=None)
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--source", type=Path, default=REPOS_ROOT / "neuriplo-infer" / "data" / "dog.jpg")
    parser.add_argument("--labels", type=Path, default=REPOS_ROOT / "neuriplo-infer" / "labels" / "coco.names")
    parser.add_argument(
        "--tensorrt-lib-dir",
        type=Path,
        action="append",
        default=None,
        help="TensorRT lib directory added to LD_LIBRARY_PATH for the tensorrt backend (repeatable).",
    )
    parser.add_argument("--startup-timeout", type=float, default=120.0)
    parser.add_argument("--infer-timeout", type=float, default=180.0)
    args = parser.parse_args()

    neuriplo_infer = REPOS_ROOT / "neuriplo-infer"
    runtime_repo = REPOS_ROOT / "neuriplo-kserve-runtime"
    runtime_bin = args.runtime_bin if args.runtime_bin is not None else default_runtime_bin(args.backend)
    model = args.model if args.model is not None else default_model(args.backend)
    infer_bin = find_infer_binary(neuriplo_infer, args.infer_build_dir, args.infer_bin)
    output_image = neuriplo_infer / "data" / "output" / processed_image_name(args.task_type, "kserve")
    base_url = f"http://127.0.0.1:{args.port}"

    tensorrt_lib_dirs = args.tensorrt_lib_dir or [
        Path("/home/oli/dependencies/TensorRT-10.13.3.9/targets/x86_64-linux-gnu/lib"),
        Path("/home/oli/dependencies/TensorRT-10.13.3.9/lib"),
    ]

    require_file(runtime_bin, f"neuriplo-kserve-runtime ({args.backend}) binary")
    require_file(infer_bin, "neuriplo-infer app binary")
    require_file(model, f"EdgeCrafter {args.backend} model artifact")
    require_file(args.source, "input image")
    require_file(args.labels, "labels file")

    log_path = Path(os.environ.get("TMPDIR", "/tmp")) / f"neuriplo-ecdet-e2e-{args.backend}-{args.port}.log"
    log_handle = log_path.open("w", encoding="utf-8")
    process: subprocess.Popen[str] | None = None
    start_ns = time.time_ns()

    try:
        runtime_cmd = [
            str(runtime_bin),
            "--model-name", args.model_name,
            "--model-path", str(model),
            "--backend", args.backend,
            "--port", str(args.port),
            "--instances", "1",
        ]
        process = subprocess.Popen(
            runtime_cmd,
            cwd=runtime_repo,
            text=True,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            env=runtime_env(args.backend, tensorrt_lib_dirs),
        )
        wait_until_ready(base_url, args.startup_timeout)

        metadata = http_json(f"{base_url}/v2/models/{args.model_name}", timeout=5.0)
        expected_platform = "neuriplo_" + args.backend
        if metadata.get("platform") != expected_platform:
            raise RuntimeError(f"unexpected runtime platform metadata: {metadata!r}")

        input_names = {item.get("name") for item in metadata.get("inputs", [])}
        output_names = {item.get("name") for item in metadata.get("outputs", [])}
        if not {"images", "orig_target_sizes"} <= input_names:
            raise RuntimeError(f"metadata missing expected EdgeCrafter inputs: {metadata!r}")
        if not {"labels", "boxes", "scores"} <= output_names:
            raise RuntimeError(f"metadata missing expected EdgeCrafter outputs: {metadata!r}")

        # Regression guard for the dtype-propagation fix: the dual-input INT64
        # contract must be advertised with real datatypes, not collapsed to FP32.
        datatypes = metadata_datatypes(metadata)
        expected_datatypes = {
            "images": "FP32",
            "orig_target_sizes": "INT64",
            "labels": "INT64",
            "boxes": "FP32",
            "scores": "FP32",
        }
        for name, expected in expected_datatypes.items():
            if datatypes.get(name) != expected:
                raise RuntimeError(
                    f"datatype mismatch for {name!r}: expected {expected}, got {datatypes.get(name)!r} "
                    f"(metadata: {metadata!r})"
                )

        infer_cmd = [
            str(infer_bin),
            f"--type={args.task_type}",
            f"--source={args.source}",
            f"--labels={args.labels}",
            f"--kserve_endpoint={base_url}",
            f"--kserve_model_name={args.model_name}",
            "--kserve_transport=http",
            "--min_confidence=0.25",
        ]
        app_output = run_checked(infer_cmd, cwd=neuriplo_infer, timeout=args.infer_timeout)

        require_file(output_image, "processed output image")
        stat = output_image.stat()
        if stat.st_size <= 0 or stat.st_mtime_ns < start_ns:
            raise RuntimeError(f"output image was not refreshed: {output_image} size={stat.st_size}")

        metrics = urllib.request.urlopen(f"{base_url}/metrics", timeout=5.0).read().decode("utf-8")
        expected_metric = f'neuriplo_http_infer_requests_success_total{{model="{args.model_name}",version="1"}} 1'
        if expected_metric not in metrics:
            raise RuntimeError(f"missing success metric: {expected_metric}")
        failure_metric = f'neuriplo_http_infer_requests_failure_total{{model="{args.model_name}",version="1"}} 0'
        if failure_metric not in metrics:
            raise RuntimeError(f"failure metric is not zero: {failure_metric}")

        print(f"edgecrafter kserve runtime e2e ok ({args.backend})")
        print(f"runtime log: {log_path}")
        print(f"model: {model}")
        print(f"output image: {output_image} ({stat.st_size} bytes)")
        if app_output.strip():
            print("app output tail:")
            print("\n".join(app_output.strip().splitlines()[-8:]))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print(f"runtime log: {log_path}", file=sys.stderr)
        return 1
    finally:
        if process is not None and process.poll() is None:
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5.0)
        log_handle.close()


if __name__ == "__main__":
    raise SystemExit(main())
