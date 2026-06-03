# vision-platform Modern C++ Pattern Review

Reviewed on: 2026-06-03

Remote: https://github.com/olibartfast/vision-platform

Reviewed ref: `main`

Branch note: no remote `develop` branch was visible through `gh` during this
review.

## Scope

This review considers the architecture/control-plane repository against the
modern pattern guidance. This repository should document ownership, contracts,
compatibility, and integration expectations rather than containing runtime
implementation.

Key files inspected locally and remotely with `gh`:

- `README.md`
- `versions.yaml`
- `docs/architecture/overview.md`
- `contracts/*.md`
- `ops/repo-meta/*.yaml`

## Pattern Alignment

- The repository correctly separates platform contracts from runtime code.
- Contracts document owners and consumers for task, backend, result, runtime,
  and configuration boundaries.
- `versions.yaml` gives a central known-good compatibility matrix.

## Findings

### Medium: Architecture docs lag the modern pattern taxonomy

`docs/architecture/overview.md` mostly lists GoF-style patterns. The new pattern
guidance should be reflected explicitly for this ecosystem: Composition Root,
Pipeline, Producer-Consumer, Queue Worker, Dynamic Batching, Object Pool, RAII,
Adapter / Anti-Corruption Layer, Timeout, Retry, Bulkhead, Health Endpoint, and
Idempotent Consumer.

Recommendation: update the architecture overview or add a dedicated pattern
guide under `docs/architecture/`.

### Medium: `tritonic` is a known consumer but not first-class in platform metadata

`vision-core` metadata lists `tritonic` as a consumer, but `tritonic` is not in
`versions.yaml` or the main ownership map.

Recommendation: either add `tritonic` as a tracked repository or remove it from
consumer metadata if it is outside the platform control-plane scope.

### Low: Serving runtime branch policy differs from the rest

Most implementation repositories expose `develop` as the integration branch.
`neuriplo-kserve-runtime` did not expose `develop` or `dev` during this review
and currently appears to use `master`.

Recommendation: update platform metadata to reflect the actual branch policy, or
create the expected integration branch in the runtime repository.

## Source Taxonomy Mapping

The platform should own documentation for the taxonomy rather than runtime
implementation. The relevant patterns are Compatibility Registry, ownership map,
ADR, Composition Root ownership, Anti-Corruption Layer boundaries, and serving
reliability patterns.

Status: `docs/architecture/modern-patterns.md` now covers the taxonomy from the
source article and links from `docs/architecture/overview.md`. Remaining work is
policy: decide whether `tritonic` is tracked in the platform matrix and reconcile
`neuriplo-kserve-runtime` branch metadata.

## Recommended Next Actions

1. Add a modern-pattern architecture page based on the supplied pattern document.
2. Decide whether `tritonic` is part of the platform compatibility matrix.
3. Reconcile `neuriplo-kserve-runtime` branch metadata with the actual remote
   branch structure.
