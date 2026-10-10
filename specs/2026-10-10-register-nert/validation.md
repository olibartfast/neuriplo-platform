# Validation

Milestone: Register nert in the multi-repository architecture

Status: Complete

## Automated Checks

1. Run `python3 scripts/check_platform.py` and require exit code 0. The
   validator derives repositories from `ops/CLUSTER_MAP.yaml`, so it checks
   that `nert` appears in `versions.yaml`, has `ops/repo-meta/nert.yaml`, and
   satisfies the non-Gitflow default-branch policy.
2. Run `python3 scripts/check_benchmark_baseline.py versions.yaml`.
3. Run `python3 scripts/generate_compat_report.py --check` and confirm the
   committed report is unchanged (no compatibility set includes `nert`).

## Negative Checks

- `nert` must not appear in any compatibility set.
- No `nert` dependency on `neuriplo` or any other ecosystem repository.
- Existing repository versions and refs in `versions.yaml` are unchanged.
- `neuriplo`'s default backend remains OPENCV_DNN in all platform text.

## Manual Checks

- Review the dependency direction as `neuriplo -> nert`.
- Review ownership: `nert` owns loader, planning, interpreter, and kernels;
  `neuriplo` owns the `NERT` backend adapter and backend selection.
- Confirm the pinned ref exists on https://github.com/olibartfast/nert. This
  needs network access and was not performed in the packet environment.

## Definition Of Done

- The cluster map, repository metadata, version matrix, root registry,
  architecture overview, ownership model, dependency policy, and contributor
  bootstrap map name `nert`.
- ADR 0013 records the extraction decision.
- The platform validation command passes.

## Results

See the handback record for the acceptance command output.
