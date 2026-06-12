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

## Planned Matrix Cases

Model x backend combinations pinned for future matrix coverage. Each entry
records the task type, model artifact, backend, serving mode, and current
status. These are not yet wired into an executable runner.

| Task type | Model | Backend | Mode | Status |
|-----------|-------|---------|------|--------|
| `ecdet` (EdgeCrafter detection) | `ecdet_s.onnx` | `onnx_runtime` (ORT) | KServe runtime, localhost | **needs model artifact** |

EdgeCrafter detection status detail: the dual-input contract (`images` FP32 +
`orig_target_sizes` INT64 -> `labels` INT64, `boxes`/`scores` FP32) is now
servable over KServe. The metadata-driven N-input plumbing was already correct;
the missing piece was datatype propagation, which was fixed by carrying a typed
datatype through the backend metadata boundary:

- `neuriplo::LayerInfo` (`neuriplo/backends/src/InferenceMetadata.hpp`) now
  carries a `TensorDtype datatype` field (default `FP32`).
- the ORT backend (`neuriplo/backends/onnx-runtime/src/ORTInfer.cpp`) maps each
  ONNX input/output element type to `TensorDtype`, throwing on unsupported types
  rather than silently reporting FP32.
- `RealNeuriploAdapter::extractDatatypes`
  (`neuriplo-kserve-runtime/src/RealNeuriploAdapter.cpp`) reports the real
  per-layer datatype via the existing `tensorDtypeToKserve` mapper.

Remaining gap: this combo is not yet exercised by an executable runner because
no `ecdet_s.onnx` artifact is checked in (export per `neuriplo-tasks`
`export/detection/edgecrafter/README.md`). The all-FP32 KServe runtime E2E (YOLO)
passes after the change; the INT64 path is built and type-checked but not yet run
against a real EdgeCrafter model.
