# ADR 0003: Keep executable runners in owning repositories

Date: 2026-05-31

Status: Accepted

## Problem

`vision-inference` owns the local CLI and Docker runner used for end-to-end
local inference examples. `neuriplo-platform` needs to describe and validate
cross-repository scenarios without duplicating app-owned scripts, model files,
or backend-specific command details.

## Constraints

- `neuriplo-platform` should not become a runtime implementation repository.
- App-owned CLI behavior belongs in `vision-inference`.
- Platform examples need stable scenario metadata, version-set references, and
  contract-level validation expectations.
- Real inference can require large models, backend dependencies, and GPU access,
  so initial platform tests must start with cheap smoke checks.

## Options

1. Copy executable E2E scripts and model artifacts into `neuriplo-platform`.
2. Leave all E2E documentation and validation in `vision-inference`.
3. Keep executable runners in owning repos and let `neuriplo-platform` orchestrate
   cross-repository smoke and integration checks.

## Decision

Executable runners remain in the repository that owns the runtime surface they
exercise. `neuriplo-platform` owns scenario documentation, compatibility metadata,
and orchestration scripts that call those app-owned runners.

For local inference, `vision-inference/docker_run_inference_e2e_example.sh`
remains the executable runner. `neuriplo-platform` documents the scenario under
`examples/e2e-local-inference/` and provides smoke coverage under
`integration-tests/local-inference-smoke/`.

## Consequences

Positive:

- Runtime behavior remains close to the code that owns it.
- Platform examples can validate cross-repository expectations without copying
  large artifacts or command internals.
- Smoke checks can run before expensive model export or inference tests.

Negative:

- Platform integration tests depend on sibling checkouts being present locally.
- The platform smoke test can break when app-owned runner flags change.
- Full inference validation still needs separate backend/model provisioning.

Follow-up:

- Add heavier integration tests only after fixture and backend requirements are
  explicit.
- Keep platform example metadata validated by CI.
- Update `vision-inference` docs to point scenario-level readers to
  `neuriplo-platform/examples`.
