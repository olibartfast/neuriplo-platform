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

## Integration Test Plan

The release-grade local inference test should extend this smoke in ordered
stages:

1. Read the selected compatibility set from `versions.yaml`.
2. Verify each sibling checkout exists and resolves to the pinned tag or commit.
3. Configure and build the minimum targets needed for `neuriplo-tasks`,
   `neuriplo`, and `neuriplo-infer`.
4. Run a mock or tiny fixture inference through the app-owned runner:
   `local image -> task -> backend -> result`.
5. Assert contract-level output:
   task type resolved, backend abstraction used, typed result family returned,
   and app output artifact created.
6. Record validation evidence in the PR using `ops/PR_EVIDENCE_TEMPLATE.md`.

The first executable version should prefer a mock backend or tiny fixture model
so it can run before GPU, model download, or large artifact requirements are
introduced.

## Usage

From `neuriplo-platform`:

```bash
integration-tests/local-inference-smoke/run.py
```

Override the dry-run preset:

```bash
integration-tests/local-inference-smoke/run.py --preset owlv2
```
