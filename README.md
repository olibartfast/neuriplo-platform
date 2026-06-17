# neuriplo platform

Architecture control plane for the neuriplo AI infrastructure and GPU-first
serving platform.

This repository coordinates the boundaries, contracts, decisions, version
compatibility, integration tests, and end-to-end examples across:

- [`neuriplo-tasks`](https://github.com/olibartfast/neuriplo-tasks): domain and task layer (CV tasks as first domain)
- [`neuriplo`](https://github.com/olibartfast/neuriplo): GPU-first backend abstraction layer
- [`neuriplo-infer`](https://github.com/olibartfast/neuriplo-infer): local application layer
- [`neuriplo-kserve-client`](https://github.com/olibartfast/neuriplo-kserve-client): standalone KServe V2 / Open Inference Protocol client library (backend-agnostic HTTP/gRPC client with retry, TLS, auth, model repository extension) consumed by `neuriplo-infer`
- [`neuriplo-kserve-runtime`](https://github.com/olibartfast/neuriplo-kserve-runtime): serving and runtime layer with dynamic batching, scheduling, and multi-GPU placement
- [`videocapture`](https://github.com/olibartfast/videocapture): video and image source layer consumed by `neuriplo-infer` (CV task domain only)

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
neuriplo-tasks          = domain/task layer (CV tasks as first domain)
neuriplo                = GPU-first backend abstraction layer
neuriplo-infer          = local application layer
neuriplo-kserve-client  = standalone KServe V2 / Open Inference Protocol client library (consumed by neuriplo-infer)
neuriplo-kserve-runtime = serving/runtime layer with dynamic batching, scheduling, multi-GPU placement
videocapture            = video/image source layer (CV task domain)
neuriplo-platform       = architecture control plane
```

## Start Here

- [Architecture overview](docs/architecture/overview.md)
- [Production architecture roadmap](docs/architecture/production-roadmap.md)
- [Ownership model](docs/architecture/ownership.md)
- [GPU hardware considerations](docs/architecture/gpu-hardware-considerations.md)
- [ADR index](docs/adr/README.md)
- [Contract index](contracts/README.md)
- [Version matrix](versions.yaml)
- [Maintenance control plane](ops/README.md)
- [Documentation migration plan](docs/architecture/doc-migration.md)
- [Dependency policy](docs/architecture/dependency-policy.md)
- [Examples](examples/README.md)
