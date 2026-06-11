# Production Architecture Roadmap

This roadmap tracks the remaining platform work needed to move from clear
architecture notes to production-ready architecture governance. The next gaps are
operational hardening, enforceable contracts, and validation that proves the
version matrix works across repositories.

## Current Direction

The ecosystem already has several structural patterns in place:

- `neuriplo-infer` has an `InferencePipelineBuilder` that builds source, batch,
  renderer, backend, task, and presentation stages, and now supports remote
  KServe V2 client mode (v0.5.0) via the standalone `neuriplo-kserve-client`
  library.
- `neuriplo-tasks` uses built-in task descriptors with matchers and creators,
  which satisfies the registry goal for compiled-in tasks.
- `neuriplo-kserve-client` is a standalone backend-agnostic KServe V2 protocol
  client (HTTP/gRPC, retry/TLS/auth, model repository extension, v0.2.0)
  consumed by `neuriplo-infer` via FetchContent.
- `neuriplo-kserve-runtime` has a request pipeline with validation, admission,
  scheduling, and response encoding stages; the feature branch merged into
  develop (2026-06-09) and the WIP serving runtime is advancing.
- `neuriplo` has backend metadata, lifecycle, state, performance, memory, and
  interface structure, but backend capabilities still need a formal public
  contract.

The highest-value next shift is not adding more named patterns. It is making the
production behavior explicit, testable, and releasable.

## Highest-Value Next Tasks

1. Formalize `BackendCapability` as a public `neuriplo` contract.
2. Add cross-repository CI that proves `versions.yaml` compatibility sets.
3. Add failure modes and a production-readiness checklist.

## Roadmap

### 1. Explicit Production Contracts

Add platform contracts for production-facing behavior:

```text
contracts/backend-capability-contract.md
contracts/model-manifest.schema.json
contracts/error-contract.md
contracts/observability-contract.md
```

Backend capabilities must be formal and owned by `neuriplo`, not inferred from
runtime-specific usage in `neuriplo-kserve-runtime`.

### 2. Real Compatibility Validation

`versions.yaml` is the compatibility source of truth. CI must prove each
compatibility set:

```text
clone pinned repos
configure/build each repo
run unit tests
run one local inference smoke test
run one KServe HTTP smoke test
```

The platform test should fail when a pinned ref cannot build or when a public
contract used across repos is broken.

### 3. Release Strategy

Document release governance for:

```text
semantic versioning
compatibility matrix
deprecation policy
breaking-change policy
release branches/tags
rollback strategy
```

This should extend the existing branch policy and version matrix rules with
explicit rules for compatibility windows and breaking changes.

### 4. Observability

Document observability as a platform contract, building on the work already
started in `neuriplo-kserve-runtime`:

```text
structured logs
metrics
tracing
request IDs
latency histograms
queue depth
batch size
model load time
backend failures
OOM/errors
```

The platform contract should define names, required dimensions, error fields,
and compatibility expectations. Runtime implementation remains in the owning
repos.

### 5. Reliability And Backpressure

Make serving reliability behavior explicit:

```text
max queue size
timeout behavior
cancellation
graceful shutdown
draining
overload response
retry policy
bulkhead isolation
per-model limits
```

These rules should be visible in contracts and runbooks, not buried in serving
implementation code.

### 6. Security

Add architecture docs for the production security assumptions:

```text
input size limits
payload validation
authn/authz story
TLS termination assumptions
container user permissions
model artifact trust
supply-chain scanning
secret handling
SBOM
```

Security boundaries should state what the platform requires and what each owning
repo or deployment layer must enforce.

### 7. Deployment Story

Document the supported production deployment shape:

```text
Docker image
Helm chart or KServe ServingRuntime YAML
resource requests/limits
GPU scheduling
readiness/liveness probes
model storage assumptions
config via env/manifest
```

The platform should define deployment expectations and evidence requirements;
image builds, charts, and runtime manifests stay in owning repos unless a future
ADR changes that boundary.

### 8. Failure-Mode Documentation

Create:

```text
docs/architecture/failure-modes.md
```

Cover at least:

```text
model not found
model load failure
backend unavailable
invalid tensor shape
queue full
request timeout
GPU OOM
unsupported dtype
version mismatch
```

Each failure mode should define owner, expected error contract, observability
signals, retry behavior, and runbook link.

### 9. Architecture Fitness Tests

Add tests that protect architecture, not just code behavior:

```text
neuriplo-tasks must not depend on neuriplo-infer
neuriplo must not depend on neuriplo-kserve-runtime
platform repo must contain no runtime code
all public contracts have examples
versions.yaml refs are buildable
```

These checks should run in platform CI and block changes that violate ownership
or compatibility policy.

### 10. Production Runbooks

Add production runbooks:

```text
ops/runbooks/deploy-runtime.md
ops/runbooks/rollback-runtime.md
ops/runbooks/debug-queue-full.md
ops/runbooks/debug-model-load-failure.md
ops/runbooks/debug-latency-regression.md
ops/runbooks/release-checklist.md
```

Runbooks should include symptoms, immediate checks, owner escalation, validation
commands, rollback criteria, and evidence to attach to PRs or incidents.

### 11. Generative Inference Protocol Alignment

Upstream KServe now splits its data plane into two tracks:

```text
predictive AI:  V1 protocol and V2 Open Inference Protocol (/infer, gRPC)
generative AI:  OpenAI-compatible endpoints (/v1/chat/completions,
                /v1/completions, /v1/embeddings) with SSE streaming
```

The neuriplo ecosystem currently routes the generative
`ImageUnderstandingTask` (llama.cpp LLM/VLM) over V2 tensors with a
float-cast-bytes text encoding. That encoding works for embedded local mode
but goes against where KServe has landed for serving: text generation does
not fit the tensor protocol (no streaming, no sampling parameters, no chat
semantics).

ADR 0006 adopted the predictive/generative split:

```text
predictive tasks (detection, segmentation, pose, depth, open-vocab,
classification) stay on V2 Open Inference Protocol via
neuriplo-kserve-client and neuriplo-kserve-runtime

generative tasks (image_understanding) keep embedded llama.cpp for local
and edge mode; at serving scale they are exposed through an
OpenAI-compatible endpoint (llama-server or a vLLM-backed deployment)
rather than reimplemented inside neuriplo-kserve-runtime

neuriplo does not compete with vLLM/KServe on LLM serving; its serving
differentiation stays on the predictive track
```

Status: ADR decided. The remote KServe V2 client path is implemented
(neuriplo-infer v0.5.0 + neuriplo-kserve-client v0.2.0). The OpenAI-compatible
generative path is documented but not yet plumbed through a platform integration
test. Remaining work: generative serving smoke test in integration-tests/.

Consequences:

- The V2 float-cast-bytes text encoding becomes an internal detail of
  embedded local mode and is not a public serving contract.
- OpenAI-compatible consumers (agent frameworks, gateways) integrate with
  the generative path with no custom protocol client.
- Agent-loop economics improve on the OpenAI path: vLLM prefix caching
  amortizes re-sent prompts, which the V2 tensor path cannot do.

### 12. Secondary Consumers: Agentic Frameworks

`ghostgrid` (multi-provider LLM/VLM agentic workflow framework) is a
registered secondary consumer alongside `neuriplo-ros` and `tritonic`.
Two integration paths map onto the two protocol tracks:

```text
generative path:  ghostgrid consumes neuriplo-ecosystem LLM/VLM output
                  through OpenAI-compatible endpoints using its existing
                  openai provider with a custom URL; no new client code

predictive path:  ghostgrid ReAct tools (detect, count, read_text,
                  open-vocab queries) are backed by neuriplo models over
                  the V2 Open Inference Protocol, replacing prompt-only
                  vision tools with grounded typed results
```

Status: ADR 0007 registered ghostgrid as a secondary consumer. ADR 0008
published result events from neuriplo-infer with renderer as first consumer.
Pending work: end-to-end integration smoke test that validates the ghostgrid
provider -> neuriplo inference chain.

Boundary rules for agentic consumers:

- Consume the V2 wire format and the result contract; do not re-implement
  task preprocessing or postprocessing outside neuriplo-tasks.
- Infrastructure routing (rate limits, model placement, gateway concerns)
  belongs to the serving and gateway layer, not the agent framework.
- Registration as a secondary consumer requires an ADR and an entry in the
  ecosystem map in `docs/architecture/overview.md`.

## Definition Of Done

Production architecture is ready when:

- public contracts define backend capabilities, model manifests, errors, and
  observability
- compatibility CI proves each supported version set from source
- release, deprecation, rollback, and breaking-change rules are documented
- failure modes and runbooks cover common serving incidents
- architecture fitness tests protect repository boundaries
- production deployment expectations are explicit enough for repeatable release
  evidence
- the predictive/generative protocol split is implemented (ADR 0006 adopted,
  remote KServe V2 client path operational in neuriplo-infer v0.5.0; generative
  smoke test still pending)
- secondary consumers, including agentic frameworks, are registered with
  explicit contract boundaries (ADRs 0007, 0008 accepted; integration smoke
  test pending)
