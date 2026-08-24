# Validation

Milestone: Register neuriplo-ui in the multi-repository architecture

Status: Complete

## Automated Checks

1. Run `python3 scripts/check_platform.py` and require exit code 0.
2. Parse `ops/CLUSTER_MAP.yaml`, `ops/policies.yaml`,
   `ops/repo-meta/neuriplo-ui.yaml`, and `versions.yaml` through the platform
   validator.
3. Confirm every new relative Markdown link resolves to a repository file.
4. Confirm the pinned private `neuriplo-ui` commit exists through authenticated
   GitHub access.
5. Confirm the current `neuriplo-infer` capability schema link is reachable.

## Negative Checks

- Active architecture documents must not describe `neuriplo-ui` as a Qt or
  in-process C++ application.
- `neuriplo-ui` must not be listed as a C++ Gitflow sibling with `develop` and
  release-only `master` branches.
- KServe must not be listed as a local inference backend. It belongs only to
  the `client_server` workflow.
- Platform metadata must not claim that the browser directly launches native
  inference or accesses local files.

## Manual Checks

- Review the dependency direction as
  `browser -> local adapter -> neuriplo-infer`.
- Review ownership: `neuriplo-ui` owns presentation, the local browser adapter,
  and browser E2E coverage; `neuriplo-infer` owns capability and execution
  behavior.
- Review that existing compatibility sets remain unchanged because the WIP UI
  is not yet part of a released compatibility claim.

## Definition Of Done

- The cluster map, repository metadata, version matrix, root registry,
  architecture overview, ownership model, and contributor bootstrap map name
  `neuriplo-ui`.
- A superseding ADR records the implemented browser architecture.
- A cross-repository contract records capability discovery ownership and
  compatibility rules.
- The platform validation command passes.

## Results

- `python3 -m py_compile scripts/check_platform.py`: passed.
- `python3 scripts/check_platform.py`: passed with `platform metadata ok`.
- `git diff --check`: passed.
- Relative links in every changed Markdown file: resolved.
- Public GitHub repository links and the pinned capability-schema link: HTTP
  200.
- Private `neuriplo-ui` repository: authenticated GitHub lookup confirmed
  visibility `PRIVATE`, default branch `master`, and the pinned commit at
  `refs/heads/master`.
- Manual and negative checks: passed; the active architecture preserves the
  `browser -> local adapter -> neuriplo-infer` boundary, keeps `neuriplo-ui`
  outside the C++ Gitflow group, and places KServe only under
  `client_server`.
