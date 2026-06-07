# Production Architecture Roadmap

This roadmap tracks the remaining platform work needed to move from clear
architecture notes to production-ready architecture governance. The next gaps are
operational hardening, enforceable contracts, and validation that proves the
version matrix works across repositories.

## Current Direction

The ecosystem already has several structural patterns in place:

- `neuriplo-infer` has an `InferencePipelineBuilder` that builds source, batch,
  renderer, backend, task, and presentation stages.
- `neuriplo-tasks` uses built-in task descriptors with matchers and creators,
  which satisfies the registry goal for compiled-in tasks.
- `neuriplo-kserve-runtime` has a request pipeline with validation, admission,
  scheduling, and response encoding stages.
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
