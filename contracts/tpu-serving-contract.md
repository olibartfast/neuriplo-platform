# TPU Serving Contract

Owner: `neuriplo-platform` (contract definition); the operator of the deployed
TPU service owns the implementation.

Consumers: [`neuriplo-infer`](https://github.com/olibartfast/neuriplo-infer),
[`neuriplo-kserve-client`](https://github.com/olibartfast/neuriplo-kserve-client),
operators, integration tests

Status: Draft

## Purpose

Define the boundary for the first remote TPU representative: a TensorFlow
ResNet-50 classifier served from a Cloud TPU VM over KServe V2 / Open Inference
Protocol. TPU execution is remote serving. The client selects an endpoint and
model identity through the existing KServe client path and never links a TPU
runtime into the inference process.

This contract covers the classifier only. A new task family needs its own
artifact and tensor contract; do not overload this model.

## Service Responsibility and Trust Boundary

The TPU service owns:

- Loading and lifecycle of the model artifact.
- Device placement on TPU chips and cores.
- The compiler and runtime stack, including TensorFlow, XLA, StableHLO, and
  `libtpu` versions and flags.
- Request admission, batching, and concurrency.
- The required HTTP transport and any optional gRPC transport.
- Health and readiness endpoints.
- Error responses that map to [error-contract.md](error-contract.md).
- Transport security, authentication, and network exposure.

The client owns:

- Endpoint, model name, model version, and transport selection through the
  existing KServe client configuration described in
  [configuration-contract.md](configuration-contract.md).
- Task preprocessing that produces the raw BGR tensor described below.
- Client-side softmax and top-k over the returned logits.
- Mapping transport failures to the shared error classification.

The trust boundary is the KServe V2 wire surface:

- The service is an external process, outside `neuriplo-infer` and outside
  [`neuriplo-kserve-runtime`](https://github.com/olibartfast/neuriplo-kserve-runtime).
  No TPU runtime or model weights are shipped by the client.
- The client trusts only the tensor contract, health semantics, error mapping,
  and model metadata defined here.
- The client must not trust service logs, internal metrics, device names, or
  implementation-specific fields, and must not infer TPU generation or topology
  from a response.
- The service must not assume the client performs TPU-specific preprocessing or
  supplies device hints.
- Credentials and endpoint authorization remain in the existing client
  configuration; this contract defines no new authentication field.

## Transport

```text
HTTP:  required
gRPC:  optional
```

Both transports use the standard KServe V2 protocol. HTTP is the
interoperability floor: a service that omits gRPC is conformant, and a client
configured for HTTP must work without gRPC support.

## Endpoint Paths

HTTP endpoints:

```text
GET  /v2
GET  /v2/health/live
GET  /v2/health/ready
GET  /v2/models/<model_name>
GET  /v2/models/<model_name>/ready
GET  /v2/models/<model_name>/versions/<version>
GET  /v2/models/<model_name>/versions/<version>/ready
POST /v2/models/<model_name>/infer
POST /v2/models/<model_name>/versions/<version>/infer
```

Optional gRPC methods on `GRPCInferenceService`:

```text
ServerMetadata
ServerLive
ServerReady
ModelMetadata
ModelReady
ModelInfer
```

`/v2` and the server health endpoints are the minimum discovery surface.
Per-model metadata and readiness are authoritative for request routing.

## Health and Readiness

```text
server live:   process is serving and can answer HTTP requests;  HTTP 200
server ready:  at least one model can accept inference;          HTTP 200
model ready:   that model is loaded and device initialization
               completed;                                        HTTP 200
```

A non-200 response means not ready. Readiness must not report success before
the model artifact is loaded and the TPU runtime is initialized. Liveness must
not depend on model readiness: a process that is live but has no ready model is
still live and reports not-ready on the readiness endpoints.

Clients must gate traffic on per-model readiness. An inference request sent to
a not-ready model may fail; the failure maps to `BACKEND_UNAVAILABLE` until the
model is ready, not to a successful empty response.

## Model Artifact and Version Naming

```text
model_name:     operator-registered, stable, opaque to the client; for the
                first representative an example is resnet50_tf_tpu
model_version:  decimal integer string ("1", "2", ...); omitted selects the
                server default; a published version is immutable
artifact:       a TensorFlow SavedModel exported for the tensorflowclassifier
                task; it is server-owned and never shipped by the client
```

The concrete model name and version used for evidence must be recorded in the
runbook and compatibility set. Renaming a model or mutating a published version
is a breaking change; publish a new name or version instead.

## Tensor Contract

```text
input:   name "image"
         datatype FP32
         shape [1, 224, 224, 3] on the wire (batch 1)
         layout NHWC
         content contiguous Float32 raw BGR pixels in [0, 255]

output:  semantic name "logits"
         datatype FP32
         shape [1, 1000] on the wire (batch 1)
         content raw ImageNet-1k class logits in class-index order
         count: exactly one output tensor per response
         wire name: metadata is authoritative; the name is not used for
                    result selection
```

The output is semantically logits, Float32 `[1,1000]`, and each response must
contain exactly one output tensor. The client consumes classifier outputs
positionally and does not use tensor names to select among them, so auxiliary
outputs, additional outputs, or reordered outputs are outside this contract. The
single output's wire name is not fixed: the first Keras 3 export names it
`output_0`, while a hand-built export may use `logits`. Clients read the one
advertised name from per-model metadata, which is needed only to frame
binary-mode outputs, and must not hardcode `logits` for result selection.

Request and response use the standard KServe V2 tensor encoding. A conforming
HTTP exchange has this logical shape:

```json
{
  "inputs": [
    {
      "name": "image",
      "shape": [1, 224, 224, 3],
      "datatype": "FP32",
      "data": [0.0, 0.0, 0.0]
    }
  ]
}
```

The `data` array above is abbreviated; it carries 150528 Float32 values. The
KServe binary-data extension is allowed, but the bytes must be contiguous,
little-endian Float32 in NHWC order with no padding.

A conforming response has this logical shape:

```json
{
  "model_name": "resnet50_tf_tpu",
  "model_version": "1",
  "outputs": [
    {
      "name": "output_0",
      "shape": [1, 1000],
      "datatype": "FP32",
      "data": [0.0]
    }
  ]
}
```

The `data` array above is abbreviated; it carries 1000 Float32 logits. The
`output_0` name is illustrative of the first Keras 3 export; the actual single
output name comes from model metadata. A response with zero, multiple, or
reordered outputs violates this contract.

### Input Semantics

- The client resizes the image to 224x224 and keeps it in BGR channel order.
- Pixel values stay in `[0, 255]`; the client does not apply ImageNet mean/std
  normalization or divide by 255.
- The artifact graph performs the ResNet BGR mean subtraction. The service must
  not add a second normalization, resize, or channel conversion.
- Every request carries batch 1: the wire input is `[1, 224, 224, 3]` and the
  wire output is `[1, 1000]`. Model metadata may advertise a dynamic batch axis
  (`-1` in KServe metadata, `None` in a SavedModel signature) and a
  `max_batch_size` of 1 or greater; a service configured that way must still
  accept a batch-1 request. This contract requires and validates batch 1 only;
  larger request batches are outside it.
- A request with a different rank, shape, or layout is rejected with
  `INVALID_TENSOR_SHAPE`. A request with a non-FP32 datatype is rejected with
  `UNSUPPORTED_DTYPE`.

### Output Semantics

- The response contains exactly one output tensor; auxiliary or reordered
  outputs are not part of this contract.
- The service returns raw logits, not probabilities or class labels.
- The client applies softmax once and computes top-k with the existing
  classification postprocessing in
  [`neuriplo-tasks`](https://github.com/olibartfast/neuriplo-tasks).
- A service that returns probabilities, top-k labels, or a different class
  count is a different model contract and must be published under a new model
  name or version.
- Class indices align with the ImageNet-1k label list selected by the client's
  labels file.

## Error Mapping

Failures use the stable codes in [error-contract.md](error-contract.md). That
contract assigns each code an owner drawn from the local repositories because it
describes local components. This service runs outside those repositories, so the
error envelope's `owner` field is overridden here: for a failure produced by the
external service, `owner` is the operator-supplied service identity recorded in
the runbook (for example the deployed service or image name), never a local
repository. A client that detects a pre-flight failure locally, for example a
`VERSION_MISMATCH` against the platform compatibility set before any request,
keeps the owner from [error-contract.md](error-contract.md).

The mapping below is the minimum for this service:

| Condition | Code | Owner | HTTP | gRPC |
|---|---|---|---:|---|
| Unknown model name or version | `MODEL_NOT_FOUND` | service/operator | 404 | `NOT_FOUND` |
| Artifact load or device initialization failed | `MODEL_LOAD_FAILED` | service/operator | 500 | `INTERNAL` |
| TPU runtime or device became unavailable after load | `BACKEND_UNAVAILABLE` | service/operator | 503 | `UNAVAILABLE` |
| Rank, shape, or layout violates the tensor contract | `INVALID_TENSOR_SHAPE` | service/operator | 400 | `INVALID_ARGUMENT` |
| Datatype is not FP32 | `UNSUPPORTED_DTYPE` | service/operator | 400 | `INVALID_ARGUMENT` |
| Deadline elapsed before a response completed | `REQUEST_TIMEOUT` | service/operator or client | 504 | `DEADLINE_EXCEEDED` |
| Version does not match a promoted compatibility set | `VERSION_MISMATCH` | service/operator or platform | 409 | `FAILED_PRECONDITION` |

Do not invent TPU-specific error codes. Accelerator memory exhaustion during
load maps to `MODEL_LOAD_FAILED`; at runtime it maps to
`BACKEND_UNAVAILABLE`. The message or `details` may identify the accelerator.
If the service implements admission control, `QUEUE_FULL` keeps its existing
meaning.

## Explicit Non-Assumptions

The client must not assume any of the following about the service:

- TPU generation, chip count, topology, or single-host versus multi-host
  placement.
- TensorFlow, XLA, StableHLO, or `libtpu` version, compiler flags, or
  compilation-cache behavior.
- Whether the service uses PJRT or any particular execution path internally.
- Batching behavior beyond the `max_batch_size` advertised in model metadata.
- Any server-side preprocessing, postprocessing, softmax, top-k, or label
  resolution.
- A specific server implementation. `neuriplo-kserve-runtime` is not required;
  any conforming KServe V2 service is acceptable.
- Availability of gRPC, metrics endpoints, logs, or non-standard discovery
  fields.
- That `device`, `precision`, or `use_gpu` fields are sent or honored; they are
  local-only configuration and are not part of this wire contract.

No in-process PJRT, XLA, StableHLO, or `libtpu` surface is added to
`neuriplo-infer` by this contract. TPU execution remains outside the client
process.

## Compatibility Rules

- Adding optional metadata or endpoints is backward compatible.
- Adding gRPC is backward compatible. Removing HTTP or requiring gRPC without
  an HTTP path is breaking.
- Changing the input tensor name, dtype, rank, shape, layout, channel order, or
  pixel range is breaking.
- Changing the output tensor dtype, shape, or class count is breaking.
- Renaming the single wire output tensor is backward compatible because clients
  read its name from model metadata only for framing and select the sole output
  positionally; the semantic output must remain raw logits.
- Adding, removing, or reordering outputs, or returning more than one output, is
  breaking.
- Changing the output from logits to probabilities or precomputed top-k is
  breaking.
- Renaming a model or mutating a published version is breaking. Publish a new
  name or version instead.
- Changing readiness semantics so that traffic is accepted before the artifact
  is loaded, or changing a documented error mapping, is breaking.
- Changing TPU generation, compiler, or runtime behind the service is backward
  compatible when the tensor, health, error, and naming contracts still hold.
- Changing the batch-1 wire shapes is breaking. Advertising a dynamic batch axis
  or a `max_batch_size` greater than 1 while still accepting batch 1 is backward
  compatible.
- A new task family requires a new tensor contract; reusing this classifier
  contract for a different task is breaking.

## Validation Strategy

- `neuriplo-tasks` validates the export in CPU metadata mode (input and output
  names, dtypes, ranks, shapes) and records a TPU execution run with the exact
  TPU type, runtime versions, command, and expected top-5 output.
- `neuriplo-infer` exercises the KServe client path against the service and
  checks output datatype and shape, then compares top-k classes and scores with
  a CPU baseline at documented tolerance. Bitwise parity is not required.
- This repository validates that the contract, configuration contract, and
  architecture note describe the same boundary, and that relative links resolve
  and platform text stays ASCII.
- Negative-path checks cover an unknown model (`MODEL_NOT_FOUND`), malformed
  shape or layout (`INVALID_TENSOR_SHAPE`), non-FP32 datatype
  (`UNSUPPORTED_DTYPE`), and a not-ready model (readiness non-200, inference
  `BACKEND_UNAVAILABLE`).
- gRPC checks run only when the service advertises gRPC. HTTP is always tested.
- TPU evidence requires exact commands, hardware, runtime versions, expected
  output, and teardown notes. Metadata-only evidence is not a TPU pass.

## Relationship to Other Contracts

- [configuration-contract.md](configuration-contract.md): selects the remote
  service by endpoint, model name, version, and transport. `device` and
  `use_gpu` remain local-only.
- [error-contract.md](error-contract.md): defines the stable codes and retry
  policy referenced above.
- [task-contract.md](task-contract.md): the domain-level task interface that
  reserves serving semantics. The concrete TensorFlow classifier input/output
  behavior is owned by the `2026-11-09-tensorflow-gpu-remote-tpu` packet in
  [`neuriplo-tasks`](https://github.com/olibartfast/neuriplo-tasks); this tensor
  contract mirrors that export.
- [result-contract.md](result-contract.md): owns typed classification results
  after client-side postprocessing.
