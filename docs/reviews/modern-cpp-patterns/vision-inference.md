# vision-inference Modern C++ Pattern Review

Reviewed on: 2026-06-03

Remote: https://github.com/olibartfast/vision-inference

Reviewed ref: `develop` at `6abb233ceef16f3cbd264df8cca8d2e188c9c288`

## Scope

This review considers the local application layer against the modern pattern
guidance, especially Composition Root, Pipeline, Builder, Command, explicit
dependency wiring, and dependency version pinning.

Key files inspected remotely with `gh`:

- `CMakeLists.txt`
- `README.md`
- `app/CMakeLists.txt`
- `app/inc/VisionApp.hpp`
- `app/src/VisionApp.cpp`
- `app/inc/InferencePipeline.hpp`
- `app/src/InferencePipeline.cpp`

## Pattern Alignment

- `VisionApp` is thin and delegates work to an `InferencePipeline`.
- `InferencePipelineBuilder` is a useful Composition Root for local inference.
- `CLICommands` and pipeline execution follow a Command-style split.
- Dependencies on `vision-core`, `neuriplo`, and `videocapture` are fetched via
  version variables rather than raw `master`, which is aligned with the platform
  compatibility model.

## Findings

### Medium: Builder stages are mostly fluent no-ops

`InferencePipelineBuilder::backend()`, `task()`, and `precision()` currently
return `*this` without doing staged work. Most construction happens in `build()`.
This makes the API look more structured than the implementation actually is.

Recommendation: either move real staged validation into those methods or
simplify the builder API so it does not imply incomplete intermediate states.

### Medium: Pipeline construction is doing several responsibilities

`InferencePipelineBuilder::build()` handles logging, label loading, hardware
detection, backend creation, model metadata conversion, task creation, and
renderer selection.

Recommendation: keep `build()` as the Composition Root, but extract small
private helpers around backend setup, task setup, and presentation setup so the
pipeline remains auditable.

### Low: Logging is globally configured inside `VisionApp`

`VisionApp::setupLogging()` initializes glog and mutates log directories. This is
acceptable for an executable, but should not leak into libraries.

Recommendation: keep logging setup in the application boundary. Avoid adding
global service lookups to domain or backend code.

## Recommended Next Actions

1. Make builder stages meaningful or collapse them into direct construction.
2. Add focused tests around pipeline construction for each task/backend category
   that the CLI supports.
3. Keep dependency pins flowing from repository version files and platform
   compatibility sets.
