# Plan

Milestone: Serve encoded-image requests against dynamic-dimension inputs

Status: In progress (Phase 1 in review)

Phases are thin and in order: each ends in a reviewable, merged state. Roles
are named by capability tier, not by model, so the model behind a role can
change without changing this plan.

## Roles

| Role | Tier | Owns | Write access |
|---|---|---|---|
| planner | strongest | this packet, handoff packets, rejection decisions | `specs/`, handoff files |
| implementer | mid or cheap | one packet's test files | only the paths its packet names |
| reviewer | strongest | diff against packet and requirements | none |
| maintainer | human | Q-1, merges to `master`, tags, attested evidence | everything |

The planner does not repair a rejected diff itself. It sends a corrected,
fresh packet back to the implementer (no silent self-repair).

## Phase 0: Reconcile GitFlow (maintainer-gated)

- Push the local back-merge so `origin/develop` contains the `v0.3.2` merge.
  If the local `develop` carries other unpushed work, push only that commit:
  `git push origin 9030732:develop`.
- Record the baseline test count of `origin/develop` on the `debug`, `grpc`,
  and `asan` presets in a scratch worktree.
- Exit: V-5 precondition, the right-hand count is `0`; the baseline is recorded in
  `validation.md`.

## Phase 1: Lock in the wildcard rule (delegated)

Branch `feature/dynamic-dim-wildcard-tests` from `develop` in a scratch
worktree. The fix exists; this phase only adds tests. If a test fails, that is
a finding, and it goes back to the planner. The implementer does not "fix"
`src/` to make it pass.

Handoff packet P1:

- Writable: `tests/KServeV2CodecTest.cpp`, `tests/GrpcV2CodecTest.cpp`,
  `tests/HttpIntegrationTest.cpp`, `tests/GrpcIntegrationTest.cpp`,
  `tests/NeuriploExecutorTest.cpp`. Nothing else.
- Read-only: `src/KServeV2Codec.cpp` (`shapeMatches`), `src/GrpcV2Codec.cpp`,
  `src/NeuriploExecutor.cpp` (input check), `src/ModelMetadata.hpp`,
  `tests/PipelineTest.cpp` (the existing `{1, -1}` case as the pattern),
  `tests/Test.hpp`, `CMakePresets.json`.
- Obligations: the V-1, V-2, and V-3 cases, table-driven where the existing
  suite is; exact identifiers `IMAGE`, `UINT8`, shape `{1, -1}`.
- Permitted commands: `cmake --preset debug|grpc`, `cmake --build --preset ...`,
  targeted `ctest --preset debug -R <name>` while iterating.
- Acceptance, run once as the last action:
  `ctest --preset debug && ctest --preset grpc`. Report the result whether it
  passes or fails.
- Stop condition: acceptance has run once, or a case fails against unchanged
  `src/`, which is reported as a finding.

Then the reviewer reads the diff against P1 and R-1 to R-3 and rejects or
approves. After approval the maintainer merges the PR into `develop`.

## Phase 2: Release audit (planner and reviewer)

- Pattern audit of `v0.3.2..develop` (about 5.9k lines): untrusted request
  data (shapes, sizes, `binary_data_size`, repository paths), error
  propagation, pipeline reshape, concurrency in the scheduler and repository
  mode, and flags honored per run mode.
- Max-effort code review of the same range. Fix every finding in one batch on
  a `feature/` branch, with tests, re-running V-4. If the batch is large, it
  becomes its own implementer packet (P2) with the same discipline as P1.
- Exit: one consolidated finding list, all closed or explicitly deferred with
  a reason.

## Phase 3: Runtime release (maintainer-gated)

- `release/0.4.0` (Q-1: `v0.4.0`) from `develop`: `VERSION`, `CHANGELOG.md`
  (name the wildcard rule and the encoded-image ensemble path explicitly).
- Release PR to `master`, tag on the merge commit, release CI green, GitHub
  release from the changelog section, back-merge, delete the release branch.
- Exit: V-5.

## Phase 4: Cross-repository proof (maintainer-attested)

- In scratch worktrees: runtime at the new tag; neuriplo-infer at `develop`.
  The runtime is not pinned by neuriplo-infer, so no pin bump is needed.
- Run V-7 and commit the evidence YAML.

## Phase 5: Documentation sync (delegated, cheap tier)

Handoff packet P5, one per repository, same shape as P1:

- neuriplo-infer (`feature/` branch, PR to `develop`): remove the limitation
  from `CHANGELOG.md` `Unreleased`, add a note naming the runtime tag, and
  update `docs/KserveRuntime.md` if it mentions the restriction. Acceptance:
  the repository's lint workflow equivalent.
- neuriplo-platform (`main`): `versions.yaml` runtime pin and compatibility
  sets, the `kserve-ensemble` README version set, `coordination/STATUS.md`,
  `specs/roadmap.md`, and this packet's `Results`. Acceptance: V-6.

The neuriplo-infer note ships with its next release. That release is pin-only
and does not need the full audit.

## Measurement

One run-ledger row per delegated attempt (P1, P2, P5): role, model, tokens
(planner and worker split), tool calls, wall-clock, first-pass acceptance
result, number of rejections. Kept in this packet's `validation.md`
`Results`.

## Risks

- The audit finds release blockers in the unrelated 5.9k-line range. That is
  expected: Phase 2 exists so they surface before the release PR rather than
  during review.
- The planner absorbs context while reviewing a large range. Mitigation: the
  audit is split by subsystem into separate reviewer passes.
- The local runtime checkout has uncommitted work. All phases run in scratch
  worktrees, and nothing is stashed or reset.
