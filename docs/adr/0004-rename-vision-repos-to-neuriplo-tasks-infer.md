# ADR 0004: Rename vision-core and vision-inference to neuriplo-tasks and neuriplo-infer

Date: 2026-06-06

Status: Proposed

## Problem

The cluster still uses legacy `vision-*` names at every layer: GitHub
repositories, platform metadata keys, CMake targets, public include paths, and
the `vision_core` C++ namespace. That naming no longer matches the neuriplo
product vocabulary (`neuriplo-platform`, `neuriplo`, `neuriplo-kserve-runtime`)
and makes ownership boundaries harder to explain.

We need a single, written migration plan that covers the full rename scope:
repository identity, build system symbols, public headers, namespaces, consumer
repos, platform contracts, and release coordination.

## Constraints

- `neuriplo-platform` owns compatibility policy and contracts, not
  implementation moves.
- Task and result semantics remain owned by the task library; this rename must
  not change tensor shapes, model type strings, CLI flags, or backend behavior
  unless explicitly versioned elsewhere.
- Sibling repos follow Gitflow: normal work on `develop`; `master` is
  release-only.
- Downstream consumers exist outside the core cluster (`vision-ros`, `tritonic`,
  and any external `find_package` users).
- Open compile-speed PRs should land before this migration starts to avoid
  overlapping large diffs.
- C++ identifiers cannot contain hyphens; repo names and CMake target names may.

## Options

1. **Repo identity only** - rename GitHub repos and platform metadata; keep
   `#include "vision-core/..."`, `namespace vision_core`, and CMake target
   `vision-core`.
2. **Repo + build identity** - option 1 plus CMake `project()`, targets,
   executables, Docker image names; keep includes and namespace.
3. **Full public API rename** - option 2 plus include tree, namespace, installed
   CMake package names, and platform contract owner keys.
4. **Full rename with one-release compatibility shims** - option 3 plus
   forwarding headers, namespace aliases, and CMake `ALIAS` targets for one
   release cycle.

## Decision

Adopt **option 4** when the migration is approved:

| Layer | vision-core (today) | neuriplo-tasks (target) |
|-------|---------------------|-------------------------|
| GitHub repo | `vision-core` | `neuriplo-tasks` |
| Platform key | `vision-core` | `neuriplo-tasks` |
| CMake project / target | `vision-core` | `neuriplo-tasks` |
| CMake package | `find_package(vision-core)` | `find_package(neuriplo-tasks)` |
| Include root | `vision-core/...` | `neuriplo/tasks/...` |
| C++ namespace | `vision_core` | `neuriplo_tasks` |
| Version env var | `VISION_CORE_VERSION` | `NEURIPLO_TASKS_VERSION` |

| Layer | vision-inference (today) | neuriplo-infer (target) |
|-------|--------------------------|-------------------------|
| GitHub repo | `vision-inference` | `neuriplo-infer` |
| Platform key | `vision-inference` | `neuriplo-infer` |
| CMake project | `vision-inference` | `neuriplo-infer` |
| Executable | `vision-inference` | `neuriplo-infer` |
| App static library | `vision-inference-app` | `neuriplo-infer-app` |
| Version env var | (implicit / sibling pins) | `NEURIPLO_INFER_VERSION` |

**Class names** (`VisionApp`, `InferencePipeline`, etc.) stay unchanged in the
first migration unless a follow-up ADR decides otherwise. The app layer has no
`vision_inference` namespace today.

**Compatibility shims** ship for one released ecosystem baseline, then remove in
the next major bump:

```cpp
// Deprecated forwarding header (neuriplo-tasks)
#pragma once
#include "neuriplo/tasks/core/result_types.hpp"
```

```cpp
namespace vision_core = neuriplo_tasks;  // deprecated; remove next major
```

```cmake
add_library(neuriplo-tasks ...)
add_library(vision-core ALIAS neuriplo-tasks)
add_library(vision-core::vision-core ALIAS neuriplo-tasks)
```

## Consequences

### Improves

- Consistent neuriplo naming across repos, docs, and platform metadata.
- Clearer role labels: tasks library vs local inference application.
- Easier onboarding: names match `neuriplo-platform` cluster map vocabulary.

### Makes harder

- Every consumer must update includes, namespaces, and link lines (or depend on
  shims temporarily).
- `versions.yaml`, `ops/repo-meta/*.yaml` filenames, and `CLUSTER_MAP.yaml` keys
  must change together (`check_platform.py` ties repo-meta filename to cluster
  key).
- FetchContent cache keys and `_*_SOURCE_DIR` variable names change; developers
  need clean build dirs.
- GitHub repo rename redirects help clones but not human bookmarks or old CI
  logs.

### Required follow-up

- New platform compatibility set in `versions.yaml` after all repos release.
- Update contracts (`task-contract.md`, `result-contract.md`) owner keys and
  documented type namespaces.
- Update integration smoke and e2e docs that reference old repo paths.
- Announce shim removal date when cutting the next major task-library release.

## Scope and blast radius

```text
neuriplo-tasks (was vision-core)
  |- ~63 public headers under include/vision-core/
  |- ~130 files with namespace vision_core
  |- ~120 source includes of "vision-core/..."
  |- CMake install/export (vision-core-config.cmake)
  |- 24 test executables
  '- export/ docs and scripts

neuriplo-infer (was vision-inference)
  |- FetchContent + versions.env pins
  |- ~80 files referencing vision-core / vision_core
  |- ~50 files referencing vision-inference naming
  |- 8 Dockerfiles, VS Code launch configs, release scripts
  '- app link to renamed task target

neuriplo-platform
  |- ~80 references across CLUSTER_MAP, versions, policies, contracts, ADRs
  |- ops/repo-meta/vision-core.yaml -> neuriplo-tasks.yaml
  '- ops/repo-meta/vision-inference.yaml -> neuriplo-infer.yaml

Secondary consumers
  |- vision-ros (FetchContent + heavy vision_core usage)
  '- tritonic (FetchContent + App.cpp vision_core usage)

neuriplo-kserve-runtime
  '- mostly docs/plan references today; update pins when integrated
```

## Effort estimate

| Phase | Work | Days (1 engineer) |
|-------|------|-------------------|
| 0. ADR approval + deprecation policy | Finalize naming table and shim lifetime | 1-2 |
| 1. neuriplo-tasks core rename | Headers, namespace, CMake install/export, tests | 4-6 |
| 2. Platform + contracts | CLUSTER_MAP, versions, repo-meta, contracts, smoke | 2-3 |
| 3. neuriplo-infer consumer update | Includes, namespaces, link targets, pins | 2-3 |
| 4. neuriplo-infer self-identity | project(), binary, static lib, Docker, CI, scripts | 2-3 |
| 5. Secondary consumers | vision-ros, tritonic | 1-2 |
| 6. Compatibility shims | Forwarding headers, namespace alias, CMake ALIAS | 2-3 |
| 7. Validation train | Full CI, smoke, release pins, changelogs | 2-3 |

**Total: 16-22 engineering days** (~3-4 calendar weeks for one engineer, ~2 weeks
with two engineers splitting phases 1+3 vs 2+4).

Add 30-50% calendar time if started before open compile-speed PRs merge.

**Cost:** no new infrastructure spend; cost is engineering time and a mandatory
coordinated ecosystem version bump.

## Migration procedure

1. Measure baseline: record current `versions.yaml` compatibility set and open
   PRs; merge compile-speed work first.
2. Approve this ADR (move status to Accepted).
3. Rename GitHub repo `vision-core` to `neuriplo-tasks` (GitHub redirect
   handles old clone URLs temporarily).
4. Land neuriplo-tasks PR: directory move, namespace, CMake, shims, tests green.
5. Update platform metadata and contracts; publish new compatibility set draft.
6. Rename GitHub repo `vision-inference` to `neuriplo-infer`.
7. Land neuriplo-infer PR: consumer updates, self rename, pins to new task
   release.
8. `vision-ros` already updated to `neuriplo-ros`; `tritonic` keeps its repo
   name but must update task-library references. Run cross-repo smoke.
9. Tag releases; update `versions.yaml` compatibility set to released tags.
10. Document shim removal target in task-library CHANGELOG; remove shims in next
    major.

## PR train (sequential)

| Order | Repository | Content | Blocks |
|-------|------------|---------|--------|
| 1 | neuriplo-platform | Accept ADR; no code rename yet | policy |
| 2 | neuriplo-tasks | Core rename + shims | all consumers |
| 3 | neuriplo-platform | Metadata, contracts, versions draft | infer pin |
| 4 | neuriplo-infer | Consumer + self rename | secondary repos |
| 5 | vision-ros, tritonic | Follow new task release | - |
| 6 | neuriplo-platform | Final compatibility set + smoke green | release |

Do not run this train in parallel with the compile-speed PR series.

## Validation

Each PR must include:

- `scripts/check_platform.py` (platform changes)
- Repo-local `ctest` / configure commands from `ops/repo-meta/*.yaml`
- `integration-tests/local-inference-smoke/run.py` after infer PR
- Evidence that task model type strings, CLI flags, result schema, and backend
  fallback behavior are unchanged

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Missed FetchContent or CI cache key | Medium | Ripgrep checklist; clean CI caches |
| External users on old includes | High | One-release forwarding headers |
| Hyphen vs underscore confusion | Medium | Naming table in this ADR |
| PR conflicts with in-flight work | High | Merge compile-speed PRs first |
| Incomplete platform key renames | High | Rename `ops/repo-meta` and CLUSTER_MAP in same PR |

## References

- `ops/CLUSTER_MAP.yaml` - current repo keys and dependency edges
- `versions.yaml` - compatibility matrix to bump after migration
- `ops/runbooks/faster-compilation.md` - unrelated; land before this work
- `ops/runbooks/cross-repo-api-migration.md` - use for consumer update workflow
- `contracts/task-contract.md` - owner field becomes `neuriplo-tasks`
