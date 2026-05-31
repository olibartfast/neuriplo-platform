# Task Contract

Owner: `vision-core`

Consumers: `vision-inference`, `neuriplo-kserve-runtime`, integration tests

Status: Draft

## Purpose

Define the domain-level interface for a vision task independent of the backend
used to execute inference.

## Responsibilities

`vision-core` owns:

- Task identity and supported task types.
- Input normalization requirements.
- Preprocessing behavior.
- Postprocessing behavior.
- Typed result structures.
- Model-family-specific task logic.

Consumers may:

- Select a task by stable task identifier.
- Provide supported inputs.
- Receive typed results.
- Inspect task metadata needed for wiring or display.

Consumers must not:

- Reimplement preprocessing or postprocessing.
- Depend on private model internals.
- Treat backend-specific tensors as the public task result.

## Compatibility Rules

- Adding optional task metadata is backward compatible.
- Adding a new task type is backward compatible when existing task identifiers
  are unchanged.
- Renaming task identifiers is breaking.
- Changing result semantics for an existing result field is breaking.
- Adding required input fields is breaking unless guarded by a new contract
  version.

## Validation Strategy

- Unit tests in `vision-core` validate task behavior.
- Integration tests in this repository validate task execution through local and
  serving runtimes.
- Example fixtures should cover at least one representative input and output per
  public task type.
