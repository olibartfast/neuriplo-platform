# neuriplo platform

Architecture control plane for the neuriplo inference ecosystem.

This repository coordinates the boundaries, contracts, decisions, version
compatibility, integration tests, and end-to-end examples across:

- `neuriplo-tasks`: domain and task layer
- `neuriplo`: backend abstraction layer
- `neuriplo-infer`: local application layer
- `neuriplo-kserve-client`: KServe V2 protocol client layer (backend-agnostic HTTP/gRPC client) consumed by `neuriplo-infer`
- `neuriplo-kserve-runtime`: serving and runtime layer (WIP / TODO - commit-pinned, not yet released)
- `videocapture`: video and image source layer consumed by `neuriplo-infer`

It should not contain runtime business logic, model-specific implementation,
backend execution code, or serving implementation code. Those responsibilities
remain in their owning repositories.

## Repository Layout

```text
neuriplo-platform/
|- docs/
|   |- architecture/
|   `- adr/
|- contracts/
|- examples/
|- integration-tests/
|- ops/
|- docker/
`- versions.yaml
```

## Operating Model

For every major platform change:

1. Write an ADR.
2. Update or add the target architecture documentation.
3. Implement the smallest viable version in the owning repository.
4. Add focused tests in the owning repository and integration coverage here.
5. Update contracts, examples, and the version matrix.

## Ownership

```text
neuriplo-tasks          = domain/task layer
neuriplo                = backend abstraction layer
neuriplo-infer          = local application layer
neuriplo-kserve-client  = KServe V2 protocol client layer (consumed by neuriplo-infer)
neuriplo-kserve-runtime = serving/runtime layer (WIP / TODO)
videocapture            = video/image source layer
neuriplo-platform       = architecture control plane
```

## Start Here

- [Architecture overview](docs/architecture/overview.md)
- [Production architecture roadmap](docs/architecture/production-roadmap.md)
- [Ownership model](docs/architecture/ownership.md)
- [ADR index](docs/adr/README.md)
- [Contract index](contracts/README.md)
- [Version matrix](versions.yaml)
- [Maintenance control plane](ops/README.md)
- [Documentation migration plan](docs/architecture/doc-migration.md)
- [Dependency policy](docs/architecture/dependency-policy.md)
- [Examples](examples/README.md)
