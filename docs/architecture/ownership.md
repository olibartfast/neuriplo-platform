# Ownership Model

This document defines responsibility boundaries across the neuriplo AI
infrastructure platform. When a change spans multiple repositories, use this
model to decide where the durable implementation should live.

## Boundary Rules

### Domain and Task Behavior

Belongs in `neuriplo-tasks`.

Examples:

- Input and output task contracts
- Preprocessing and postprocessing pipelines
- Result types
- Model-family task adapters
- Task registry and factory behavior

The first task domain is computer vision. Additional domains (NLP embeddings,
audio transcription, tabular models, generative VLM output postprocessing) are
natural extensions under the same contract.

### Backend Execution

Belongs in `neuriplo`.

Examples:

- GPU-first backend interfaces (CUDA, TensorRT, ONNX Runtime, OpenVINO, future accelerators)
- Execution session abstractions with GPU memory management
- Backend capability reporting (GPU device count, memory, compute capability)
- Mixed-precision and quantization policy
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

- KServe V2 / Open Inference Protocol server
- Request admission
- Scheduling and dynamic batching
- Multi-GPU model placement and scheduling policy
- Model lifecycle and version management
- GPU health, utilization reporting, and operational endpoints
- Server-side wiring from KServe requests to `neuriplo-tasks` and `neuriplo`

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
