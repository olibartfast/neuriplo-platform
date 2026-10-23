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

- [Failure mode contract](failure-modes/README.md): validates the
  platform-owned failure-mode matrix, error codes, retry policy, owner
  assignment, transport statuses, observability fields, and runbook links.
- [OpenAI-compatible generative serving](openai-generative-serving/README.md):
  validates the ADR 0006 generative-track metadata for `/v1/chat/completions`
  and keeps the path separate from KServe V2 tensor serving.
- [KServe ensemble agreement](kserve-ensemble/README.md): checks that a
  server-side ensemble reports the contracted encoded-image surface, and (once
  the runtime and adapter land) that it produces the same detections as the
  client-preprocessed path for the same image.

App-surface suites (local inference smoke, YOLO / EdgeCrafter KServe E2E,
RF-DETR pose local-vs-KServe) moved to
`neuriplo-infer/integration-tests/` per ADR 0003 -- executable runners live in
the owning repo. Task x backend evidence is tracked in
[neuriplo-infer `docs/BackendCoverage.md`](https://github.com/olibartfast/neuriplo-infer/blob/develop/docs/BackendCoverage.md).

## Validated Matrix Cases

The YOLO / EdgeCrafter backend matrix now lives with the tests in
[neuriplo-infer `integration-tests/`](https://github.com/olibartfast/neuriplo-infer/tree/develop/integration-tests);
`ecdet` converted to TFLite remains intentionally excluded (ONNX-to-TFLite
conversion fidelity is known bad -- see the `KNOWN-BAD` cell in
`docs/BackendCoverage.md`).

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

Model artifacts live under `~/model_repository/ecdet_s_<backend>/1/` (see
`neuriplo-infer/integration-tests/kserve-runtime-edgecrafter-e2e/prepare_model_repository.py`). Export the ONNX
per `neuriplo-tasks` `export/detection/edgecrafter/README.md`; build the
TensorRT engine from it with `trtexec`; convert OpenVINO IR with `ovc`; export
ExecuTorch `.pte` with `export_ecdet_executorch.py`. TensorRT engines are version-
and GPU-specific.
