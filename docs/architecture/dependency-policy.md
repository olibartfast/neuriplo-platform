# Dependency Policy

This document defines cross-repository dependency ownership and compatibility
rules for the vision platform. Repo-local build details stay in the owning
repositories.

## Source Of Truth

Platform-level sources:

- `versions.yaml`: known-good ecosystem versions and WIP commit pins.
- `ops/CLUSTER_MAP.yaml`: repository roles and dependency edges.
- `ops/repo-meta/*.yaml`: repo-local entrypoints, public surfaces, and
  constraints.
- `ops/policies.yaml`: branch policy, review rules, and allowed change classes.

Implementation-level sources:

- `neuriplo-tasks`: task contracts, model task behavior, preprocessing,
  postprocessing, result types.
- `neuriplo`: backend abstractions, backend adapters, backend runtime package
  versions, runtime compatibility behavior.
- `neuriplo-infer`: local CLI, app configuration, runtime wiring,
  visualization, local setup scripts.
- `neuriplo-kserve-runtime`: serving runtime protocol, admission, scheduling,
  batching, lifecycle, operational endpoints.
- `videocapture`: video and image source semantics, video backend behavior.

## Ownership Rules

`neuriplo-platform` owns compatibility policy, not implementation behavior.

Released repositories should be referenced by immutable release tags in platform
compatibility sets. WIP repositories may be pinned by commit SHA until they have
stable releases.

Backend package versions belong to `neuriplo`. Application and serving repos may
consume those versions, but should not redefine backend version policy in prose.

Task and result semantics belong to `neuriplo-tasks`. Consumers may document how
they use those contracts, but should not redefine tensor shapes, dtype meaning,
or result schema semantics.

Local app setup behavior belongs to `neuriplo-infer`. Cross-repository
compatibility belongs here.

Serving runtime dependency behavior belongs to `neuriplo-kserve-runtime` when it
is about serving mechanics. Shared backend execution compatibility still belongs
to `neuriplo`.

## Version Matrix Rules

For each repository in `versions.yaml`:

- Released repos use `version: vX.Y.Z` and a matching immutable commit `ref`.
- WIP repos use `version: wip` and a 40-character commit SHA `ref`.
- Compatibility sets must use the declared release tag for released repos.
- Compatibility sets must use the pinned commit SHA for WIP repos.

The current baseline treats `neuriplo-tasks`, `neuriplo`, and `neuriplo-infer` as
released repos. `neuriplo-kserve-runtime` is WIP and pinned by commit.

## Branch Policy

Sibling implementation repositories follow Gitflow:

- normal work targets `develop`, `feat/*`, or `feature/*`
- `master` is release-only
- direct changes to `master` are not allowed

`neuriplo-platform` currently uses `main` for platform documentation and metadata.

## Dependency Change Workflow

For cross-repository dependency changes:

1. Identify the owning repository for the changed contract or dependency.
2. Update implementation and repo-local tests in the owning repository first.
3. Update downstream consumers on `develop` or a feature branch.
4. Update `neuriplo-platform` contracts, runbooks, and `versions.yaml` when the
   ecosystem compatibility surface changes.
5. Record major boundary or compatibility decisions as ADRs.

## What Not To Duplicate

Do not duplicate these in platform docs:

- exact backend installation commands owned by `neuriplo`
- local CLI setup details owned by `neuriplo-infer`
- task tensor semantics owned by `neuriplo-tasks`
- serving implementation details owned by `neuriplo-kserve-runtime`
- video backend setup matrices owned by `videocapture`

Instead, link to the owning repo and document only the cross-repository contract
or compatibility implication here.
