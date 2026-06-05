# Modern Architecture Patterns

This page maps the vision platform repositories to modern C++ and service
architecture patterns used across inference, serving, and integration code. It
extends the GoF-style pattern summary in `overview.md` with operational patterns
that matter at repository boundaries. It is based on the modern C++ pattern
review docs and the source taxonomy in
https://olibartfast.ninja/blog/modern-cpp-design-patterns-beyond-gof.html.

## Platform-wide Patterns

### Composition Root

`vision-inference` owns local executable wiring. `neuriplo-kserve-runtime` owns
serving-process wiring. Runtime dependencies should be created at these
application boundaries and passed inward, rather than discovered through hidden
global service locators.

### Dependency Injection And Service Locator

Core dependencies should be explicit constructor or factory inputs. Service
Locator-style lookup is acceptable only for controlled infrastructure concerns
such as logging, metrics, tracing, plugin discovery, or legacy migration. It
should not hide domain, backend, or task dependencies from public APIs.

### Pipeline

Inference flows should stay explicit:

1. Acquire input.
2. Preprocess using `vision-core` task contracts.
3. Execute through `neuriplo` backend abstractions.
4. Postprocess into `vision-core` result variants.
5. Render, serialize, or return results in the owning application.

Pipeline steps may be refactored internally, but cross-repository contracts must
keep task inputs, tensor shapes, result schemas, and error behavior stable.

### Adapter And Anti-Corruption Layer

Vendor SDKs, serving protocols, and media backends should stay behind adapter
interfaces:

- `neuriplo`: backend adapters over ONNX Runtime, TensorRT, OpenVINO, and other
  engine APIs.
- `vision-core`: task adapters between model tensors and stable result types.
- `vision-inference`: CLI and video IO adapters around user inputs.
- `neuriplo-kserve-runtime`: KServe V2 protocol adapter around internal task and
  backend contracts.

Do not leak vendor SDK types into platform contracts or application-facing task
interfaces.

### RAII And Explicit Ownership

Runtime objects that own files, models, buffers, network clients, or backend
sessions should use RAII and move-only ownership. Public factory boundaries
should return explicit owners such as `std::unique_ptr` where a single component
owns lifecycle.

### Type Erasure, Policies, And Concepts

Runtime-flexible behavior may use type erasure or callable strategies when that
keeps APIs smaller than inheritance-heavy hierarchies. Compile-time behavior may
use policy-based design or concepts when types are known and performance or
diagnostics matter. Public contracts should state whether extension is runtime
or compile-time.

### Registry

Registries are acceptable when they make supported capabilities auditable:

- `vision-core`: model type to task-family routing.
- `neuriplo`: backend metadata and construction.
- `neuriplo-platform`: repository ownership and compatibility metadata.

Registries should keep ordering and fallback behavior explicit. Dynamic plugin
registries need their own contract before use.

## Serving And Reliability Patterns

### Producer-Consumer And Queue Worker

Serving runtimes may decouple request admission from execution with bounded
queues. Queue ownership, cancellation, and shutdown behavior must be explicit so
workers cannot outlive their models, executors, or request contexts.

### Dynamic Batching

Batch schedulers may group compatible requests, but batching must preserve each
request output order, timeout, and error mapping. Shape and dtype assumptions
remain cross-repository contract concerns.

### Zero-Copy Ownership

Hot paths that move frames, tensors, packets, or GPU buffers should pass
ownership or references between stages instead of repeatedly copying payloads.
Queues should make ownership transfer explicit with move-only handles where
possible.

### Object Pool

Pools are appropriate for expensive reusable resources such as buffers, sessions,
or request objects. Pool entries must have clear reset rules before reuse and
must not hide unbounded memory growth.

### Double Buffering

Double buffering is appropriate when one stage writes fresh data while another
stage reads the previous snapshot, for example camera capture, rendering, audio,
or shared sensor state. Swap ownership and visibility explicitly.

### Timeout, Retry, And Bulkhead

External calls and long-running inference paths should have bounded execution.
Retries must be idempotent or explicitly guarded and should use exponential
backoff with jitter for remote or shared-service failures. Circuit breakers may
fail fast when downstream systems are unhealthy. Bulkheads should isolate model,
backend, or tenant failures so one overloaded path does not block unrelated work.

### Health Endpoint

Operational endpoints should report readiness and liveness from real subsystem
state: model lifecycle, backend availability, queue health, and scheduler state.
Static health responses are not enough for serving runtimes.

### Idempotent Consumer

Serving and integration workers should tolerate duplicate request handling when
transport or retry behavior can replay work. Idempotency keys, request IDs, and
stable error responses belong at application or protocol boundaries.

## Migration And Domain Patterns

### Strangler Fig

When modernizing legacy runtime paths, wrap old behavior behind a compatibility
interface and replace behavior incrementally. Avoid big-bang rewrites for
inference, serving, or hardware integration paths with existing production
behavior.

### CQRS, Repository, And Unit Of Work

These patterns belong only where platform services own persistent state or
stateful command/query APIs. They are not default patterns for task or backend
libraries, but they are valid for serving control planes, model registries, or
operational metadata stores.

### Sidecar And Backend-for-Frontend

Sidecars may own deployment concerns such as TLS, telemetry, proxying, or
service discovery. Backend-for-Frontend components may tailor APIs for specific
clients. Both are deployment or service-boundary patterns, not library-level C++
patterns.

## Repository Guidance

| Repository | Primary modern patterns |
|---|---|
| `vision-core` | Factory Registry, Strategy, Visitor helpers, type erasure or concepts where useful, Adapter, explicit task contracts |
| `neuriplo` | Backend Adapter, runtime Factory, State, Decorator for observability, RAII, zero-copy ownership |
| `vision-inference` | Composition Root, Dependency Injection, Pipeline, Builder, Command, application-boundary logging |
| `neuriplo-kserve-runtime` | Producer-Consumer, Queue Worker, Dynamic Batching, Timeout, Circuit Breaker, Bulkhead, Health Endpoint |
| `videocapture` | Adapter, RAII resource ownership, Strategy for capture backends, double buffering when needed |
| `neuriplo-platform` | Compatibility Registry, ownership map, ADRs, cross-repository contract docs |

## Change Checklist

Before accepting a cross-repository architecture change, answer:

- Which repository owns the composition root for this behavior?
- Which dependencies are constructor-injected, and which cross-cutting services may use controlled lookup?
- Which contract prevents vendor or protocol types from leaking across layers?
- Which lifecycle object owns cleanup, cancellation, and shutdown?
- Which registry or metadata file makes the supported cases auditable?
- Which timeout, retry, batching, circuit-breaker, bulkhead, or health behavior changes for users?
- Which data movement path avoids avoidable hot-path copies?
- Which repo-local and downstream checks prove compatibility still holds?
