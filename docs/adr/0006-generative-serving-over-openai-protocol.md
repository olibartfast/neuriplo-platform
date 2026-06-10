# ADR 0006: Serve generative tasks over OpenAI-compatible endpoints, keep predictive tasks on KServe V2

Date: 2026-06-10

Status: Proposed

## Problem

`neuriplo-tasks` includes `ImageUnderstandingTask`, which routes a text prompt
(and optionally an image) through an LLM/VLM backend such as llama.cpp. In
embedded local mode this works: preprocess packs the prompt into raw UTF-8
bytes, and postprocess decodes the backend's float-cast response bytes back
into a string.

Carrying that same encoding onto the remote serving path forces text
generation through the KServe V2 tensor protocol, which gives up:

- token streaming (V2 has no SSE/streaming semantics),
- sampling parameters and chat-message semantics,
- prefix/KV-cache reuse across agent-loop calls that re-send growing prompts,
- compatibility with the OpenAI-style clients that LLM consumers already have.

Upstream KServe has meanwhile split its data plane into two tracks:

```text
predictive AI:  V1 protocol and V2 Open Inference Protocol (/infer, gRPC)
generative AI:  OpenAI-compatible endpoints (/v1/chat/completions,
                /v1/completions, /v1/embeddings) with SSE streaming,
                served by vLLM-first runtimes
```

We need to decide how the neuriplo ecosystem serves generative output
remotely.

## Constraints

- `neuriplo-kserve-runtime` is WIP and scoped to the KServe V2 protocol;
  the ecosystem's serving differentiation is the predictive/CV track.
- llama.cpp already ships `llama-server`, an OpenAI-compatible HTTP server
  for the same GGUF models the embedded backend loads.
- KServe's own generative runtimes (vLLM, HuggingFace fallback) already
  provide OpenAI-compatible serving at scale; reimplementing continuous
  batching, prefix caching, and streaming inside `neuriplo-kserve-runtime`
  would duplicate them without differentiation.
- Embedded local mode in `neuriplo-infer` must keep working unchanged on
  CPU/edge targets with no server dependency.
- The result contract requires that consumers never treat backend raw
  outputs as public results.

## Options

1. Status quo: serve `image_understanding` over V2 tensors with the
   float-cast-bytes text encoding.
2. Implement an OpenAI-compatible facade inside `neuriplo-kserve-runtime`
   alongside the V2 endpoints.
3. Split by track: predictive tasks stay on V2 via `neuriplo-kserve-client`
   and `neuriplo-kserve-runtime`; generative tasks keep embedded llama.cpp
   for local/edge mode and are exposed remotely through existing
   OpenAI-compatible servers (`llama-server` for GGUF models, or a
   vLLM-backed KServe deployment), not through `neuriplo-kserve-runtime`.

## Decision

Option 3. The protocol follows the inference track, matching the upstream
KServe data-plane split:

- Predictive tasks (detection, segmentation, classification, pose, depth,
  open-vocabulary detection, optical flow) are served over the KServe V2
  Open Inference Protocol. No change.
- Generative tasks (`image_understanding`) remain embedded llama.cpp in
  local mode. Remote generative serving delegates to an OpenAI-compatible
  endpoint; `neuriplo-kserve-runtime` does not grow an LLM serving path.
- The V2 float-cast-bytes text encoding is demoted to an internal detail of
  the embedded backend boundary. It is not a public serving contract, and
  no remote consumer may depend on it.

## Consequences

Positive:

- Remote generative consumers (agent frameworks, gateways, standard SDKs)
  integrate with zero custom protocol code and get streaming, sampling
  parameters, and chat semantics for free.
- Agent-loop workloads gain prefix caching on vLLM-backed deployments,
  which the V2 tensor path cannot offer.
- `neuriplo-kserve-runtime` keeps a single protocol and a focused scope;
  the ecosystem does not compete with vLLM/KServe on LLM serving.

Negative:

- Remote generative mode depends on a third-party server (`llama-server`
  or vLLM) being deployed and operated alongside the predictive runtime.
- The platform now documents two serving protocols, and contracts must say
  clearly which tasks ride which track.
- If `neuriplo-infer` ever needs remote generative inference, it requires
  an OpenAI-compatible client path; until then remote `image_understanding`
  is out of scope for `neuriplo-kserve-client`.

Follow-up:

- Record the track-to-protocol mapping in `contracts/task-contract.md` and
  note the demotion of the float-cast-bytes encoding in
  `contracts/result-contract.md`.
- Add an example under `examples/` that serves a GGUF model with
  `llama-server` and consumes it through the OpenAI protocol.
- Keep `versions.yaml` unchanged; third-party generative servers are
  deployment dependencies, not version-matrix members.
