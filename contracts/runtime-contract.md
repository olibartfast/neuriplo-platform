# Runtime Contract

Owner: `neuriplo-kserve-runtime`

Consumers: KServe clients, deployment automation, integration tests

Status: Draft

## Purpose

Define serving runtime behavior for model loading, request admission, scheduling,
inference execution, and operational endpoints. Remote `neuriplo-infer` usage is
coupled to the KServe V2 protocol surface; the concrete server may be
`neuriplo-kserve-runtime` or another compatible endpoint.

## Responsibilities

`neuriplo-kserve-runtime` owns:

- KServe V2 protocol handling.
- Request validation and admission.
- Scheduling and dynamic batching.
- Model lifecycle.
- Pipeline (ensemble) models: a graph of preprocess, model, and postprocess
  steps served as one model. See [ensemble-contract.md](ensemble-contract.md)
  for the wire surface and ADR 0011 for the decision.
- Health and readiness endpoints.
- Metrics and operational status.

Consumers may:

- Submit requests using the supported KServe V2 surface.
- Use `neuriplo-infer` as a KServe V2 client without depending on `neuriplo`
  backend internals.
- Observe model readiness.
- Query operational endpoints.
- Depend on documented error responses.

Consumers must not:

- Depend on undocumented scheduler internals.
- Assume every KServe V2 endpoint is implemented by `neuriplo-kserve-runtime`.
- Assume batching behavior beyond the public configuration contract.
- Infer model lifecycle state from implementation-specific logs.

## Compatibility Rules

- Adding optional endpoints or metadata is backward compatible.
- Adding a model kind (for example `pipeline`) is backward compatible; existing
  single-model behavior must not change.
- Pipeline models never batch: `max_batch_size` is 1 by contract.
- Changing documented request or response shape is breaking.
- Changing admission failure semantics is breaking when clients can observe the
  difference.
- Scheduler changes are compatible when public latency, ordering, and response
  contracts remain intact.

## Validation Strategy

- Runtime component tests live in `neuriplo-kserve-runtime`.
- Cross-repository protocol tests live in this repository.
- Integration tests should include healthy, invalid-request, not-ready, and
  overloaded-request scenarios.
