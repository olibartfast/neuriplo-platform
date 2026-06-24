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

Prefer Markdown and YAML with short, explicit sections. Keep files ASCII-only.
Hyperlink component and repository names to their GitHub repository on first
mention in a document (outside code blocks); a reader must not need prior
context to know what `neuriplo-kserve-client` or `neuriplo-tasks` refers to.

When editing any documentation with hyperlinks, verify all relative links resolve to
existing files and absolute GitHub URLs are reachable. Prefer absolute GitHub blob/tree
URLs over fragile cross-repo relative paths (e.g. `../../../neuriplo/docs/foo.md`). The root `README.md`
is the canonical linked registry. Use lowercase kebab-case for docs and directories, for example `dependency-policy.md` and `local-inference-smoke/`. ADRs use zero-padded numeric prefixes: `0003-keep-runners-in-owning-repos.md`.

Python scripts should be small, dependency-light, executable, and compatible with Python 3.12. Use clear error messages and nonzero exits for validation failures.

## Testing Guidelines

Run `scripts/check_platform.py` before every commit. If integration-test metadata or smoke behavior changes, also run `integration-tests/local-inference-smoke/run.py`. Do not add model downloads, generated artifacts, or GPU-dependent checks without documenting requirements in the test README.

## Agent Commit Signing

Every commit produced by an AI agent MUST include a `Co-authored-by` trailer
that identifies the agent, the LLM model used, and the agent vendor. This makes
agent contributions visible in GitHub's contribution graph and `git shortlog`.

Format: `Co-Authored-By: <Agent> <Model> <<vendor-email>>`

| Agent | Vendor email | Example trailer |
|-------|-------------|-----------------|
| Cursor | `cursoragent@cursor.com` | `Co-authored-by: Cursor <cursoragent@cursor.com>` |
| Claude Code | `noreply@anthropic.com` | `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` |
| Opencode | `agent@opencode.ai` | `Co-Authored-By: Opencode via DeepSeek V4 Pro <agent@opencode.ai>` |

The model name MUST match the LLM the agent is powered by (check the system
prompt). If the model changes across sessions, the trailer must reflect the
model used for that specific commit.

The vendor email MUST NOT be associated with any real GitHub user profile to prevent incorrect attribution in commit histories. Always verify that agent emails use private/noreply or non-associated vendor domains (e.g., `antigravity-agent-private@google.com`).

Place the trailer in the commit body (after the subject line and blank line),
not the subject.

## Commit & Pull Request Guidelines

Use concise imperative commit subjects, matching existing history, for example `Add local inference smoke integration test`. Keep platform-only changes on `main`.

**Coding components** (`neuriplo-tasks`, `neuriplo`, `neuriplo-infer`,
`neuriplo-kserve-client`, `neuriplo-kserve-runtime`, `videocapture`) must follow
Gitflow before commit, push, or PR: normal work targets `develop`, `feat/*`, or
`feature/*`; `master` is release-only. See `.agents/rules/always-apply.md`
and `ops/policies.yaml`.

**neuriplo-platform** is the document/architecture orchestrator. Gitflow is not
mandatory here; work normally lands on `main`. Do not apply sibling
`develop`/`master` branch rules to this repo.

PRs should describe changed docs/contracts, affected repos, validation output, and any follow-up required. Use `ops/PR_EVIDENCE_TEMPLATE.md` for cross-repo maintenance work.

## Architecture Rules

Do not move runtime implementation into this repo. Document ownership, contracts, compatibility, and integration expectations here; keep implementation details in the owning repository.
