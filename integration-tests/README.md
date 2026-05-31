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

- [Local inference smoke](local-inference-smoke/README.md): validates local sibling
  checkouts, pinned refs, and the app-owned E2E runner dry-run path.
