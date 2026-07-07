# Failure Mode Contract Test

Validation status: Metadata contract check, executable negative-path tests not
yet attested

Version set: `rfdetr-keypoint-pose-followup`

Owning repos: `neuriplo-platform`, `neuriplo-kserve-runtime`, `neuriplo`, `neuriplo-tasks`, `neuriplo-kserve-client`, `neuriplo-infer`

## Purpose

Validate the platform-owned failure-mode matrix before the runtime and client
repositories wire every negative-path test. This test makes the expected error
codes, owner repositories, retry behavior, transport statuses, observability
fields, and runbook links explicit.

## What It Checks

- every required failure case from `docs/architecture/failure-modes.md` is
  declared
- each case uses a stable code from `contracts/error-contract.md`
- retry and transport status fields are present
- every case names an owning repository
- every case links a repository-local runbook
- observability fields include request and model correlation data

## Usage

From `neuriplo-platform`:

```bash
integration-tests/failure-modes/run.py
```

This is a metadata check. Executable runtime/client negative-path tests stay in
the owning repositories and should be linked as attested evidence when they are
available.
