# Inference Modes

`neuriplo-infer` supports two architecture modes. The dependency boundary depends
on which mode is being built and deployed.

## Embedded Local Mode

```text
CLI/config
  |
  v
neuriplo-infer
  |
  |- neuriplo-tasks: task preprocess and postprocess
  |- neuriplo: backend abstraction and execution
  '- videocapture: local image or video source handling
```

In this mode `neuriplo-infer` is built with direct dependencies on
`neuriplo-tasks`, `neuriplo`, and `videocapture`. It is the composition root for
local inference and runs on the same machine as the backend runtime and model
artifacts.

Use this mode when the goal is a local executable, local model access, and direct
backend execution without a client/server boundary.

## Remote KServe Client Mode

```text
CLI/config
  |
  v
neuriplo-infer KServe V2 client
  |
  v
KServe V2 endpoint
  |
  |- neuriplo-kserve-runtime -> neuriplo-tasks + neuriplo
  '- another KServe-compatible serving endpoint
```

In this mode `neuriplo-infer` is coupled to the KServe V2 client protocol, not to
`neuriplo` backend internals. The server owns model loading, task/backend wiring,
queueing, scheduling, batching, and operational behavior.

`neuriplo-kserve-runtime` is one compatible server implementation. The same
client path should also be usable with other KServe-compatible endpoints, such as
Triton Inference Server or OpenVINO Model Server, subject to model metadata and
tensor schema compatibility.

Use this mode when the goal is remote inference, service isolation, independent
server deployment, or compatibility with non-Neuriplo KServe endpoints.

## Boundary Rules

- Embedded local mode may depend directly on `neuriplo`.
- Remote KServe client mode must not depend on `neuriplo` backend internals.
- `neuriplo-kserve-runtime` may depend on `neuriplo`; it owns that server-side
  composition.
- KServe client compatibility is governed by the runtime contract and model
  metadata, not by the concrete server implementation.
- Platform tests should cover both paths when a compatibility set claims support
  for both local and remote inference.
