# neuriplo platform

Architecture control plane for the neuriplo inference ecosystem.

This repository coordinates the boundaries, contracts, decisions, version
compatibility, integration tests, and end-to-end examples across:

- [`neuriplo-tasks`](https://github.com/olibartfast/neuriplo-tasks): domain and task layer
- [`neuriplo`](https://github.com/olibartfast/neuriplo): backend abstraction layer
- [`neuriplo-infer`](https://github.com/olibartfast/neuriplo-infer): local application layer
- [`neuriplo-kserve-client`](https://github.com/olibartfast/neuriplo-kserve-client): standalone KServe V2 protocol client library (v0.2.0, backend-agnostic HTTP/gRPC client with retry, TLS, auth, model repository extension) consumed by `neuriplo-infer`
- [`neuriplo-kserve-runtime`](https://github.com/olibartfast/neuriplo-kserve-runtime): serving and runtime layer (WIP - commit-pinned, not yet tagged)
- [`videocapture`](https://github.com/olibartfast/videocapture): video and image source layer consumed by `neuriplo-infer`

Secondary consumers tracked best-effort (not part of the ecosystem build or
version matrix):

- [`neuriplo-ros`](https://github.com/olibartfast/neuriplo-ros): ROS integration
- [`tritonic`](https://github.com/olibartfast/tritonic): Triton-oriented client
- [`ghostgrid`](https://github.com/olibartfast/ghostgrid): agentic LLM/VLM
  workflow framework (see ADR 0007)

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
neuriplo-kserve-client  = standalone KServe V2 protocol client library (consumed by neuriplo-infer)
neuriplo-kserve-runtime = serving/runtime layer (WIP, commit-pinned)
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
