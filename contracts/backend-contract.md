# Backend Contract

Owner: `neuriplo`

Consumers: `neuriplo-infer` embedded local mode, `neuriplo-kserve-runtime`, integration tests

Status: Draft

## Purpose

Define the execution boundary between embedded local application or serving
runtime code and inference backends such as ONNX Runtime, TensorRT, OpenVINO, or
future engines. `neuriplo-infer` remote KServe client mode consumes the KServe V2
runtime contract instead of this backend contract directly.

## Responsibilities

`neuriplo` owns:

- Backend capability discovery.
- Backend session creation.
- Input and output tensor binding.
- Execution lifecycle.
- Runtime compatibility checks.
- Backend-specific error normalization.

Consumers may:

- Request a backend by name or capability.
- Construct an execution session from a model artifact and configuration.
- Submit preprocessed tensors for execution.
- Receive raw backend outputs for task-level postprocessing.

Consumers must not:

- Reach into backend-specific runtime handles.
- Encode backend-specific assumptions outside capability checks.
- Bypass `neuriplo` for supported backend execution paths.

## Compatibility Rules

- Adding a backend is backward compatible.
- Adding optional capability fields is backward compatible.
- Removing a capability field is breaking.
- Changing tensor binding semantics is breaking.
- Backend-specific features should be exposed as capabilities, not ad hoc
  application checks.

## Validation Strategy

- Unit tests in `neuriplo` validate each backend adapter.
- Integration tests in this repository validate at least one task across each
  supported backend in the compatibility matrix.
- Runtime compatibility failures should be tested as first-class behavior.
