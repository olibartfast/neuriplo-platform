# Configuration Contract

Owners: `vision-inference`, `neuriplo-kserve-runtime`, `neuriplo`

Consumers: CLI users, deployment automation, integration tests

Status: Draft

## Purpose

Define shared configuration expectations for selecting tasks, model artifacts,
backends, runtime behavior, and output handling.

## Responsibilities

Application and runtime repositories own their local configuration surfaces.
Shared fields that cross repository boundaries should be documented here.

Shared configuration areas:

- Task selection.
- Model artifact path or reference.
- Backend selection and backend capabilities.
- Device and precision preferences.
- Runtime batching and lifecycle options.
- Output serialization and visualization options.

## Compatibility Rules

- Adding optional configuration fields is backward compatible.
- Renaming fields is breaking.
- Changing defaults can be breaking when observable behavior changes.
- Backend-specific configuration must be namespaced or capability-gated.
- Serving-only configuration should not leak into local CLI contracts unless the
  local application consumes it.

## Validation Strategy

- Owning repositories validate local configuration parsing.
- This repository validates shared configuration examples against compatible
  repository versions.
- Example configurations should be versioned with `versions.yaml`.
