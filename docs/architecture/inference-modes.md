# Inference Modes

`neuriplo-infer` supports two architecture modes for GPU-accelerated and CPU
inference. The dependency boundary depends on which mode is being built and
deployed.

`neuriplo-ui` sits above both modes through the same process boundary:

```text
browser -> neuriplo-ui local adapter -> neuriplo-infer
```

The UI first selects `local` or `client_server` from the binary's capability
payload. A local backend is selected only inside the `local` workflow. KServe
V2 is a protocol choice inside `client_server`, never a local backend.

## Embedded Local Mode

```text
CLI/config
  |
  v
neuriplo-infer
  |
  |- neuriplo-tasks: task preprocess and postprocess (CV tasks as first domain)
  |- neuriplo: GPU-first backend abstraction and execution (CUDA, TensorRT, ONNX Runtime, OpenVINO)
  '- videocapture: local image or video source handling (optional, CV-domain only)
```

In this mode `neuriplo-infer` is built with direct dependencies on
`neuriplo-tasks`, `neuriplo`, and optionally `videocapture`. It is the composition
root for local inference and runs on the same machine as the GPU backend runtime
and model artifacts.

Use this mode when the goal is a local executable, direct GPU backend access,
and direct backend execution without a client/server boundary.

## Remote KServe Client Mode

```text
CLI/config
  |
  v
neuriplo-infer (KServe client wiring: KserveEngine adapter)
  |
  v
neuriplo-kserve-client (backend-agnostic KServe V2 protocol client, HTTP/gRPC)
  |
  v
KServe V2 endpoint
  |
  |- neuriplo-kserve-runtime -> neuriplo-tasks + neuriplo
  '- another KServe-compatible serving endpoint
```

In this mode `neuriplo-infer` is coupled to the KServe V2 client protocol, not to
`neuriplo` backend internals. The wire protocol itself is implemented in the
standalone `neuriplo-kserve-client` library (consumed via FetchContent); only the
`KserveEngine` adapter that maps protocol bytes to the neuriplo inference contract
lives in `neuriplo-infer`. The server owns model loading, GPU placement, task/backend wiring, queueing,
scheduling, batching, GPU health reporting, and operational behavior.

`neuriplo-kserve-runtime` is one compatible server implementation. The same
client path should also be usable with other KServe-compatible endpoints, such as
Triton Inference Server or OpenVINO Model Server, subject to model metadata and
tensor schema compatibility.

Use this mode when the goal is remote inference, service isolation, independent
server deployment, or compatibility with non-Neuriplo KServe endpoints.

## Boundary Rules

- Embedded local mode may depend directly on `neuriplo`.
- Remote KServe client mode must not depend on `neuriplo` backend internals.
- `neuriplo-kserve-client` must stay backend-agnostic (raw tensor bytes, no
  `neuriplo` dependency) so it remains reusable by any KServe V2 consumer.
- `neuriplo-kserve-runtime` may depend on `neuriplo`; it owns that server-side
  composition.
- KServe client compatibility is governed by the runtime contract and model
  metadata, not by the concrete server implementation.
- Platform tests should cover both paths when a compatibility set claims support
  for both local and remote inference.
- `neuriplo-ui` must discover workflow/backend/protocol availability from
  `neuriplo-infer`; it must not maintain a parallel registry.
