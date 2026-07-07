# ADR 0010: Generalize task domains beyond computer vision

Date: 2026-07-01

Status: Accepted

## Problem

[`neuriplo-tasks`](https://github.com/olibartfast/neuriplo-tasks) started
with computer vision task families, and CV remains the only fully shipped task
domain. That history must not become a permanent
architecture limit. Common ML task taxonomies include multimodal, NLP, computer
vision, audio, tabular, and reinforcement learning workloads. Some of these fit
the existing preprocess/execute/postprocess contract directly; others need
different protocol or lifecycle rules.

The platform needs a stable taxonomy before runtime code grows around ad-hoc
model-family labels.

## Decision

Treat `neuriplo-tasks` as the general task contract layer. Computer vision is
the first implemented domain, not the platform ceiling.

The platform reserves these task domains:

```text
cv          shipped first domain
nlp         planned
audio       planned
tabular     planned
multimodal  planned
rl          tracked, out of scope for serving v1
```

Each domain must define:

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

Serving protocol follows task behavior:

- Predictive tensor tasks use KServe V2 / Open Inference Protocol.
- Generative chat/text tasks use OpenAI-compatible endpoints, per ADR 0006.
- Embedded local tasks may use implementation-specific encodings internally,
  but those encodings are not public serving contracts.

## Consequences

Positive:

- Future task work has a domain contract before implementation.
- `neuriplo-tasks` can grow to NLP, audio, tabular, and multimodal workloads
  without repo renaming or a premature split.
- Serving protocol choices are made explicitly per domain and task behavior.

Negative / cost:

- Contracts need to distinguish implemented domains from reserved domains.
- A future second shipped domain will force a concrete decision on whether
  `neuriplo-tasks` remains one repo or splits into per-domain packages.
- Reinforcement learning is intentionally tracked but not designed for serving
  v1 because environment interaction and policy lifecycle semantics differ from
  stateless inference requests.

## Follow-up

- Pilot one non-CV predictive task family before adding broad abstractions.
- Prefer NLP embeddings as the first pilot because they are tensor-shaped,
  batchable, and compatible with KServe V2.
- Update downstream repos only after the platform contract and task metadata
  are stable.
