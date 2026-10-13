# ADR 0013: Standalone Fetched Dependency Manager

Date: 2026-10-13

Status: Proposed

## Problem

Each C++ sibling tracks third-party packages its own way: divergent
`versions.env` files, duplicated `setup_*.sh` curl logic, apt-only
assumptions, and no conan/vcpkg/snap coverage. There is no uniform
per-project status (wanted vs installed vs update-available).

## Constraints

- [`neuriplo-platform`](https://github.com/olibartfast/neuriplo-platform)
  holds no runtime/tool code (ADR 0003).
- New dependencies are a forbidden automation change class; bumps need
  human review.
- Existing `source versions.env` and `cmake -D` precedence must keep
  working during migration.
- Day-1 scope covers apt, snap, conan, vcpkg, custom-url, fetchcontent.

## Options

1. Standalone repo fetched via `FetchContent` (chosen shape). One owner,
   versioned tags, consumed like
   [`neuriplo-kserve-client`](https://github.com/olibartfast/neuriplo-kserve-client).
2. Platform-hosted tooling. Rejected: violates ADR 0003, unversioned
   relative to consumers.
3. Extend `neuriplo-infer` scripts. Rejected: wrong owner; forces every
   sibling to depend on the app layer, inverting the dependency edges in
   `ops/CLUSTER_MAP.yaml`.

## Decision

Create a standalone repo (coldpac, no `neuriplo-` prefix)
owning the manifest schema, resolvers per provider, lockfile,
`versions.env` projection, and `status`/`check-updates` commands.
Consumers fetch it pinned to a tag. The platform owns only
`contracts/dependency-manifest-contract.md` and this packet.

## Consequences

What improves: one declaration shape, one status view, explicit provider
precedence/fallback/offline behavior, lossless migration off duplicated
setup scripts.

What gets harder: a new repo to release; consumers carry a FetchContent
pin to maintain; snap needs snapd hosts outside hermetic CI.

Follow-up: repo creation + Group 2-5 of
`specs/2026-10-13-unified-dependency-manager/plan.md`; first integration
in `videocapture`; platform records the tooling pin.
