# Inference Modes

`neuriplo-infer` supports two architecture modes for inference. Accelerator
choice does not add a third mode: GPU and CPU are local execution choices inside
embedded local mode, and TPU is a remote serving choice inside the KServe client
mode. The dependency boundary depends on which mode is being built and
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

## Remote TPU Serving

Remote TPU inference is not a third architecture mode. It is a service
implementation inside remote KServe client mode: `neuriplo-infer` uses the same
KServe client wiring and sends tensors to a TPU-side KServe V2 service.

```text
CLI/config
  |
  v
neuriplo-infer (KServe client wiring: KserveEngine adapter)
  |
  v
neuriplo-kserve-client (KServe V2 HTTP required, gRPC optional)
  |
  v
Cloud TPU host: KServe V2 service
  |
  '- TPU device and TensorFlow runtime (service-owned)
```

The first representative is a TensorFlow ResNet-50 classifier that accepts raw
BGR pixels and returns logits. `neuriplo-infer` selects the service by endpoint,
model name, version, and transport; it does not select a TPU device. The TPU
service owns device placement, the compiler, runtime, batching, model lifecycle,
readiness, and error responses. The client owns image preprocessing, client-side
softmax, and top-k after the logits return.

```text
input:   Float32 NHWC [1, 224, 224, 3], raw BGR pixels in [0, 255]
output:  Float32 logits [1, 1000]
```

The full wire boundary, readiness rules, naming, and error mapping live in
[tpu-serving-contract.md](../../contracts/tpu-serving-contract.md). The export
and validation recipe live in the `2026-11-09-tensorflow-gpu-remote-tpu` packet
in [`neuriplo-tasks`](https://github.com/olibartfast/neuriplo-tasks), and the
end-to-end remote harness lives in the matching packet in
[`neuriplo-infer`](https://github.com/olibartfast/neuriplo-infer).

`device` and `use_gpu` remain local-only fields. They describe hardware owned by
the local process and never name a remote TPU. Remote TPU serving adds no
in-process PJRT, XLA, StableHLO, or `libtpu` dependency to `neuriplo-infer`.

## Boundary Rules

- Embedded local mode may depend directly on `neuriplo`.
- Remote KServe client mode must not depend on `neuriplo` backend internals.
- Remote TPU serving is reached only through the KServe client path. It adds no
  local backend, `device` value, or in-process PJRT/XLA/StableHLO/`libtpu`
  dependency.
- `device` and `use_gpu` remain local-only; they never address a remote TPU
  service.
- TPU service compatibility is governed by
  [tpu-serving-contract.md](../../contracts/tpu-serving-contract.md) and model
  metadata, not by TPU generation, compiler version, or server implementation.
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
