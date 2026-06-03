# neuriplo Modern C++ Pattern Review

Reviewed on: 2026-06-03

Remote: https://github.com/olibartfast/neuriplo

Reviewed ref: `develop` at `347db75aa3ee78965b9a128b9b46bc291a10437b`

## Scope

This review considers the backend abstraction layer against the modern pattern
guidance, especially Backend abstraction, Adapter, Registry, State, RAII, and
explicit version compatibility.

Key files inspected remotely with `gh`:

- `CMakeLists.txt`
- `cmake/BackendRegistry.cmake`
- `backends/src/InferenceInterface.hpp`
- `backends/src/InferenceInterface.cpp`

## Pattern Alignment

- `InferenceInterface` is the right abstraction point for backend Strategy /
  Adapter implementations.
- `BackendRegistry.cmake` centralizes CMake-visible backend metadata and keeps
  backend identifiers stable.
- Backend lifecycle state is represented with `BackendState`, which is aligned
  with a State-pattern approach.
- Version and dependency validation are part of configure-time flow.

## Findings

### Medium: Backend registry exists at CMake level, but runtime discovery is not clearly represented

`BackendRegistry.cmake` is useful for build configuration and dependency
validation. The runtime side still depends on backend setup code to select and
construct concrete engines.

Recommendation: keep the CMake registry for build metadata, but mirror it with a
small runtime backend factory registry if runtime backend selection keeps
expanding.

### Low: Interface owns timing and validation concerns

`InferenceInterface` contains execution timing and validation helpers. This is
pragmatic, but it blends core backend execution with observability concerns.

Recommendation: leave it in place for now. If metrics become more complex,
extract timing into a Decorator around `InferenceInterface` rather than pushing
more cross-cutting behavior into every backend.

## Recommended Next Actions

1. Make the runtime backend construction path as centralized as the CMake
   backend metadata path.
2. Add backend capability tests that assert each supported backend has metadata,
   dependency validation, and construction behavior.
3. Prefer Adapter classes around vendor SDKs and keep vendor types out of public
   application-facing interfaces.
