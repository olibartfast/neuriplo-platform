# Ownership Model

This document defines responsibility boundaries across the vision inference
ecosystem. When a change spans multiple repositories, use this model to decide
where the durable implementation should live.

## Boundary Rules

### Domain and Task Behavior

Belongs in `vision-core`.

Examples:

- Input and output task contracts
- Preprocessing and postprocessing pipelines
- Result types
- Model-family task adapters
- Task registry and factory behavior

### Backend Execution

Belongs in `neuriplo`.

Examples:

- Backend interfaces
- ONNX Runtime, TensorRT, OpenVINO, or future backend adapters
- Execution session abstractions
- Backend capability reporting
- Runtime compatibility behavior

### Local Application Flow

Belongs in `vision-inference`.

Examples:

- CLI commands
- Config loading and validation
- Wiring task logic to backend execution
- Visualization and local output formatting
- End-to-end local workflows

### Serving Runtime

Belongs in `neuriplo-kserve-runtime`.

Examples:

- KServe V2 protocol handling
- Request admission
- Scheduling and dynamic batching
- Model lifecycle
- Health, readiness, metrics, and operational endpoints

### Architecture Control Plane

Belongs in `neuriplo-platform`.

Examples:

- ADRs
- Cross-repository contract definitions
- Version compatibility matrix
- Integration test plans
- End-to-end examples
- Architecture diagrams and operating guidance

## Decision Heuristic

If a change is about what a task means, put it in `vision-core`.

If a change is about how inference runs on a backend, put it in `neuriplo`.

If a change is about how a user runs local inference, put it in
`vision-inference`.

If a change is about serving requests in production, put it in
`neuriplo-kserve-runtime`.

If a change is about how repositories coordinate, document and test that
coordination in `neuriplo-platform`.
