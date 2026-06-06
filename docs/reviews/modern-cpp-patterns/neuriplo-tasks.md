# neuriplo-tasks Modern C++ Pattern Review

Reviewed on: 2026-06-03

Remote: https://github.com/olibartfast/neuriplo-tasks

Reviewed ref: `develop` at `ed2d11e5e2f6272d40f136627db7cce7ff1e7d3a`

## Scope

This review considers the `develop` branch against the modern pattern guidance in
`modern_cpp_design_patterns_beyond_gof.md`, with emphasis on explicit
composition, registries, pipeline boundaries, RAII, and avoiding hidden global
dependencies.

Key files inspected remotely with `gh`:

- `CMakeLists.txt`
- `README.md`
- `include/neuriplo/tasks/core/task_factory.hpp`
- `src/core/task_factory.cpp`
- `include/neuriplo/tasks/core/task_interface.hpp`

## Pattern Alignment

- `TaskInterface` provides a clear Strategy-style boundary for preprocessing and
  postprocessing.
- `TaskFactory` uses a registration table of matchers and creators rather than a
  monolithic switch. This is a good step toward a Factory Registry pattern.
- Task ownership remains in the domain layer, which matches the platform task
  contract.
- `std::unique_ptr` ownership is used for task creation, which fits RAII and
  Rule-of-Zero expectations.

## Source Taxonomy Mapping

Relevant source patterns: Factory Registry, Strategy, modern Visitor via
`std::variant` / `std::visit`, Adapter, explicit ownership, and optional type
erasure or concepts. `neuriplo-tasks` should keep task contracts stable and avoid
plugin machinery until third-party task extension is an explicit product goal.

Acceptance guidance: route all stable model strings through tested descriptors or
registry entries, keep `Result` schema unchanged, and prefer optional visitor
helpers over forcing consumers into one dispatch style.

## Findings

### Medium: Task registration is still closed at compile time

`src/core/task_factory.cpp` uses a static registration table compiled into
`neuriplo-tasks`. This is simpler and safer than dynamic plugins, but every new
task still requires editing the central factory source.

Recommendation: keep the current table for stable built-in tasks, but consider a
separate extension registry if external task plugins become a supported use case.

### Low: Factory matching mixes routing policy with construction

The match predicates encode alias normalization, task family routing, and
construction in one table. This is workable, but the table will become harder to
audit as more model families are added.

Recommendation: split the registration table into task-family groups or add a
small typed `TaskDescriptor` so routing metadata is visible without reading
lambda bodies.

## Recommended Next Actions

1. Keep `TaskFactory` as the public creation boundary.
2. Add tests that assert all stable model type strings from the platform metadata
   route to the expected task family.
3. Document whether third-party task plugins are in scope. If yes, design an
   explicit plugin registry rather than expanding the internal static table
   indefinitely.
