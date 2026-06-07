# Local Inference Smoke Test

Validation status: Draft executable smoke, not a release E2E

Version set: `initial-architecture-baseline`

Owning repos:

- `neuriplo-platform`: smoke-test orchestration and version expectations.
- `neuriplo-infer`: app-owned E2E runner and CLI behavior.
- `neuriplo-tasks`: task/export tooling and task contracts.
- `neuriplo`: backend abstraction and execution.
- `neuriplo-kserve-runtime`: WIP serving runtime, commit-pinned only in this smoke.
- `videocapture`: video/image source handling consumed by `neuriplo-infer`.

## Purpose

Validate that the local checkout cluster can satisfy the platform compatibility
matrix before running expensive model export or inference work.

## What It Checks

- `versions.yaml` parses.
- local sibling repositories exist next to `neuriplo-platform`.
- released repositories contain the expected release tags.
- released repository tags resolve to the commit SHA pinned in `versions.yaml`.
- WIP repositories contain the pinned commit SHA.
- `neuriplo-infer/docker_run_inference_e2e_example.sh` exists.
- the app-owned runner can list presets.
- the app-owned runner can dry-run one representative preset.

## What It Does Not Check Yet

- model download
- model export
- backend dependency installation
- real inference execution
- numerical or visual output correctness

Use `../kserve-runtime-e2e/run.py` for the real local KServe runtime release
validation path.

## Usage

From `neuriplo-platform`:

```bash
integration-tests/local-inference-smoke/run.py
```

Override the dry-run preset:

```bash
integration-tests/local-inference-smoke/run.py --preset owlv2
```
