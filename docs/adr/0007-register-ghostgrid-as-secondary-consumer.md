# ADR 0007: Register ghostgrid as a secondary agentic consumer

Date: 2026-06-10

Status: Proposed

## Problem

[`ghostgrid`](https://github.com/olibartfast/ghostgrid) is a multi-provider
LLM/VLM agentic workflow framework (Python)
with sequential, parallel, conditional, iterative, Mixture-of-Agents, and
ReAct workflows, including tool-using vision agents. It wants to consume
neuriplo inference output in two ways:

- as an LLM provider: agents consume generative output from
  neuriplo-ecosystem models (llama.cpp GGUF, `image_understanding`), and
- as grounded tools: ReAct vision tools (`detect_objects`, `count_objects`,
  `read_text`, open-vocabulary queries) backed by real neuriplo predictive
  models instead of prompt-only VLM calls that can hallucinate.

The ecosystem map names secondary consumers (`neuriplo-ros`, `tritonic`)
but has no registration or boundary rules for an agentic framework.

## Constraints

- `ghostgrid` is an external Python repository with its own lifecycle; it
  is not part of the ecosystem build and must not enter the version matrix.
- ADR 0006 fixes the protocol split: predictive tasks on KServe V2,
  generative tasks on OpenAI-compatible endpoints.
- The result contract allows downstream clients to render, serialize,
  filter, and transform results, but forbids re-deriving semantics from
  backend raw outputs.
- Task preprocessing and postprocessing are owned by `neuriplo-tasks` and
  must not be re-implemented outside it.
- Infrastructure routing concerns (rate limits, model placement, gateway
  behavior) belong to the serving and gateway layer, not to consumers.

## Options

1. Leave ghostgrid unregistered and out of scope for the platform.
2. Register ghostgrid as a secondary consumer with explicit contract
   boundaries, alongside `neuriplo-ros` and `tritonic`.
3. Adopt ghostgrid into the ecosystem as an owned application layer
   (rejected: different language, lifecycle, and ownership burden; the
   platform must not absorb agent-framework runtime concerns).

## Decision

Option 2. ghostgrid is a secondary consumer with two integration paths,
each mapped to a protocol track from ADR 0006:

```text
generative path:  ghostgrid consumes neuriplo-ecosystem LLM/VLM output
                  through OpenAI-compatible endpoints using its existing
                  openai provider with a custom URL; no new client code

predictive path:  ghostgrid ReAct tools are backed by neuriplo models over
                  the KServe V2 Open Inference Protocol, returning typed
                  results (detections, segments, poses) as grounded tool
                  observations
```

Boundary rules for ghostgrid (and future agentic consumers):

- Consume the V2 wire format and the public result contract; never decode
  backend raw tensors or re-implement task pre/postprocessing.
- Consume generative output only through OpenAI-compatible endpoints; the
  embedded float-cast-bytes encoding is off limits (ADR 0006).
- Do not absorb gateway-layer concerns; model routing infrastructure stays
  in the serving/gateway layer.
- Secondary consumers are best-effort: result-contract compatibility rules
  protect them, but they do not gate ecosystem releases and do not appear
  in `versions.yaml`.

## Consequences

Positive:

- The ecosystem gains an agentic consumption story: LLM agents reason,
  neuriplo predictive models perceive, and tool observations are typed and
  verifiable instead of prompt-derived.
- The generative path needs no ghostgrid changes beyond endpoint
  configuration, validating ADR 0006's protocol choice.
- Boundary rules are written once and apply to any future agentic
  consumer, not just ghostgrid.

Negative:

- Result-contract changes now have one more downstream consumer to
  consider, even if best-effort.
- The predictive path depends on `neuriplo-kserve-runtime` (WIP) or
  another V2-compatible server actually serving the models ghostgrid's
  tools need.

Follow-up:

- Add ghostgrid to the ecosystem map in `docs/architecture/overview.md`
  as a secondary consumer.
- In ghostgrid: add a V2 `/infer`-backed detection tool to the ReAct tool
  registry, consuming serialized result-contract output.
- Add an integration example under `examples/` once a V2 endpoint serving
  a detection model is available to test against.
