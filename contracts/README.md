# Contracts

This directory describes cross-repository contracts. A contract should define the
shape, ownership, compatibility expectations, and validation strategy for an
interface used across repositories.

## Initial Contract Areas

- [Task contract](task-contract.md): `neuriplo-tasks` input/output semantics
  consumed by applications and runtimes.
- [Backend contract](backend-contract.md): `neuriplo` execution interface
  consumed by local and serving runtimes.
- [Result contract](result-contract.md): typed inference outputs returned by
  tasks and rendered by applications.
- [Runtime contract](runtime-contract.md): KServe V2 request/response behavior
  for `neuriplo-kserve-runtime`.
- [Ensemble contract](ensemble-contract.md): encoded-image input and decoded
  result envelope for server-side ensembles, shared by
  `neuriplo-kserve-runtime` and Triton deployments.
- [Configuration contract](configuration-contract.md): shared configuration
  expectations across local and serving flows.
- [Event contract](event-contract.md): broker-published result event envelope
  produced by `neuriplo-infer` and observed by out-of-process consumers.
- [Error contract](error-contract.md): stable failure classification, owner
  assignment, retry policy, and transport status mapping for local and remote
  inference flows.
- [GPU capability contract](gpu-capability-contract.md): GPU device discovery,
  memory, compute capability, and topology surface reported by `neuriplo`
  backends.
- [Benchmarking contract](benchmarking-contract.md): throughput/latency
  benchmark expectations, reproducibility rules, and performance regression
  thresholds for compatibility sets.
- [Capability discovery contract](capabilities-contract.md): build-specific
  tasks, models, parameters, local backends, and client-server workflows
  produced by `neuriplo-infer` for `neuriplo-ui` and other tools.

## Contract Template

```text
Name
Owner
Consumers
Version
Purpose
Schema or API surface
Compatibility rules
Validation strategy
Examples
```
