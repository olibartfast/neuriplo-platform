# Architecture Overview

The platform is organized around explicit boundaries between task semantics,
backend execution, local application flow, and serving operations. Modern C++
and service patterns are mapped in `modern-patterns.md`.

## Ecosystem Map

```text
neuriplo-tasks
    |
neuriplo
    |
neuriplo-infer

neuriplo-kserve-runtime
    |
neuriplo

neuriplo-platform
    |
coordinates architecture, contracts, versions, examples, and integration tests
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
- Runtime wiring
- Visualization
- End-to-end local application flow

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

## Architectural Questions

Every major change should answer:

- Where should this belong?
- Who owns this responsibility?
- What are the component boundaries?
- What contracts exist between components?
- How does this evolve when the next model, backend, or runtime appears?
