# Architecture Overview

The platform is organized around explicit boundaries between task semantics,
backend execution, local application flow, and serving operations.

## Ecosystem Map

```text
vision-core
    |
neuriplo
    |
vision-inference

neuriplo-kserve-runtime
    |
neuriplo

vision-platform
    |
coordinates architecture, contracts, versions, examples, and integration tests
```

## Repository Responsibilities

### vision-core

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

### vision-inference

Owns:

- CLI
- Configuration
- Runtime wiring
- Visualization
- End-to-end local application flow

Likely patterns:

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

### vision-platform

Owns:

- Architecture documentation
- ADRs
- Cross-repository contracts
- Version matrix
- Integration tests
- End-to-end examples

Does not own:

- Business logic
- Runtime implementation
- Backend code
- Model-specific task code

## Architectural Questions

Every major change should answer:

- Where should this belong?
- Who owns this responsibility?
- What are the component boundaries?
- What contracts exist between components?
- How does this evolve when the next model, backend, or runtime appears?
