# Architecture Overview

Neuriplo is an AI infrastructure and GPU-first serving platform. It provides an
Open Inference Protocol (KServe V2) runtime and client, a backend-agnostic GPU
execution layer (ONNX Runtime, TensorRT, OpenVINO, and future accelerators), and
a task domain layer that currently starts with computer vision workloads.

The platform is organized around explicit boundaries between task semantics,
backend execution, local application flow, and serving operations. Modern C++
and service patterns are mapped in `modern-patterns.md`.

## Ecosystem Map

```text
embedded local mode:
  neuriplo-infer -> neuriplo-tasks + neuriplo + videocapture

remote KServe client mode:
  neuriplo-infer -> neuriplo-kserve-client -> KServe V2 endpoint
                   |- neuriplo-kserve-runtime -> neuriplo-tasks + neuriplo
                   '- other KServe-compatible servers (Triton, OVMS, ...)

neuriplo-platform coordinates architecture, contracts, versions, examples, and
integration tests across both modes.
```

## C4-Style Context

```text
Person: platform maintainer
  |
  | reads and updates policy, contracts, ADRs, versions, examples, smoke plans
  v
System: neuriplo-platform
  |
  | governs compatibility expectations for
  v
System boundary: neuriplo inference ecosystem
  |
  |- neuriplo-tasks: task contract, preprocess, postprocess, result type (CV tasks as first domain)
  |- neuriplo: GPU-first backend abstraction, execution, GPU capability reporting
  |- neuriplo-infer: embedded local app and KServe V2 client wiring
  |- neuriplo-kserve-client: backend-agnostic KServe V2 protocol client (HTTP/gRPC)
  |- neuriplo-kserve-runtime: KServe V2 server with dynamic batching, scheduling, multi-GPU placement
  '- videocapture: image and video source handling (optional, for CV task domain)

External systems:
  |- model artifacts and labels
  |- container runtime and GPU backend packages (CUDA, TensorRT, oneAPI)
  |- KServe-compatible serving endpoints
  '- AI datacenter infrastructure (GPU fleets, model registries, node orchestration)
```

## Repository Responsibilities

### [neuriplo-tasks](https://github.com/olibartfast/neuriplo-tasks)

Owns:

- Task contracts
- Preprocessing
- Postprocessing
- Result types
- Model-specific task logic

The first task domain is computer vision (detection, segmentation, pose, depth,
classification, open-vocabulary). Additional domains (NLP embeddings, audio
transcription, tabular inference) are natural extensions that fit the same
preprocess/execute/postprocess contract.

Likely patterns:

- Factory Method / Registry
- Strategy
- Template Method
- Visitor
- Composite
- Adapter
- Explicit task contracts

### [neuriplo](https://github.com/olibartfast/neuriplo)

Owns:

- GPU-first backend abstractions (CUDA, TensorRT, ONNX Runtime, OpenVINO, future accelerators)
- Backend execution and session lifecycle
- GPU capability discovery and reporting (device count, memory, compute capability)
- Runtime compatibility and mixed-precision policy

Likely patterns:

- Adapter
- Bridge
- Abstract Factory
- Decorator
- State
- RAII
- Runtime factory registry

### [neuriplo-infer](https://github.com/olibartfast/neuriplo-infer)

Owns:

- CLI
- Configuration
- Runtime wiring for embedded local inference
- KServe V2 client wiring for remote inference
- Visualization
- End-to-end local and remote application flow

Likely patterns:

- Composition Root
- Pipeline
- Facade
- Builder
- Command

### [neuriplo-kserve-client](https://github.com/olibartfast/neuriplo-kserve-client)

Owns:

- KServe V2 / Open Inference Protocol client (HTTP and gRPC transports)
- Wire protocol encode/decode over raw little-endian tensor bytes
- Health/readiness probes and the model repository extension (index/load/unload)
- Transport concerns: retry/backoff, keep-alive, TLS/mTLS, auth
- No dependency on any inference backend (consumed by neuriplo-infer)

Likely patterns:

- Adapter
- Strategy (transport selection)
- Facade
- Retry / Backoff / Timeout
- Pure protocol/codec helpers

### [neuriplo-kserve-runtime](https://github.com/olibartfast/neuriplo-kserve-runtime)

Owns:

- KServe V2 / Open Inference Protocol server
- Request admission and validation
- Scheduling and dynamic batching
- Multi-GPU model placement and scheduling policy
- Model lifecycle and version management
- GPU health and utilization reporting
- Operational endpoints (health, readiness, metrics)

Likely patterns:

- Proxy
- Mediator
- Observer
- Chain of Responsibility
- Memento
- Strategy
- Producer-Consumer
- Queue Worker
- Dynamic Batching
- Timeout / Retry / Bulkhead
- Health Endpoint
- Idempotent Consumer

### [neuriplo-platform](https://github.com/olibartfast/neuriplo-platform)

Owns:

- Architecture documentation
- ADRs
- Cross-repository contracts
- Version matrix
- Integration tests
- End-to-end examples
- Modern pattern taxonomy

Does not own:

- Business logic
- Runtime implementation
- Backend code
- Model-specific task code

## Architecture Pattern References

- `docs/architecture/modern-patterns.md`: modern C++ and service pattern
  taxonomy for repository boundaries, serving reliability, and change review.
- `docs/architecture/inference-modes.md`: embedded local and remote KServe
  client/server dependency modes for `neuriplo-infer`.
- `docs/architecture/production-roadmap.md`: production-readiness roadmap for
  contracts, compatibility CI, release policy, observability, reliability,
  security, deployment, failure modes, fitness tests, and runbooks.

## Architectural Questions

Every major change should answer:

- Where should this belong?
- Who owns this responsibility?
- What are the component boundaries?
- What contracts exist between components?
- How does this evolve when the next model, backend, or runtime appears?
