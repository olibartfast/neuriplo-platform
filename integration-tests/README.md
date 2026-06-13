# Integration Tests

Integration tests validate ecosystem behavior across repository boundaries. Unit
and component tests remain in the owning repositories.

## Scope

Good candidates:

- One task executing through one or more backends.
- Local CLI wiring from configuration to result output.
- KServe V2 request/response compatibility.
- Version matrix compatibility checks.

Out of scope:

- Model-specific unit tests.
- Backend adapter unit tests.
- Runtime implementation tests that do not cross repository boundaries.

## Test Design

Each integration test should document:

- Repositories and versions under test.
- Required model artifacts.
- Expected inputs and outputs.
- Operational assumptions such as GPU, CPU, memory, or container runtime.
## Current Tests

- [Local inference smoke](local-inference-smoke/README.md): validates local sibling
  checkouts, pinned refs, and the app-owned E2E runner dry-run path.
- [KServe runtime E2E](kserve-runtime-e2e/README.md): starts the real serving
  runtime, runs the app-layer KServe HTTP client against it, verifies rendered
  output, and checks metrics.
- [EdgeCrafter KServe runtime E2E](kserve-runtime-edgecrafter-e2e/README.md):
  exercises the EdgeCrafter `ecdet` dual-input INT64 contract across the
  `onnx_runtime`, `tensorrt`, `openvino`, and `executorch` backends, asserting the advertised
  datatypes as the regression guard for the metadata dtype-propagation fix.
  OpenVINO and ExecuTorch coverage includes in-process local inference plus KServe HTTP and gRPC.
  Transport latency evidence (HTTP JSON vs binary vs gRPC) is in
  [kserve-runtime-edgecrafter-e2e/BENCHMARK.md](kserve-runtime-edgecrafter-e2e/BENCHMARK.md).

## Validated Matrix Cases

| Task type | Model | Backend | Mode | Status |
|-----------|-------|---------|------|--------|
| `yolo26` | `yolo26s.onnx` | `onnx_runtime` | KServe runtime, localhost | passing |
| `ecdet` (EdgeCrafter detection) | `ecdet/1/model.onnx` | `onnx_runtime` | KServe runtime, localhost | passing |
| `ecdet` (EdgeCrafter detection) | `ecdet/1/model.engine` | `tensorrt` | KServe runtime, localhost | passing |
| `ecdet` (EdgeCrafter detection) | `ecdet/1/model.xml` | `openvino` | local in-process | passing |
| `ecdet` (EdgeCrafter detection) | `ecdet/1/model.xml` | `openvino` | KServe runtime HTTP/gRPC, localhost | passing |
| `ecdet` (EdgeCrafter detection) | `ecdet/1/model.pte` | `executorch` | local in-process | passing |
| `ecdet` (EdgeCrafter detection) | `ecdet/1/model.pte` | `executorch` | KServe runtime HTTP/gRPC, localhost | passing |

EdgeCrafter exercises the dual-input contract (`images` FP32 + `orig_target_sizes`
INT64 -> `labels` INT64, `boxes`/`scores` FP32) end to end. The metadata-driven
N-input plumbing was already correct; the missing piece was datatype propagation,
fixed by carrying a typed datatype through the backend metadata boundary:

- `neuriplo::LayerInfo` (`neuriplo/backends/src/InferenceMetadata.hpp`) carries a
  `TensorDataType datatype` field (default `Float32`).
- the ORT and TensorRT backends map each input/output element type to
  `TensorDataType`, throwing on unsupported types rather than silently reporting
  FP32.
- `RealNeuriploAdapter::extractDatatypes`
  (`neuriplo-kserve-runtime/src/RealNeuriploAdapter.cpp`) reports the real
  per-layer datatype as KServe V2 tokens.

Model artifacts live under `~/model_repository/ecdet/1/` (see
`kserve-runtime-edgecrafter-e2e/prepare_model_repository.py`). Export the ONNX
per `neuriplo-tasks` `export/detection/edgecrafter/README.md`; build the
TensorRT engine from it with `trtexec`; convert OpenVINO IR with `ovc`; export
ExecuTorch `.pte` with `export_ecdet_executorch.py`. TensorRT engines are version-
and GPU-specific.
