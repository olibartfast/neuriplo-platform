# Ownership Model

This document defines responsibility boundaries across the neuriplo inference
ecosystem. When a change spans multiple repositories, use this model to decide
where the durable implementation should live.

## Boundary Rules

### Domain and Task Behavior

Belongs in `neuriplo-tasks`.

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

Belongs in `neuriplo-infer`.

Examples:

- CLI commands
- Config loading and validation
- Wiring task logic to backend execution in embedded local mode
- KServe V2 client configuration in remote client/server mode
- Visualization and local output formatting
- End-to-end local and remote workflows

### KServe Protocol Client

Belongs in `neuriplo-kserve-client`.

Examples:

- KServe V2 / Open Inference Protocol client (HTTP and gRPC transports)
- Wire encode/decode over raw little-endian tensor bytes
- Client-side health/readiness probes and model repository calls (index/load/unload)
- Transport reliability: retry/backoff, keep-alive, TLS/mTLS, auth
- Anything reusable by a KServe client that must stay free of inference-backend code

### Serving Runtime

Belongs in `neuriplo-kserve-runtime`.

Examples:

- KServe V2 server protocol handling
- Request admission
- Scheduling and dynamic batching
- Model lifecycle
- Server-side wiring from KServe requests to `neuriplo-tasks` and `neuriplo`
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

If a change is about what a task means, put it in `neuriplo-tasks`.

If a change is about how inference runs on a backend, put it in `neuriplo`.

If a change is about how a user runs embedded local inference or calls a remote
KServe endpoint, put it in `neuriplo-infer`.

If a change is about how the KServe V2 wire protocol is spoken on the client side
(transports, encode/decode, retries, TLS) and must not depend on an inference
backend, put it in `neuriplo-kserve-client`.

If a change is about serving KServe requests in production or mapping those
requests to Neuriplo task/backend execution, put it in `neuriplo-kserve-runtime`.

If a change is about how repositories coordinate, document and test that
coordination in `neuriplo-platform`.
