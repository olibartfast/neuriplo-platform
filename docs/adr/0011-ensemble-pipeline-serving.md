# ADR 0011: Serve ensembles as a native runtime pipeline model kind

Date: 2026-08-04

Status: Proposed

## Problem

Today every consumer of
[`neuriplo-kserve-runtime`](https://github.com/olibartfast/neuriplo-kserve-runtime)
preprocesses on the client: decode the image, letterbox it, normalize it, and
send a dense FP32 NCHW tensor. The client also postprocesses: decode raw model
outputs through [`neuriplo-tasks`](https://github.com/olibartfast/neuriplo-tasks).
The server sees only an opaque tensor-in / tensor-out model.

That costs a full-resolution float tensor on the wire per request (a 640x640x3
FP32 tensor is 4.9 MB, roughly fifty times a typical JPEG), and it pins
preprocessing to the client's CPU even when the server has an idle GPU.

[`tritonic`](https://github.com/olibartfast/tritonic) v0.4.0 already solved this
against NVIDIA Triton: a Triton ensemble runs DALI GPU preprocessing, then
TensorRT, then optional DALI GPU postprocessing, and the client sends encoded
JPEG bytes. The client-facing contract that came out of that work is small and
transport-neutral -- an encoded-image input, an inner "task model" consulted for
task metadata, and a fixed decoded output envelope. The neuriplo stack has no
equivalent, so the same application cannot get server-side preprocessing from
our own runtime.

## Constraints

- `neuriplo-kserve-client` is deliberately a pure protocol peer. Its header
  states that nothing in it may depend on neuriplo or task types; that is what
  makes it a standalone peer of Triton's client library. Ensemble support must
  not change that.
- `neuriplo-kserve-runtime` currently links only `neuriplo`, the backend
  abstraction. It does not link `neuriplo-tasks`, so it has no letterbox, no
  JPEG decode, and no NMS.
- The layering recorded in `ops/CLUSTER_MAP.yaml` puts the serving runtime below
  the task layer. Preprocessing on the server inverts that for the steps that
  need task knowledge.
- We are not adopting Triton or DALI as a runtime dependency. Neither is
  available in the runtime's deployment targets, and the CUDA toolchain would
  dominate its build.
- The wire contract must stay compatible with what tritonic already emits, so an
  application can point at either server without a code change.

## Options

1. **Client-side only.** Teach `neuriplo-infer` to talk to a real Triton
   ensemble, and leave our runtime alone. Cheapest, but our runtime keeps
   forcing dense-tensor clients, and the capability stays locked to Triton
   deployments.
2. **Protocol parity without real chaining.** Have the runtime accept an
   encoded-image input and report `platform: ensemble`, but keep a single
   underlying model. Preserves the client contract, delivers the wire-size win,
   and delivers nothing on the compute-placement problem.
3. **Native pipeline model kind.** Give the runtime a real graph of steps --
   preprocess, model, postprocess -- with tensor routing between them, composed
   metadata, and the tritonic output envelope.

## Decision

Option 3.

`neuriplo-kserve-runtime` gains a `pipeline` model kind, loaded under the
backend name `ensemble`. A pipeline model is declared by a JSON graph of ordered
steps. `model` steps execute another model already in the runtime's registry;
`preprocess` and `postprocess` steps run `neuriplo-tasks` code in process.
The composed model exposes the first step's inputs and the last step's outputs
and reports `platform: ensemble`.

Three boundaries make this safe:

- **The client learns nothing.** `neuriplo-kserve-client` already carries
  `UINT8` inputs, `INT32`/`INT64`/`FP32` raw outputs, and a `platform` field. It
  gains conformance coverage for ensembles and nothing else. Decoding the
  envelope into task results stays in the `neuriplo-infer` adapter, where the
  task types already live.
- **The task dependency is optional.** `neuriplo-tasks` enters the runtime
  behind `NEURIPLO_RUNTIME_WITH_TASKS`, linking `neuriplo-tasks::vision-stb` for
  image decode and never `vision-opencv`, so the runtime stays OpenCV-free. Built
  `OFF`, the runtime is exactly what it is today and `preprocess`/`postprocess`
  steps refuse to load with an explicit message.
- **The wire contract is copied, not invented.** The encoded-image input and the
  output envelope are transcribed from tritonic v0.4.0 into
  [`contracts/ensemble-contract.md`](../../contracts/ensemble-contract.md), and
  both servers are validated against that one document.

Our built-in steps run on the CPU. tritonic's run on the GPU through DALI. Since
they agree on the envelope, a GPU step kind can be added later without any
client-visible change.

## Consequences

What improves:

- Requests carry an encoded image instead of a dense float tensor.
- Preprocessing placement becomes a deployment decision rather than an
  application rewrite.
- One documented envelope covers both our runtime and Triton, so
  `neuriplo-infer` has a single client-side code path for both.

What gets harder:

- The runtime's dependency graph grows, and with `NEURIPLO_RUNTIME_WITH_TASKS=ON`
  a task-layer change can break a serving build. The compatibility matrix in
  `versions.yaml` must now pin `neuriplo-tasks` for the runtime too.
- Model lifecycle gains an edge case: unloading a model that a loaded pipeline
  references. Pipelines resolve references at inference time and report
  `MODEL_NOT_READY`, rather than pinning referenced models alive.
- Dynamic batching does not apply to pipeline models. The contract fixes
  `max_batch_size: 1`, matching tritonic's encoded-image path.

Follow-up work:

- Runtime: graph config, `PipelineExecutor`, built-in steps, admission rules.
- Client: ensemble leg in the conformance oracle.
- `neuriplo-infer`: `--input_mode`, `--task_model`, `--postprocess_mode`, and
  the envelope decoder ported from tritonic.
- Platform: `integration-tests/kserve-ensemble/` asserting the ensemble path and
  the preprocessed path agree on the same image.
