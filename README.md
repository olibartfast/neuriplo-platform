# neuriplo platform

Architecture control plane for a GPU-first AI inference serving ecosystem.

Neuriplo Platform validates cross-repository compatibility between:

- task contracts
- backend execution
- local inference applications
- KServe V2 clients
- KServe-compatible serving runtime
- video/image source layers

It publishes version sets, integration evidence, benchmark baselines,
failure-mode expectations, and architecture decisions across:

- [`neuriplo-tasks`](https://github.com/olibartfast/neuriplo-tasks): domain and task layer (CV tasks as first domain)
- [`neuriplo`](https://github.com/olibartfast/neuriplo): GPU-first backend abstraction layer and backend capability reporting
- [`neuriplo-infer`](https://github.com/olibartfast/neuriplo-infer): local and remote inference application layer, including benchmark scenario execution
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

## Getting Started

New contributor? Start with [CONTRIBUTING.md](CONTRIBUTING.md) -- it covers
bootstrapping, validation, and what to read first.

Core reference:

- [Architecture overview](docs/architecture/overview.md)
- [ADR index](docs/adr/README.md)
- [Contract index](contracts/README.md)
- [Version matrix](versions.yaml)
- [Example scenarios](examples/README.md)
- [Integration tests and validated model matrix](integration-tests/README.md)
