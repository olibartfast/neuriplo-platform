# Repo Name Migration

This page is the platform reference for legacy repository names during the
`vision-*` to `neuriplo-*` migration. ADR 0004 owns the decision and sequencing;
this document is the quick lookup table used by docs, metadata, and PR reviews.

## Canonical Names

Use the new names in platform metadata, contracts, examples, integration tests,
and runbooks.

| Legacy name | Canonical name | Ownership role | Notes |
|-------------|----------------|----------------|-------|
| `vision-core` | `neuriplo-tasks` | Task contracts, preprocessing, postprocessing, result types | Public API shims are allowed only for the compatibility window defined by ADR 0004. |
| `vision-inference` | `neuriplo-infer` | Local CLI, app configuration, runtime wiring, visualization | The app-owned E2E runner remains in this repo. |
| `neuriplo` | `neuriplo` | Backend abstraction and execution | No rename. |
| `neuriplo-kserve-runtime` | `neuriplo-kserve-runtime` | KServe V2 serving runtime | No rename. |
| `videocapture` | `videocapture` | Video and image source handling | No rename. |
| `vision-ros` | `neuriplo-ros` | ROS consumer of task and backend APIs | External to this platform baseline unless listed in a compatibility set. |
| `tritonic` | `tritonic` | Secondary consumer | No repo rename, but task-library references must move to `neuriplo-tasks`. |

## Review Rules

- New platform references should use `neuriplo-tasks` and `neuriplo-infer`.
- Legacy names are allowed only when documenting migration history, shims, or
  backward compatibility behavior.
- Compatibility evidence should name both the canonical repo and any legacy
  surface being exercised, for example `neuriplo-tasks` forwarding headers for
  old `vision-core/...` includes.
- `versions.yaml`, `ops/CLUSTER_MAP.yaml`, and `ops/repo-meta/*.yaml` must use
  canonical names only.

## Shim Removal

Compatibility shims are temporary. Their lifetime is controlled by ADR 0004 and
the released ecosystem baseline in `versions.yaml`. Do not add new dependencies
on legacy names after the canonical repo names are available.
