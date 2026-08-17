# Requirements: Control-Plane Validation Hardening

Milestone: 2026-08-17-control-plane-validation-hardening

Owner: `neuriplo-platform` (human), executed by the platform agent role

Status: Draft

## Goal

Make the checks this repository already declares actually decide the outcome of
a change. Today [`neuriplo-platform`](https://github.com/olibartfast/neuriplo-platform)
declares performance gates, a benchmarking contract, and a set of validators,
but the declarations and the enforcement have drifted apart:

- `scripts/check_benchmark.py` discovers result files under
  `integration-tests/**/results/*.json`. No `results/` directory exists in the
  repository, so the script validates zero files, prints
  `no benchmark result files found`, and exits 0. It is also not referenced by
  `.github/workflows/platform-check.yml`.
- Two hermetic scenario checkers (`integration-tests/opencv-boundary-v060/run.py`
  and `integration-tests/rfdetr-pose-local-vs-kserve/run.py`) are never run by
  CI, although they need no sibling checkout, no GPU, and no live server.
- `ops/policies.yaml` declares `performance_gates` (5 percent latency and
  throughput regression ceilings, 0.01 accuracy drop) and nothing compares any
  measurement against them.
- All three benchmark baselines referenced by `versions.yaml` contain null
  metrics only. The only baselines holding real measurements
  (`integration-tests/kserve-ensemble/baselines/`) use an ad-hoc schema, do not
  follow [the benchmarking contract](../../contracts/benchmarking-contract.md),
  and are referenced by no compatibility set.
- Every file in `contracts/` carries `Status: Draft` and none carries a
  `Version` field, although `contracts/README.md` prescribes both. No validator
  reads `contracts/` at all, making the repository's most load-bearing
  directory its least checked one.
- Contributors and agents are told to run different subsets of checks depending
  on what changed (`AGENTS.md`, "Testing Guidelines"). No single command
  reproduces what CI runs.

After this milestone, one command decides pass or fail, that command is what CI
runs, and the gates named in `ops/policies.yaml` either enforce or are removed.

## In Scope

1. A single scoreboard command that runs the full hermetic validation set, and a
   CI workflow that invokes only that command.
2. Repairing `scripts/check_benchmark.py` discovery so it validates the benchmark
   documents that exist, and adding it to the scoreboard.
3. A regression gate that compares a benchmark result against its declared
   baseline using the thresholds in `ops/policies.yaml`.
4. Bringing the `kserve-ensemble` measurements under the benchmarking contract
   and referencing them from a compatibility set in `versions.yaml`.
5. A `CODEOWNERS` file establishing that acceptance artifacts (contracts,
   scenario runners, baselines, `versions.yaml`) are specifier-owned.
6. A contracts validator in `scripts/check_platform.py` enforcing the header
   fields that `contracts/README.md` already prescribes, plus a `Version` field
   and a closed set of `Status` values.

## Out of Scope

Explicitly not part of this milestone. Each is a candidate for a later packet.

- Producing real GPU measurements for the currently null baselines
  (`rfdetr-pose-local`, `rfdetr-pose-kserve-grpc`, `ecdet-kserve-http`). This
  milestone makes the gate work on populated baselines and skip null ones; it
  does not run hardware.
- Cross-repository build and test CI that compiles pinned refs from source
  (production roadmap item 2). The scoreboard here stays hermetic.
- Promoting any contract out of `Draft`. This milestone adds the lifecycle
  fields and validation; deciding that a contract is `Stable` is a human review
  step taken per contract, later.
- Generating per-role agent definitions with write allowlists from
  `ops/CLUSTER_MAP.yaml`.
- Changing the `coordination/` inbox message format to a handoff-packet shape.
- A validator for `specs/` itself. The convention is established by this
  milestone being written; enforcing it can wait until a second packet exists.
- Any change inside a sibling implementation repository. Nothing here needs one.

## Decisions

- **The scoreboard runs the hermetic set by default.** Sibling-dependent checks
  (`integration-tests/local-inference-smoke/run.py`,
  `scripts/check_component_progress.py`) and live-serving scenarios
  (`kserve-ensemble`, `kserve-runtime-yolo-e2e`,
  `kserve-runtime-edgecrafter-e2e`) run only behind an explicit flag. A command
  that silently means something different on a laptop than in CI is not a
  scoreboard.
- **CI calls the scoreboard and nothing else.** Steps enumerated in the workflow
  are how the current drift happened; the workflow must not be able to run a
  different set than a contributor does.
- **The regression gate skips null metrics rather than failing on them.** A
  placeholder baseline means "not yet measured", which is honest and already
  recorded; treating it as a failure would make the gate impossible to adopt
  before hardware runs happen. The gate reports how many comparisons it skipped
  so the number is visible rather than silent.
- **Comparison direction is fixed per metric.** Latency higher than baseline is
  a regression; throughput lower than baseline is a regression; accuracy lower
  than baseline is a regression. Improvements never fail the gate.
- **Contract `Status` becomes a closed set:** `Draft`, `Review`, `Stable`,
  `Superseded`. Existing files keep `Draft` and gain `Version: 0.x`, so the
  validator can land without a documentation rewrite.
- **`CODEOWNERS` encodes ownership that already exists** in
  `ops/CLUSTER_MAP.yaml` and `AGENTS.md`. It adds review requirements, not new
  ownership claims.

## Constraints and Context

- This repository is a control plane. No runtime implementation may move here
  (`AGENTS.md`, "Architecture Rules"). Every change in this milestone is a
  validator, a metadata file, or a document.
- All files must be ASCII. `scripts/check_platform.py` enforces this across the
  whole tree.
- Scripts must be small, dependency-light, executable, and Python 3.12
  compatible. The only third-party import in use is `pyyaml`; this milestone
  adds none.
- Platform work lands on `main`; sibling Gitflow rules do not apply here
  (`.agents/rules/always-apply.md`).
- The scoreboard must stay runnable on a machine with no GPU, no sibling
  checkouts, and no network access to a serving endpoint. CI runs
  `ubuntu-latest` with `pyyaml` installed and nothing else.
- Prior art for the validator style is `validate_runbooks` and
  `validate_integration_tests` in `scripts/check_platform.py`: read the file,
  assert required sections, collect errors, exit nonzero with clear messages.
- The measurements this milestone brings under contract were produced by
  `integration-tests/kserve-ensemble/benchmark_preprocessing.py` and
  `compare_preprocessing.py`. Their existing JSON output is the input to the
  schema work, not something to re-run.
