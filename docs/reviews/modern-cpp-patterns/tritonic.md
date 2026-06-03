# tritonic Modern C++ Pattern Review

Reviewed on: 2026-06-03

Remote: https://github.com/olibartfast/tritonic

Reviewed ref: `develop` at `710faf5ddde8921e24652887b5a1dca95eb882ef`

## Scope

This review considers the Triton client application against the modern pattern
guidance, especially RAII, Rule of Zero, Adapter, Service Locator caution,
Pipeline, and explicit dependency/version management.

Key files inspected remotely with `gh`:

- `CMakeLists.txt`
- `src/triton/Triton.hpp`
- `src/triton/Triton.cpp`

## Pattern Alignment

- `ITriton` provides an adapter boundary around the Triton client API.
- Shared memory concepts are separated from normal inference flow.
- The application is moving toward local infrastructure rather than depending on
  `vision-infra`.

## Findings

### High: Manual union of non-trivial clients violates RAII

`TritonClient` stores HTTP and GRPC `std::unique_ptr` members in a manual union
with an empty destructor. Only the HTTP member is placement-constructed. Writing
the GRPC member later changes the active union member without correct lifetime
management.

Recommendation: replace the union with `std::variant`, two nullable members, or
separate HTTP and GRPC adapter classes implementing a common internal client
interface.

### High: CUDA shared memory is allocated but not freed

`createCudaSharedMemoryRegion()` uses `cudaMalloc`, but
`SharedMemoryRegion::cleanup()` does not call `cudaFree`.

Recommendation: make CUDA memory an RAII resource. `cleanup()` should call
`cudaFree` when the region owns CUDA memory.

### Medium: `InferResult` ownership starts too late

`infer()`, `inferText()`, and shared-memory inference create a raw
`tc::InferResult*`, parse it, and only then reset a `std::unique_ptr`. If result
parsing throws, the raw result leaks.

Recommendation: immediately wrap the result after a successful `Infer()` call.

### Medium: `vision-core` is fetched from `master`

`CMakeLists.txt` fetches `vision-core` with `GIT_TAG master`. This bypasses the
platform compatibility matrix and makes the consumer sensitive to unrelated
changes on the release branch.

Recommendation: use a tag, commit, or version variable aligned with
`vision-platform/versions.yaml`.

### Low: Logger access uses Service Locator style

`Triton` obtains loggers through `LoggerManager::GetLogger()`. This is tolerable
for infrastructure logging, but it hides dependencies and makes tests less
explicit.

Recommendation: inject logger dependencies where practical, especially for
classes with significant behavior.

## Recommended Next Actions

1. Replace `TritonClient` union before further GRPC/HTTP expansion.
2. Fix CUDA shared-memory ownership.
3. Wrap Triton raw results immediately after successful inference calls.
4. Pin `vision-core` to a known-good version or platform-managed ref.
