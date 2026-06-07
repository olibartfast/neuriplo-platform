# ADR 0001: Use neuriplo-platform as architecture control plane

Date: 2026-05-31

Status: Accepted

## Problem

The neuriplo inference ecosystem spans multiple repositories with distinct
responsibilities. Without a coordination point, architecture decisions, version
compatibility, integration scenarios, and cross-repository contracts can drift
into implementation repositories where ownership becomes unclear.

## Constraints

- Runtime implementation should remain close to the code that owns it.
- Public repositories should not require internal planning documents.
- Cross-repository contracts need a stable place to be reviewed and tested.
- The platform should avoid becoming a god repository.

## Options

1. Put all architecture, contracts, integration tests, and runtime code in one
   repository.
2. Keep all coordination documents scattered across implementation repositories.
3. Use `neuriplo-platform` as a private architecture control plane while keeping
   implementation in the owning repositories.

## Decision

Use `neuriplo-platform` as the architecture control plane for ADRs, architecture
documentation, contracts, version matrix, integration tests, Docker composition,
and end-to-end examples.

Implementation remains in the owning repositories:

- `neuriplo-tasks` owns domain and task behavior.
- `neuriplo` owns backend abstractions and execution.
- `neuriplo-infer` owns local application flow.
- `neuriplo-kserve-runtime` owns serving runtime behavior.

## Consequences

Positive:

- Ownership boundaries stay explicit.
- Cross-repository decisions have a stable review location.
- Integration tests can validate ecosystem behavior without moving runtime logic.
- Private planning can stay private while public repositories remain focused.

Negative:

- Changes spanning repositories require disciplined documentation updates.
- Integration tests depend on compatible versions of multiple repositories.
- The platform repository needs active maintenance to avoid becoming stale.

Follow-up:

- Define concrete contracts under `contracts/`.
- Establish integration test conventions.
- Populate `versions.yaml` as repositories publish compatible releases.
