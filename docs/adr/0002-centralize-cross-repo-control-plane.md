# ADR 0002: Centralize cross-repo control plane

Date: 2026-05-31

Status: Accepted

## Problem

`neuriplo-infer` had accumulated cross-repository architecture and maintenance
documentation because it was the practical end-to-end integration point for the
stack. That made the application repository look like the platform authority,
even though it should only own CLI, configuration, runtime wiring,
visualization, and local application flow.

## Constraints

- Implementation repositories must remain responsible for their own runtime code.
- Cross-repository boundaries, policies, and compatibility information need one
  canonical home.
- Sibling repositories use a Gitflow model: normal work targets `develop` or a
  feature branch, while `master` is release-only.
- `neuriplo-kserve-runtime` is currently WIP and may be pinned by commit until it
  has stable releases.

## Options

1. Leave cross-repository control-plane docs in `neuriplo-infer`.
2. Duplicate the same docs across every repository.
3. Move cross-repository control-plane docs to `neuriplo-platform` and leave
   implementation-specific docs in the owning repositories.

## Decision

Use `neuriplo-platform` as the canonical home for cross-repository control-plane
assets:

- architecture docs
- ADRs
- contracts
- version matrix
- repo metadata
- maintenance policies
- multi-repo runbooks
- integration-test plans

`neuriplo-infer` will keep application-specific docs and link to
`neuriplo-platform` for cross-repository boundaries and maintenance workflows.

## Consequences

Positive:

- The application repository no longer acts as the implicit platform authority.
- Cross-repository rules can be validated in one place.
- Gitflow policy can be encoded and checked outside implementation repos.
- Future serving-runtime docs can be added without stretching `neuriplo-infer`.

Negative:

- Existing automation that reads `neuriplo-infer/ops` must migrate.
- Some links and developer habits need to change.
- The platform repository now needs CI to prevent stale metadata.

Follow-up:

- Keep `neuriplo-infer/ops` as a compatibility pointer until automation moves.
- Add metadata validation in `neuriplo-platform` CI.
- Move only genuinely cross-repository docs; keep repo-local implementation docs
  in their owning repositories.
