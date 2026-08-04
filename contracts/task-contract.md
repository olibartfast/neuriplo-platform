# Task Contract

Owner: `neuriplo-tasks`

Consumers: `neuriplo-infer`, `neuriplo-kserve-runtime`, integration tests

Status: Draft

## Purpose

Define the domain-level interface for a task independent of the backend used to
execute inference. Computer vision is the first implemented task domain; ADR
0010 reserves additional domains for NLP, audio, tabular, multimodal, and
reinforcement-learning workloads.

## Responsibilities

`neuriplo-tasks` owns:

- Task domain identity.
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

A server-side ensemble is the one sanctioned way to obtain results without
running `neuriplo-tasks` preprocessing and postprocessing in the consumer: the
work still happens in this task layer, just inside the serving runtime, and it
reaches the consumer through the envelope in
[ensemble-contract.md](ensemble-contract.md). Decoding that envelope must
produce the same typed results as the local path -- it is a transport for task
results, not a second definition of them.

## Task Domains

Status by domain:

```text
cv          implemented first domain
nlp         reserved; first preferred pilot is embeddings
audio       reserved
tabular     reserved
multimodal  reserved
rl          tracked; out of scope for serving v1
```

Every shipped domain must define:

```text
task_type strings
input contract
result contract
serving protocol
batching semantics
streaming support
backend expectations
example configuration
```

## Serving Track

Predictive tensor tasks use KServe V2 / Open Inference Protocol for remote
serving. Current CV task families are on this track.

Generative chat/text tasks use OpenAI-compatible endpoints for remote serving.
`image_understanding` remains an embedded local task in `neuriplo-infer`; remote
serving delegates to an OpenAI-compatible server per ADR 0006.

Implementation-specific encodings inside embedded local mode are not public
serving contracts.

## Compatibility Rules

- Adding optional task metadata is backward compatible.
- Adding a new task type is backward compatible when existing task identifiers
  are unchanged.
- Adding a new task domain is backward compatible when existing domains are
  unchanged.
- Renaming task identifiers is breaking.
- Moving an existing task type to a different serving protocol is breaking
  unless covered by a versioned compatibility window.
- Changing result semantics for an existing result field is breaking.
- Adding required input fields is breaking unless guarded by a new contract
  version.

## Validation Strategy

- Unit tests in `neuriplo-tasks` validate task behavior.
- Integration tests in this repository validate task execution through local and
  serving runtimes.
- Example fixtures should cover at least one representative input and output per
  public task type.
