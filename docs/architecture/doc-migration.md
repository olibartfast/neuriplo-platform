# Documentation Migration Plan

`neuriplo-infer` historically carried some cross-repository documentation
because it was the practical integration point for the stack. `neuriplo-platform`
is now the canonical home for architecture-control-plane material.

## Move Here

These belong in `neuriplo-platform`:

- Cross-repository ownership and boundary docs.
- ADRs.
- Version compatibility matrices.
- Cross-repository contracts.
- Multi-repo runbooks and agent policies.
- End-to-end examples that exercise more than one repository.
- Integration test plans and compatibility evidence.

## Keep In Owning Repos

These stay in implementation repositories:

- Repo-local build instructions.
- Repo-local CLI or API reference.
- Backend-specific implementation notes.
- Generated docs tied directly to source code.
- Unit and component test instructions.
- Release process details owned by a single repository.

## Initial Transfers

The first migrated area is `neuriplo-infer/ops`, now represented under
`neuriplo-platform/ops` with paths and roles adapted for the full platform.

`neuriplo-infer` should eventually replace its cross-repo `ops` content with a
short pointer to this repository, while retaining application-specific docs such
as CLI usage, app architecture, and release workflow.
