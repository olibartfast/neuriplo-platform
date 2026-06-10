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
- [Configuration contract](configuration-contract.md): shared configuration
  expectations across local and serving flows.
- [Event contract](event-contract.md): broker-published result event envelope
  produced by `neuriplo-infer` and observed by out-of-process consumers.

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
