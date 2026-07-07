# Debug Serving Failure Runbook

Use this when a local or remote inference request fails with a classified error
from `contracts/error-contract.md`.

## Goal

Identify the owning repository, decide whether retry is allowed, and collect
enough evidence to fix or route the failure.

## Inputs

- Error code and message.
- HTTP or gRPC status.
- Request ID, model name, and compatibility set when available.
- Runtime logs or client output.
- Current `versions.yaml` compatibility set.

## Procedure

1. Map the error code to `contracts/error-contract.md`.

2. Confirm the owner repository.
   - `neuriplo-platform`: version matrix, compatibility-set, or evidence issue.
   - `neuriplo-kserve-runtime`: model lifecycle, admission, queue, timeout, or protocol status issue.
   - `neuriplo`: backend initialization, capability, dtype, or GPU memory issue.
   - `neuriplo-tasks`: task shape, preprocessing, postprocessing, or result contract issue.
   - `neuriplo-kserve-client` or `neuriplo-infer`: client timeout, presentation, or request construction issue.

3. Preserve correlation data.
   - request ID
   - model name and version
   - compatibility set
   - backend and device when known
   - tensor name, dtype, or shape when the failure is request-specific

4. Apply retry policy from the error contract.
   - Retry only errors marked retryable.
   - Do not retry `INVALID_TENSOR_SHAPE`, `UNSUPPORTED_DTYPE`, or `VERSION_MISMATCH` without a corrective change.

5. Reproduce in the owning repository using its negative-path test or local
   runner.

6. If the failure crosses a public contract, update the platform evidence:
   `integration-tests/failure-modes/cases.yaml`, the relevant compatibility
   report, or the contract document.

7. Attach evidence to the PR using `ops/PR_EVIDENCE_TEMPLATE.md`.

## Exit Criteria

- Error code and owner are identified.
- Retry decision is documented.
- Required observability fields are captured or listed as missing.
- Owning repository has a reproduction path or a tracked follow-up.
