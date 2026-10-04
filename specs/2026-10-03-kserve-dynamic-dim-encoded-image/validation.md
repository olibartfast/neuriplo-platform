# Validation

Milestone: Serve encoded-image requests against dynamic-dimension inputs

Status: In progress (Phase 2 fix batch running)

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

### Phase 1 replan, 2026-10-03

Review of the first attempt showed that V-1 and V-3, as written, cannot be met
by tests alone. `HttpIntegrationTest` serves models through `StubExecutor`,
whose metadata is hard-coded (`src/StubExecutor.cpp`), so an endpoint-level
test with a `{1, -1}` input needs a `src/` test seam, which Phase 1 forbids.
The requirements are unchanged; the evidence is located as follows:

- V-1, HTTP: covered at `parseInferenceRequest`, the function the HTTP server
  calls, for JSON data and the binary extension. gRPC: the codec test shows
  the concrete shape is carried through `convertInferRequest`; validation is
  the executor's, covered by the executor tests. Pipeline model: the existing
  `PipelineTest` `IMAGE UINT8 {1, -1}` case.
- V-3: checked on the executor's reported metadata after an accepted request,
  not through the HTTP/gRPC metadata endpoints.
- Deferred to Phase 4 (end to end): endpoint-level acceptance and metadata over
  a real served ensemble, which V-7 exercises anyway.

### Run ledger

| Attempt | Role | Model tier | Tokens | Tool calls | Wall-clock | Acceptance | Outcome |
|---|---|---|---|---|---|---|---|
| P1 | implementer | mid | 60k | 10 | 98 s | pass (325 / 347) | Rejected by review: three rejection rows passed for the wrong reason (a later count check also names `IMAGE`) |
| P1 review | reviewer | strongest | 30k | 8 | 66 s | n/a | REJECT, 3 blocking, 4 nits |
| P1b | implementer (fresh) | mid | 48k | 8 | 54 s | pass (325 / 347) | Specific message per row; `[2,5]` given 10 values |
| P1b review | reviewer (fresh) | strongest | 31k | 6 | 49 s | n/a | APPROVE, 0 blocking; nit: no row tested the rank check alone |
| P1c | implementer (fresh) | mid | 44k | 8 | 49 s | pass (325 / 347) | Rank-only rows `[1]` / `{1}`; helpers into one namespace |

Planner interventions: no source repair. The planner ran `clang-format` once,
a mechanical change to one line in a new table row. The acceptance script
had no format check, which is a planner gap; acceptance for later phases runs
`scripts/check-format.sh`.

### Phase 1 result, 2026-10-03

Branch `feature/dynamic-dim-wildcard-tests` at `f5ef1df`,
[neuriplo-kserve-runtime#17](https://github.com/olibartfast/neuriplo-kserve-runtime/pull/17)
to `develop`. Tests only; no `src/` change.

- V-1, V-2, V-3 (as scoped by the replan): met. 8 + 1 + 0 new cases in
  `KServeV2CodecTest`, `NeuriploExecutorTest` and `GrpcV2CodecTest`; every
  rejection row asserts the message of the check it targets.
- V-4: `debug` 325 (was 317), `grpc` 347 (was 338), `asan` 325 (was 317), all
  passing; `scripts/check-format.sh` and the `lint` clang-tidy build pass.
- Mutation evidence. Each check was disabled alone on the debug build and then
  restored:

  | Mutation | Caught by |
  |---|---|
  | codec: request `-1` | `kserve_v2_codec_dynamic_dim_rejects_bad_requests` |
  | codec: concrete dimension | that case and `kserve_v2_codec_concrete_dims_stay_strict` |
  | codec: wildcard removed | the three accept cases and the reject case |
  | codec: rank | `kserve_v2_codec_dynamic_dim_rejects_bad_requests` |
  | executor: request `-1` | `neuriplo_executor_dynamic_dim_rejects_bad_requests` |
  | executor: concrete dimension | that case and `neuriplo_executor_concrete_dims_stay_strict` |
  | executor: wildcard removed | the accept case, the reject case, and the existing pipeline case |
  | executor: rank | `neuriplo_executor_dynamic_dim_rejects_bad_requests` |

- For the Phase 2 audit: `src/KServeV2Codec.cpp` runs the `shapeMatches` check
  twice in a row in `parseInferenceRequest`. It is harmless and redundant.

Phase 1 closed 2026-10-04: #17 merged into `develop` as `165dec0`, with all 12 CI checks green.

### Phase 2 audit result, 2026-10-04

Three read-only reviewer passes over `v0.3.2..165dec0`, one per subsystem,
plus the planner's own build checks. Findings: 4 BLOCKER, 16 MAJOR, 31 MINOR
(slice A pipeline 4/10, slice B repository 3 blockers/8/10, slice C deploy
4/10, planner 2). Raw reports: `phase2/findings-{A,B,C}.md` in the planner's
scratch space; the dispositions below are the record.

Planner findings:

- G-1 BLOCKER: the pinned neuriplo-tasks v0.8.0 lacks `decodeImage` (added in
  v0.8.1), so `NEURIPLO_RUNTIME_ENABLE_TASKS=ON`, the build that serves
  encoded-image ensembles, does not compile. No CI job builds it. Verified:
  tasks v0.8.2 + neuriplo v0.10.0 builds and passes 357/357.
- G-2 MINOR: `CMakeLists.txt` uses plain `set()` for the pins, so
  `-DNEURIPLO_TASKS_VERSION=...` cannot override `versions.env`.

Fix batch (one feature branch and PR per packet):

| Packet | Tier | Findings |
|---|---|---|
| P2-A pipeline + build | strongest | G-1 (pins tasks v0.8.2, neuriplo v0.10.0; CI job with tasks on), G-2, A-1, A-2, A-3, A-4, A-5, A-6, A-10 (FRAME_SIZE datatype only), A-11, A-12 (wrong types only), A-14, duplicated `shapeMatches` |
| P2-B1 lifecycle | strongest | B-1, B-2 (+ wrong-typed admin fields 400), B-3, B-8, B-12, B-17 |
| P2-B2 repository/config | strongest | B-4, B-5, B-6, B-7, B-10, B-11, B-13, B-14, B-15, B-16 + C-8, B-19, B-20, B-21, A-7 |
| P2-C deploy | mid | C-1, C-2, C-4, C-5, C-6, C-10, C-11, C-12, C-13, C-14 |
| P2-D changelog | mid | C-3 / B-9, and every user-visible change above |

Deferred, with reason (each goes to the runtime `specs/roadmap.md`
follow-ups):

- A-8 (cancellation not propagated into steps), A-9 (step failure status
  codes), A-10 edge-type checks, A-12 unknown keys, B-18 and the matching
  slice A note (ensembles stay ready when a step model is unloaded; cached
  step metadata goes stale): these are correctness-of-diagnostics or
  operability issues on paths with no wrong-answer outcome, and each needs a
  design choice that does not belong in a release batch.
- A-13 (ensemble contract: `platform` for model-first graphs,
  `max_batch_size`): this is a contract question, so it is raised against
  `contracts/ensemble-contract.md` and not changed unilaterally.
- C-7 (images and pods run as root) and C-9 (`Dockerfile.tensorrt` builds from
  the context checkout): the fix needs a k3d/GPU validation run with `fsGroup`
  on the PVC, which this packet cannot attest. Listed as a known limitation in
  the v0.4.0 notes.
- Admin and repository routes are unauthenticated and accept arbitrary
  `model_path` / `plugin_dir`. That is the pre-existing design, and the
  release notes state it as a known limitation.
- gRPC codec does no metadata validation (pre-existing; executors validate).

### Early Phase 4 smoke, 2026-10-04

Ahead of the release, to de-risk V-7: runtime `develop` `165dec0`, real ONNX
Runtime + gRPC + task steps, with tasks pinned to v0.8.2 in a scratch build
(v0.8.0 does not compile, G-1). Model `yolo26s.onnx`; ensembles
`yolo-detection.json` (pre + model + post envelope) and a pre + model graph;
both advertise `IMAGE UINT8 [1, -1]`. Client: neuriplo-infer v0.10.0 build
(this path is unchanged through v0.10.2) on `data/dog.jpg`.

| Transport | Postprocess | Graph | Exit | Detections |
|---|---|---|---|---|
| HTTP | gpu (envelope) | pre + model + post | 0 | bicycle 0.94, dog 0.93, truck 0.54 |
| HTTP | cpu | pre + model | 0 | rendered |
| gRPC | gpu (envelope) | pre + model + post | 0 | rendered |
| gRPC | cpu | pre + model | 0 | bicycle 0.94, dog 0.93, truck 0.54 |

Server-side and client-side postprocessing rendered identical boxes and
scores. `--postprocess_mode=cpu` against the envelope graph is correctly
refused by the client; the ensemble README is to document the pre + model
graph for that mode (P2-A). This is not the V-7 record: V-7 is re-run on the
release tag.

### Phase 2 fix batch progress, 2026-10-04

| Packet | Runtime PR | Merge | Review rounds | Local acceptance |
|---|---|---|---|---|
| P2-C deploy | #19 | 746b54a | 2 | 135/135 preparer suite, dash + busybox + shellcheck |
| P2-A pipeline + build | #21 | 35cc57a | 4 (general, then three A-3 parser rounds) | debug 333, grpc 355, debug-tasks 348 |
| P2-B1 lifecycle | #22 | 2b844e9 | 3 (concurrency focus) | debug 350, grpc 372, tsan 350, no TSan warnings |
| P2-B2 repository/config | pending | | | baseline debug 358, grpc 380 |
| P2-D changelog | pending | | | |

A-3, the pre-decode pixel cap, needed three security rounds. Round 1 found
an overflow, a JPEG fill-byte bypass and a CgBI bypass. Round 2 found
inter-segment padding, an `FF FF D8` SOI, CgBI runs of 8 or more, and
misread BMP core headers. Round 3 ran about 9M differential fuzz inputs
against `stbi_info_from_memory` under ASan/UBSan, with 0 bypasses, and asked
for one more test, the core-BMP huge-dims test; a mutant without that branch
gave 5095 bypasses in 200K inputs.

Planner mutation check on P2-B1: removing the post-swap `notify_all` hangs
the suite, and counting Loading placeholders in `allReady` fails it.

Run ledger additions. The implementers ran the strongest tier with a
12-turn limit per run.

| Attempt | Role | Tokens (cumulative) | Resumes | Acceptance runs | Outcome |
|---|---|---|---|---|---|
| P2-A | implementer | ~356k | 9 | 3 (one per correction round) | approved after round 4 |
| P2-B1 | implementer | ~399k | 10 | 3 | approved after round 3 |
| P2-C | implementer (mid) | n/a | 2 | 2 | approved after round 2 |
| A-3 rounds 2/3 | reviewer | 35k / 47k | 1 / 0 | n/a | REJECT / REJECT (test gap only) |
| P2-B1 round 2 | reviewer | 116k | 0 | n/a | REJECT (flaky test only) |

Interventions:
- Planner gap: `acceptance.sh` diffed against `origin/develop`, which moved
  during the batch, so a correct P2-A run failed its scope check. The check
  now diffs against `HEAD`, and the planner re-scored that run (PASS).
- No planner source repair.
- The implementers repeatedly spent their first run reading. Smaller packets
  would cut the number of resumes.
- Side task, owner request: the runtime and client `plan/` folders were
  ported into `specs/` and removed (runtime #20, client #9). In the client
  run, the implementer ran acceptance three times instead of once.
