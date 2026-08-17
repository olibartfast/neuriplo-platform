# Plan: Control-Plane Validation Hardening

Milestone: 2026-08-17-control-plane-validation-hardening

Each group is independently implementable, independently reviewable, and ends in
an observable result. Groups 1 and 4 are independent of each other; group 3
depends on group 2. Run `scripts/check_all.py` after each group once group 1
exists.

## Group 1: Single scoreboard command

1. Add `scripts/check_all.py`. It runs the hermetic validation set in a fixed
   order, always all of it, never conditionally:
   - `scripts/check_platform.py`
   - `scripts/check_benchmark_baseline.py versions.yaml`
   - `scripts/generate_compat_report.py --check`
   - `scripts/check_benchmark.py`
   - `integration-tests/failure-modes/run.py`
   - `integration-tests/openai-generative-serving/run.py`
   - `integration-tests/opencv-boundary-v060/run.py`
   - `integration-tests/rfdetr-pose-local-vs-kserve/run.py`
2. Print one line per check with its exit status, then a final `PASS` or `FAIL`
   summary naming every failed check. Exit nonzero if any check failed. Do not
   stop at the first failure; a partial scoreboard is worse than a slow one.
3. Add a `--with-siblings` flag that additionally runs
   `integration-tests/local-inference-smoke/run.py` and
   `scripts/check_component_progress.py`. Document that these need sibling
   checkouts (`scripts/bootstrap.py`) and are not part of the CI gate.
4. Rewrite `.github/workflows/platform-check.yml` so the validate job has one
   check step: `scripts/check_all.py`. Keep checkout, Python setup, and the
   `pyyaml` install steps.
5. Replace the conditional guidance in `AGENTS.md` ("Testing Guidelines" and
   "Build, Test, and Development Commands") and in `CONTRIBUTING.md`
   ("Validation") with the single command. State that CI runs exactly this.

Observable result: `scripts/check_all.py` passes locally, the workflow file
names no individual validator, and the two previously unrun hermetic scenario
checkers now run on every push.

## Group 2: Make benchmark document validation real

1. Decide and document the location of benchmark documents. Baselines stay under
   `integration-tests/<scenario>/baselines/`; a run writes to
   `integration-tests/<scenario>/results/`. Add `results/` to `.gitignore`
   unless a result is being promoted to a baseline.
2. Fix discovery in `scripts/check_benchmark.py` so it validates both
   `integration-tests/**/baselines/*.json` and `integration-tests/**/results/*.json`.
   The current glob matches no directory that exists.
3. Change the empty case from `print("no benchmark result files found"); return 0`
   to a nonzero exit when discovery finds nothing and no explicit path was
   given. Silent success is what hid this for as long as it did.
4. Exclude the ad-hoc ensemble files from benchmark-schema validation until
   group 2 step 5 converts them, so the check can go green immediately. Prefer
   an explicit skip list in the script over a naming trick.
5. Convert `integration-tests/kserve-ensemble/baselines/preprocessing-latency.json`
   to the benchmarking-contract document shape: `benchmark_version`,
   `compatibility_set`, `timestamp`, `hardware`, `backend`, `model`, `results[]`
   with `scenario`, `category`, `batch_size`, `metrics`. Map the existing
   `mean_ms` / `median_ms` / `p95_ms` / `fps` values onto `latency_p50_ms`,
   `latency_p95_ms`, and `requests_per_second`; leave genuinely unmeasured
   fields null, as the contract allows. Keep the original file alongside if the
   raw distribution data is worth retaining.
6. Leave `dali-vs-cpu.json` as an agreement artifact, not a benchmark document.
   It measures detection parity, not throughput or latency. Note this in
   `integration-tests/kserve-ensemble/README.md` so a later reader does not try
   to force it into the benchmark schema.
7. Add an `ensemble-preprocessing-placement` compatibility set to
   `versions.yaml` referencing the converted baseline, so the repository's only
   real measurements are reachable from the version matrix.
8. Remove the skip list entry added in step 4.

Observable result: `scripts/check_benchmark.py` reports a nonzero file count,
`scripts/check_benchmark_baseline.py versions.yaml` resolves the new scenario,
and the ensemble numbers are discoverable from `versions.yaml` rather than only
from `coordination/STATUS.md` prose.

## Group 3: Enforce the declared performance gates

1. Add `scripts/check_benchmark_regression.py`. For each compatibility set in
   `versions.yaml` with `benchmark_baselines`, resolve each scenario's baseline
   document and the matching result document under the scenario's `results/`
   directory, matched by `scenario` and `batch_size`.
2. Compare using the thresholds in `ops/policies.yaml.performance_gates`:
   - `latency_p50_ms`, `latency_p95_ms`, `latency_p99_ms` may exceed baseline by
     at most `latency_regression_pct_max`.
   - `requests_per_second` may fall below baseline by at most
     `throughput_regression_pct_max`.
   - Accuracy-style metrics, where present, may fall by at most
     `accuracy_drop_max` in absolute terms.
3. Skip any comparison where the baseline metric is null, and print a per-set
   count of skipped comparisons. Skip the whole scenario, without failing, when
   no result document exists; the gate must be adoptable before hardware runs
   are automated.
4. Fail with a message naming the scenario, metric, baseline value, measured
   value, and the percentage by which it exceeded the gate.
5. Add the script to `scripts/check_all.py` and to
   `contracts/benchmarking-contract.md` as the contract's named validation
   mechanism.

Observable result: a deliberately regressed result document fails
`scripts/check_all.py` with a message naming the metric, and the repository no
longer declares a threshold that nothing reads.

## Group 4: Ownership and contract lifecycle

1. Add `.github/CODEOWNERS` covering the specifier-owned surface:
   `/contracts/`, `/versions.yaml`, `/ops/policies.yaml`,
   `/integration-tests/**/run.py`, `/integration-tests/**/baselines/`,
   `/specs/`, and `/.agents/`. Assign to the human maintainer.
2. Record in `AGENTS.md` that an implementing agent does not modify baselines,
   scenario runners, or `ops/policies.yaml` as part of making a check pass. A
   failing gate is a finding to report, not an artifact to edit.
3. Add `validate_contracts` to `scripts/check_platform.py`, modelled on the
   existing `validate_runbooks`. For every `contracts/*.md` except `README.md`,
   require: a title line starting with `# `, an `Owner:` line, a `Consumers:`
   line, a `Version:` line, a `Status:` line whose value is one of `Draft`,
   `Review`, `Stable`, `Superseded`, and the sections `## Purpose`,
   `## Compatibility` and `## Validation`. Match section headings by prefix so
   existing variants such as `## Compatibility Rules` continue to pass.
4. Add the missing `Version:` line to all ten contract files, starting at
   `0.1` for each, and keep their existing `Status: Draft`.
5. Update the contract template in `contracts/README.md` so its field list
   matches exactly what the validator enforces, and state the `Status` values.

Observable result: `scripts/check_platform.py` fails when a contract is missing
a lifecycle field, every contract declares a version, and the review requirement
for acceptance artifacts is encoded rather than assumed.

## Sequencing note

Group 1 first: until one command decides the outcome, every later group has to
argue about which checks it should have run.
