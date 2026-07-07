# Failure Modes

This document defines the production failure modes that the platform expects
each repository to classify, observe, and validate. It complements
`contracts/error-contract.md`; implementation remains in the owning repositories.

## Scope

Failure-mode coverage is platform evidence, not runtime code. Each case must
declare:

- owner repository
- stable error code
- expected transport status
- retry behavior
- observability fields
- runbook link
- validation status

The first platform test is metadata-only so CI can run it without model
artifacts, GPU hardware, or a serving process.

## Required Cases

| Case | Error code | Owner | Retry | Runbook |
|---|---|---|---:|---|
| model-not-found | `MODEL_NOT_FOUND` | `neuriplo-kserve-runtime` | false | `ops/runbooks/debug-serving-failure.md` |
| model-load-failure | `MODEL_LOAD_FAILED` | `neuriplo-kserve-runtime` | false | `ops/runbooks/debug-serving-failure.md` |
| backend-unavailable | `BACKEND_UNAVAILABLE` | `neuriplo` | true | `ops/runbooks/debug-serving-failure.md` |
| invalid-tensor-shape | `INVALID_TENSOR_SHAPE` | `neuriplo-kserve-runtime` | false | `ops/runbooks/debug-serving-failure.md` |
| queue-full | `QUEUE_FULL` | `neuriplo-kserve-runtime` | true | `ops/runbooks/debug-serving-failure.md` |
| request-timeout | `REQUEST_TIMEOUT` | `neuriplo-kserve-runtime` | true | `ops/runbooks/debug-serving-failure.md` |
| gpu-oom | `GPU_OOM` | `neuriplo` | true | `ops/runbooks/debug-serving-failure.md` |
| unsupported-dtype | `UNSUPPORTED_DTYPE` | `neuriplo` | false | `ops/runbooks/debug-serving-failure.md` |
| version-mismatch | `VERSION_MISMATCH` | `neuriplo-platform` | false | `ops/runbooks/debug-serving-failure.md` |

## Ownership Boundaries

`neuriplo-platform` owns:

- the failure-mode list
- the error contract
- required metadata shape
- compatibility evidence requirements

`neuriplo-kserve-runtime` owns:

- KServe HTTP/gRPC error mapping
- admission failures
- queue and timeout behavior
- model lifecycle failures

`neuriplo` owns:

- backend initialization failures
- GPU allocation failures
- backend dtype and capability failures

`neuriplo-tasks` owns:

- task-level shape and semantic validation
- task result compatibility expectations

`neuriplo-kserve-client` and `neuriplo-infer` own:

- client-side timeout presentation
- mapping remote protocol failures into user-visible diagnostics
- preserving request IDs and model names when available

## Promotion Rules

A compatibility set may be promoted with metadata-only failure-mode coverage
while executable negative-path tests are still absent, but the report must say
that the coverage is not attested.

Promotion to production-ready requires executable evidence for at least:

```text
MODEL_NOT_FOUND
INVALID_TENSOR_SHAPE
QUEUE_FULL
REQUEST_TIMEOUT
UNSUPPORTED_DTYPE
VERSION_MISMATCH
```

GPU-specific failures such as `GPU_OOM` may be attested on hardware runners or
documented as skipped with a hardware reason.
