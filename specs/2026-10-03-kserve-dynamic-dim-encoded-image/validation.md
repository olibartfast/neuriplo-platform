# Validation

Milestone: Serve encoded-image requests against dynamic-dimension inputs

Status: In progress (Phase 0 complete)

Written before implementation. Each check names the requirement it closes. The
runtime commands run in a scratch worktree of `neuriplo-kserve-runtime` at the
phase's branch.

## Automated Checks

- V-1 (R-1): New `KServeV2CodecTest`, `GrpcV2CodecTest` or
  `GrpcIntegrationTest`, and `HttpIntegrationTest` cases send a concrete
  request dimension against a metadata `-1`, for a plain model and a pipeline
  model with an `IMAGE UINT8 [1, -1]` input, through HTTP JSON, HTTP binary, and
  gRPC. All are accepted and reach the executor with the request's shape.
- V-2 (R-2): Table-driven rejection cases on the same paths: rank mismatch,
  concrete mismatch, request dimension `-1`, non-integer dimension, and
  payload/shape count mismatch. Each returns 400 or `INVALID_ARGUMENT`, and the
  message names the input.
- V-3 (R-3): After a wildcard request succeeds, the model metadata (HTTP and
  gRPC) still reports `-1` for the dynamic axis.
- V-4 (R-1 to R-3): The full suite stays green with no regressions:
  `cmake --preset debug && cmake --build --preset debug && ctest --preset debug`,
  plus the `grpc` and `asan` presets. Baseline count recorded before Phase 1.
- V-5 (R-4): `git rev-list --left-right --count origin/develop...origin/master`
  has a right-hand count of `0` before the release (`master` holds nothing
  `develop` lacks) and prints `0 0` after the back-merge. The tag resolves to the `master` merge commit, and the runtime's
  release CI passes on the tag.
- V-6 (R-6): `scripts/check_platform.py` and
  `scripts/generate_compat_report.py --check` pass with the new runtime pin, and
  ref integrity verifies every repository.

## Negative Checks

- `BatchCompatibility` still rejects `BYTES` tensors.
- No change in `neuriplo-infer/app/` or in `neuriplo-kserve-client`.
- A metadata dimension that is concrete is never treated as a wildcard.

## Manual / Attested Checks

- V-7 (R-5): Serve an ensemble whose input is `IMAGE UINT8 [1, -1]` from the
  release build. Run neuriplo-infer
  `--input_mode=encoded-image --task_model=<inner>` over `--kserve_transport=http`
  and `grpc` on a JPEG, once with `--postprocess_mode=cpu` and once with `gpu`.
  Each exits 0 with detections. The same run against `v0.3.2` is rejected,
  which shows the check discriminates. Recorded as an evidence YAML next to
  `integration-tests/kserve-ensemble/`.
- V-8 (R-6): The known limitation is gone from neuriplo-infer
  `CHANGELOG.md` `Unreleased`, with a note naming the runtime release, and the
  `kserve-ensemble` README version set names the tag.

## Definition Of Done

V-1 to V-8 pass with dated evidence below, the runtime tag is published, and
the platform matrix pins it.

## Results

### Phase 0, 2026-10-03

- GitFlow reconcile: the content-neutral back-merge `9030732` (`v0.3.2` merge
  reachable from `develop`) was pushed to `origin/develop` as a fast-forward
  (`f4e4bff..9030732`).
  `git rev-list --left-right --count origin/develop...origin/master` prints
  `12 0`. V-5 precondition met.
- Baseline at `origin/develop` `9030732`, scratch worktree. CTest registers 3
  entries (`unit`, `version`, `help`); the `unit` binary
  `neuriplo-kserve-runtime-tests` holds the cases:

  | Preset | CTest | Unit cases |
  |---|---|---|
  | `debug` | 3/3 pass | 317 pass |
  | `grpc` | 3/3 pass | 338 pass |
  | `asan` | 3/3 pass | 317 pass |

  V-4 compares Phase 1 against these counts: they may only grow, with no
  failures.
