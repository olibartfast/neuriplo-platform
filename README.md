# neuriplo platform

Architecture control plane for the neuriplo inference ecosystem.

This repository coordinates the boundaries, contracts, decisions, version
compatibility, integration tests, and end-to-end examples across:

- `vision-core`: domain and task layer
- `neuriplo`: backend abstraction layer
- `vision-inference`: local application layer
- `neuriplo-kserve-runtime`: serving and runtime layer
- `videocapture`: video and image source layer consumed by `vision-inference`

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
vision-core             = domain/task layer
neuriplo                = backend abstraction layer
vision-inference        = local application layer
neuriplo-kserve-runtime = serving/runtime layer
videocapture            = video/image source layer
neuriplo-platform       = architecture control plane
```

## Start Here

- [Architecture overview](docs/architecture/overview.md)
- [Ownership model](docs/architecture/ownership.md)
- [ADR index](docs/adr/README.md)
- [Contract index](contracts/README.md)
- [Version matrix](versions.yaml)
- [Maintenance control plane](ops/README.md)
- [Documentation migration plan](docs/architecture/doc-migration.md)
- [Dependency policy](docs/architecture/dependency-policy.md)
- [Examples](examples/README.md)
