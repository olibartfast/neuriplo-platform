# Repository Guidelines

## Project Structure & Module Organization

`neuriplo-platform` is an architecture/control-plane repository. Runtime code stays in sibling repos. Key areas:

- `docs/architecture/`: architecture notes and migration policy.
- `docs/adr/`: Architecture Decision Records; use `0000-template.md` for new decisions.
- `contracts/`: cross-repository task, backend, result, runtime, and configuration contracts.
- `ops/`: cluster map, repo metadata, policies, runbooks, and PR evidence templates.
- `examples/`: platform-level scenario docs, not large model files.
- `integration-tests/`: cross-repo smoke/integration checks.
- `versions.yaml`: known-good version and commit compatibility matrix.
- `scripts/check_platform.py`: metadata and structure validator.

## Build, Test, and Development Commands

This repo has no build step. Use validation commands instead:

```bash
scripts/check_platform.py
scripts/check_component_progress.py
integration-tests/local-inference-smoke/run.py
```

`check_platform.py` validates YAML metadata, required docs, examples, integration-test shape, ASCII content, and version policy. `check_component_progress.py` reports compile-speed and baseline tooling progress across local sibling implementation repos (see `ops/runbooks/faster-compilation.md`). The smoke test checks local sibling checkouts and dry-runs the app-owned E2E runner.

## Coding Style & Naming Conventions

Prefer Markdown and YAML with short, explicit sections. Keep files ASCII-only. Use lowercase kebab-case for docs and directories, for example `dependency-policy.md` and `local-inference-smoke/`. ADRs use zero-padded numeric prefixes: `0003-keep-runners-in-owning-repos.md`.

Python scripts should be small, dependency-light, executable, and compatible with Python 3.12. Use clear error messages and nonzero exits for validation failures.

## Testing Guidelines

Run `scripts/check_platform.py` before every commit. If integration-test metadata or smoke behavior changes, also run `integration-tests/local-inference-smoke/run.py`. Do not add model downloads, generated artifacts, or GPU-dependent checks without documenting requirements in the test README.

## Commit & Pull Request Guidelines

Use concise imperative commit subjects, matching existing history, for example `Add local inference smoke integration test`. Keep platform-only changes on `main`. Sibling implementation repos follow Gitflow: normal work targets `develop`, `feat/*`, or `feature/*`; `master` is release-only.

Before any commit or push, follow the mandatory Gitflow rules in
`.cursor/rules/gitflow-workflow.mdc` and `ops/policies.yaml`. Feature work
merges to `develop`; release and hotfix work merges to `master` and back to
`develop`; never push normal work directly to sibling `master` or force-push
`main`/`master`.

PRs should describe changed docs/contracts, affected repos, validation output, and any follow-up required. Use `ops/PR_EVIDENCE_TEMPLATE.md` for cross-repo maintenance work.

## Architecture Rules

Do not move runtime implementation into this repo. Document ownership, contracts, compatibility, and integration expectations here; keep implementation details in the owning repository.
