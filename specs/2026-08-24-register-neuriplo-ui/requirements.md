# Requirements

Milestone: Register neuriplo-ui in the multi-repository architecture

Status: Complete

## Goal

Make [`neuriplo-ui`](https://github.com/olibartfast/neuriplo-ui) a first-class
component in the Neuriplo architecture control plane and record the interface
it consumes from `neuriplo-infer`.

## In Scope

- Add repository, checkout, ownership, dependency, and automation metadata.
- Pin the current private repository state as WIP in `versions.yaml`.
- Replace the proposed Qt architecture with an accepted browser application
  decision while retaining the old ADR as superseded history.
- Document the browser, local adapter, and `neuriplo-infer` process boundary.
- Document capability schema version 1 without copying the owning JSON Schema.
- State that `local` and `client_server` are workflow choices, and that KServe
  is a client-server protocol rather than a local backend.

## Out Of Scope

- UI implementation changes.
- A released `neuriplo-ui` version or inclusion in an existing compatibility
  set.
- Real run execution, result rendering, or benchmark contracts beyond the
  implemented capability-discovery boundary.
- New platform runtime code or dependencies.

## Decisions

- `neuriplo-ui` is a standalone browser application repository using a local
  API adapter to invoke `neuriplo-infer`.
- `neuriplo-infer` remains authoritative for build-specific tasks, models,
  parameters, backends, workflows, protocols, and transports.
- `neuriplo-ui` uses `master` as its current default integration branch and is
  not governed by the C++ sibling Gitflow rule.

## Constraints

- Keep all platform files ASCII-only.
- Link to the owning repository for implementation details and schema content.
- Preserve existing compatibility claims and runtime ownership boundaries.
