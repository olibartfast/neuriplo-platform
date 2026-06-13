# EdgeCrafter KServe Runtime E2E

Validation status: Real local E2E (onnx_runtime and tensorrt backends)

Version set: sibling branch set with local built binaries and model artifacts.

Owning repos:

- `neuriplo-platform`: cross-repository E2E orchestration and release evidence.
- `neuriplo-kserve-runtime`: KServe V2 serving runtime process.
- `neuriplo`: backend abstraction and ONNX Runtime / TensorRT execution.
- `neuriplo-infer`: app-layer KServe V2 client binary.
- `neuriplo-tasks`: EdgeCrafter (`ecdet`) preprocessing and postprocessing.

## Purpose

Exercise the EdgeCrafter detection dual-input contract through the real serving
path, across backends:

```text
images            FP32  [1,3,640,640]
orig_target_sizes INT64 [1,2]            -> labels INT64 [1,300]
                                            boxes  FP32  [1,300,4]
                                            scores FP32  [1,300]
```

This is the regression coverage for the metadata dtype-propagation fix: the test
asserts the advertised datatypes (`orig_target_sizes`/`labels` must be `INT64`,
not `FP32`). Before the fix the backend metadata hardcoded `FP32`, so the INT64
input was rejected by the runtime element-count check and the INT64 output
decoded as garbage. Both the ONNX Runtime and TensorRT backends are validated.

## Required Local Artifacts

- runtime binaries (build per backend):
  - `../neuriplo-kserve-runtime/build/real-onnx/neuriplo-kserve-runtime`
  - `../neuriplo-kserve-runtime/build/real-trt/neuriplo-kserve-runtime`
- app binary: `../neuriplo-infer/build-kserve-codex/app/neuriplo-infer`
- EdgeCrafter model artifacts:
  - onnx_runtime: `ecdet_s.onnx` (e.g. `../edgecrafter-cpp-inference/models/ecdet_s.onnx`)
  - tensorrt: `ecdet_s.trt.engine` built with the same TensorRT version the
    runtime links (engines are version-locked)
- `../neuriplo-infer/data/dog.jpg` and `../neuriplo-infer/labels/coco.names`

Export the ONNX model per `neuriplo-tasks/export/detection/edgecrafter/README.md`
and build the TensorRT engine from it with `trtexec`.

Latency measurements (local in-process TRT vs KServe HTTP/gRPC, including the
HTTP binary-tensor fix) are recorded in [BENCHMARK.md](BENCHMARK.md).

## Usage

From `neuriplo-platform`:

```bash
# ONNX Runtime backend (HTTP transport)
integration-tests/kserve-runtime-edgecrafter-e2e/run.py --backend onnx_runtime

# TensorRT backend (HTTP transport)
integration-tests/kserve-runtime-edgecrafter-e2e/run.py --backend tensorrt

# TensorRT backend over gRPC (needs a runtime built with gRPC support)
integration-tests/kserve-runtime-edgecrafter-e2e/run.py --backend tensorrt --transport grpc
```

Select the client transport with `--transport {http,grpc}` (default `http`). The
`grpc` transport requires the runtime binary to be built with
`-DNEURIPLO_RUNTIME_ENABLE_GRPC=ON`; the runtime then serves gRPC on
`--grpc-port` (default `--port + 1`) alongside HTTP. The HTTP E2E path enables
the KServe binary tensor extension for inference requests so large image tensors
travel as raw bytes instead of JSON number arrays; gRPC still uses protobuf raw
tensor contents by default.

The `tensorrt` backend adds the TensorRT library directory to `LD_LIBRARY_PATH`
for the runtime process; override the default with `--tensorrt-lib-dir` (it is
repeatable). Override model and binary paths with `--model`, `--runtime-bin`,
and `--infer-build-dir` when using non-default locations.

## What It Checks

- runtime starts with the requested backend; `/v2/health/{live,ready}` are true
- `/v2/models/ecdet` reports `neuriplo_<backend>`, inputs `images` +
  `orig_target_sizes`, outputs `labels` / `boxes` / `scores`
- advertised datatypes match the contract (`orig_target_sizes` and `labels` are
  `INT64`; `images`, `boxes`, `scores` are `FP32`) - the dtype regression guard
- the app-layer executable runs a real KServe inference request over the
  selected transport (HTTP or gRPC)
- `../neuriplo-infer/data/output/processed_ecdet_kserve.png` is refreshed and
  non-empty
- Prometheus metrics confirm one successful request and zero failures: the HTTP
  per-transport counters for `--transport http`, and the transport-agnostic
  `neuriplo_scheduler_requests_{accepted,rejected,timed_out}_total` for
  `--transport grpc` (the gRPC server has no per-transport counter)

## Notes

- The rendered image is named `processed_<model>_<backend>.png` by the app,
  where backend is always `kserve` for remote inference (the client does not
  observe the runtime's compute backend), so both backends write
  `processed_ecdet_kserve.png`.
- TensorRT engines are TensorRT-version and GPU specific; a runtime built
  against a different TensorRT version will fail to deserialize the engine.
