# Architecture Overview

The platform is organized around explicit boundaries between task semantics,
backend execution, local application flow, and serving operations. Modern C++
and service patterns are mapped in `modern-patterns.md`.

## Ecosystem Map

```text
embedded local mode:
  neuriplo-infer -> neuriplo-tasks + neuriplo + videocapture

remote KServe client mode:
  neuriplo-infer -> KServe V2 endpoint
                   |- neuriplo-kserve-runtime -> neuriplo-tasks + neuriplo
                   '- other KServe-compatible servers

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
  |- neuriplo-tasks: task contract, preprocess, postprocess, result type
  |- neuriplo: backend abstraction, backend execution
  |- neuriplo-infer: embedded local app and KServe V2 client
  |- neuriplo-kserve-runtime: KServe V2 server backed by neuriplo
  '- videocapture: image and video source handling

External systems:
  |- model artifacts and labels
  |- container runtime and GPU or CPU backend packages
  |- KServe-compatible serving endpoints
  '- secondary consumers such as neuriplo-ros and tritonic
```

## Repository Responsibilities

### neuriplo-tasks

Owns:

- Task contracts
- Preprocessing
- Postprocessing
- Result types
- Model-specific task logic

Likely patterns:

- Factory Method / Registry
- Strategy
- Template Method
- Visitor
- Composite
- Adapter
- Explicit task contracts

### neuriplo

Owns:

- Backend abstractions
- Backend execution
- Runtime compatibility

Likely patterns:

- Adapter
- Bridge
- Abstract Factory
- Decorator
- State
- RAII
- Runtime factory registry

### neuriplo-infer

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

### neuriplo-kserve-runtime

Owns:

- KServe V2 protocol
- Request admission
- Scheduling
- Dynamic batching
- Model lifecycle
- Operational endpoints

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

### neuriplo-platform

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
- `docs/architecture/repo-name-migration.md`: legacy to canonical repository
  naming table for the `vision-*` rename.

## Architectural Questions

Every major change should answer:

- Where should this belong?
- Who owns this responsibility?
- What are the component boundaries?
- What contracts exist between components?
- How does this evolve when the next model, backend, or runtime appears?
