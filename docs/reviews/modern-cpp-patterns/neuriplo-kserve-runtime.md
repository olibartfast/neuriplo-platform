# neuriplo-kserve-runtime Modern C++ Pattern Review

Reviewed on: 2026-06-03

Remote: https://github.com/olibartfast/neuriplo-kserve-runtime

Reviewed ref: `master` at `baf4d9ed2eb0b8d22c0f86e22c4ec7b1a5318a1a`

Branch note: no remote `develop` or `dev` branch was visible through `gh` during
this review.

## Scope

This review considers the serving runtime against the modern pattern guidance,
especially Queue Worker, Producer-Consumer, Dynamic Batching, Timeout, Bulkhead,
Registry, Health Endpoint, Metrics, and Adapter boundaries.

Key files inspected remotely with `gh`:

- `CMakeLists.txt`
- `README.md`
- `src/Scheduler.hpp`
- `src/ModelScheduler.cpp`
- `src/DynamicBatcher.cpp`
- `src/BackendRegistry.cpp`

## Pattern Alignment

- `Scheduler` provides a clear scheduling interface.
- `ModelScheduler` uses a bounded queue and worker threads, matching a
  Queue Worker / Producer-Consumer shape.
- `DynamicBatcher` separates merge and split behavior from scheduler control
  flow.
- Runtime exposes health, readiness, and metrics endpoints as first-class
  operational behavior.

## Source Taxonomy Mapping

Relevant source patterns: Queue Worker, Producer-Consumer, Dynamic Batching,
Timeout, Retry with Backoff, Circuit Breaker, Bulkhead, Health Endpoint,
Idempotent Consumer, Metrics, and Registry. Scheduler deadlines must isolate
blocked executor work instead of synchronously waiting during cleanup.

Acceptance guidance: make timeout tests use a deliberately blocking executor,
make concurrent backend capability reads stress the registry, and preserve KServe
response ordering and error mapping.

## Findings

### High: Async timeout path can block while destroying the future

`ModelScheduler::runInference()` uses `std::async` when `instances > 1` and
returns `false` on `future.wait_until(deadline) == timeout`. The local future is
then destroyed. For a `std::launch::async` future, destruction can block until
the async task completes. That defeats the timeout and weakens the bulkhead
boundary.

Recommendation: execute backend calls on owned worker threads with cooperative
cancellation, or use executor instances that can be abandoned safely without
blocking the scheduler thread.

### High: Backend registry default initialization is not thread-safe

`BackendRegistry.cpp` uses a function-local `static bool registered` and mutates
the global `capabilities` map before acquiring `registry_mutex`. Concurrent
first calls can race.

Recommendation: use `std::once_flag` and `std::call_once`, or construct an
immutable default registry before exposing mutation.

### Medium: Scheduler implementation is dense

`ModelScheduler.cpp` owns queueing, batching, deadlines, executor selection,
metrics, and result fulfillment in one implementation.

Recommendation: keep the public `Scheduler` interface, but consider extracting
executor selection, deadline handling, and metrics recording into small
collaborators if scheduler behavior continues to grow.

## Recommended Next Actions

1. Fix the timeout path before relying on scheduler deadlines for production
   isolation.
2. Make backend registry initialization thread-safe.
3. Add stress tests for concurrent backend capability reads and scheduler
   timeout behavior with a deliberately blocking executor.
