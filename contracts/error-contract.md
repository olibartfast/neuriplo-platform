# Error Contract

Owner: `neuriplo-platform` (contract definition); serving and application
repositories own implementation.

Consumers: `neuriplo-infer`, `neuriplo-kserve-client`,
`neuriplo-kserve-runtime`, integration tests, runbooks

Status: Draft

## Purpose

Define the cross-repository error surface for local and remote inference flows.
The same failure must be classifiable whether it is observed through embedded
local execution, the KServe V2 client path, or the serving runtime.

This contract does not require every repository to expose identical transport
details. It requires stable error classification, owner assignment, retry
semantics, and observability fields so callers and operators can respond
consistently.

## Error Envelope

Errors should normalize to this logical shape:

```json
{
  "code": "MODEL_NOT_FOUND",
  "message": "model 'rfdetr-pose' was not found",
  "owner": "neuriplo-kserve-runtime",
  "retryable": false,
  "http_status": 404,
  "grpc_status": "NOT_FOUND",
  "request_id": "req-123",
  "model": "rfdetr-pose",
  "details": {
    "repository": "model-repository",
    "version": "1"
  }
}
```

Local C++ exceptions do not need to use JSON internally, but release evidence
and integration tests should be able to map them to these fields.

## Required Fields

```text
code          stable uppercase snake-case error code
message       human-readable summary, safe for logs and client output
owner         repository responsible for fixing the underlying failure
retryable     boolean caller retry guidance
http_status   HTTP status when exposed through KServe HTTP
grpc_status   gRPC status when exposed through KServe gRPC
request_id    correlation id when a request reached a runtime boundary
model         model name when known
details       optional structured context, no secrets
```

## Required Error Codes

| Code | Owner | Retryable | HTTP | gRPC | Meaning |
|---|---|---:|---:|---|---|
| `MODEL_NOT_FOUND` | `neuriplo-kserve-runtime` | false | 404 | `NOT_FOUND` | Requested model is not registered or not loaded. |
| `MODEL_LOAD_FAILED` | `neuriplo` or `neuriplo-kserve-runtime` | false | 500 | `INTERNAL` | Runtime found the model but backend initialization failed. |
| `BACKEND_UNAVAILABLE` | `neuriplo` | true | 503 | `UNAVAILABLE` | Backend provider or device is unavailable. |
| `INVALID_TENSOR_SHAPE` | `neuriplo-tasks` or `neuriplo-kserve-runtime` | false | 400 | `INVALID_ARGUMENT` | Request tensor rank, shape, dtype, or layout violates the task contract. |
| `QUEUE_FULL` | `neuriplo-kserve-runtime` | true | 429 | `RESOURCE_EXHAUSTED` | Admission control rejected the request because queue capacity is exhausted. |
| `REQUEST_TIMEOUT` | `neuriplo-kserve-runtime` or `neuriplo-kserve-client` | true | 504 | `DEADLINE_EXCEEDED` | Deadline elapsed before a response completed. |
| `GPU_OOM` | `neuriplo` | true | 503 | `RESOURCE_EXHAUSTED` | Backend could not allocate required GPU memory. |
| `UNSUPPORTED_DTYPE` | `neuriplo` or `neuriplo-tasks` | false | 400 | `INVALID_ARGUMENT` | Tensor dtype is not supported by the selected backend or task. |
| `VERSION_MISMATCH` | `neuriplo-platform` | false | 409 | `FAILED_PRECONDITION` | Repository or model version does not match a promoted compatibility set. |

## Compatibility Rules

- Adding a new error code is backward compatible when existing codes keep their
  meaning.
- Changing `retryable` for a required code is breaking.
- Changing the transport status for a required code is breaking unless the old
  status was never released.
- Error messages may change, but the stable `code` must not be parsed from
  free-form text.
- `details` may add fields. Removing fields used by runbooks or integration
  tests is breaking.

## Validation Strategy

- `integration-tests/failure-modes/run.py` validates the platform-owned failure
  matrix and required metadata shape.
- Runtime and client repositories own executable negative-path tests for their
  transports.
- Compatibility reports should link negative-path evidence before a set is
  promoted beyond draft when failures affect public serving behavior.
