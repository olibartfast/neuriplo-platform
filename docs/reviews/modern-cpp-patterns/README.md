# Modern C++ Pattern Reviews

Reviewed on: 2026-06-03

These reviews compare each neuriplo-platform related repository against the
modern C++ and architecture patterns described in:

`/home/oli/Downloads/modern_cpp_design_patterns_beyond_gof.md` and the published source article:

https://olibartfast.ninja/blog/modern-cpp-design-patterns-beyond-gof.html

Remote metadata was checked with `gh`. Source files were inspected on the
integration branch where available:

- `vision-core`: `develop`
- `neuriplo`: `develop`
- `vision-inference`: `develop`
- `videocapture`: `develop`
- `tritonic`: `develop`
- `neuriplo-kserve-runtime`: `master` because no `develop` or `dev` branch was
  visible
- `neuriplo-platform`: `main` because no `develop` branch was visible

## Repository Reviews

- [vision-core](vision-core.md)
- [neuriplo](neuriplo.md)
- [vision-inference](vision-inference.md)
- [videocapture](videocapture.md)
- [neuriplo-kserve-runtime](neuriplo-kserve-runtime.md)
- [tritonic](tritonic.md)
- [neuriplo-platform](neuriplo-platform.md)

## Source Taxonomy Applied

The review set now maps findings to these modern C++ and production patterns:

- RAII and Rule of Zero for owned clients, CUDA buffers, sessions, and results.
- Dependency Injection and Composition Root for explicit wiring.
- Factory Registry and Plugin Architecture for backend/task selection.
- Pipeline, Producer-Consumer, Queue Worker, and Dynamic Batching for inference flow.
- Anti-Corruption Layer and Adapter for vendor SDK and protocol boundaries.
- Timeout, Retry with Backoff, Circuit Breaker, Bulkhead, Health Endpoint, and
  Idempotent Consumer for serving reliability.
- Object Pool, Zero-Copy Ownership, and Double Buffering for hot data paths.

## Cross-Repository Priorities

1. Fix RAII and lifetime issues in `tritonic`.
2. Fix timeout and registry concurrency issues in `neuriplo-kserve-runtime`.
3. Reconcile platform metadata with actual remote branches and tracked
   consumers.
4. Update platform architecture docs to include modern non-GoF patterns used by
   inference and serving systems.
