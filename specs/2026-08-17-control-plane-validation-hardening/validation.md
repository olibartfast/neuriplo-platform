# Validation: Control-Plane Validation Hardening

Milestone: 2026-08-17-control-plane-validation-hardening

Written before implementation. If a check below turns out to be the wrong
evidence, change it here in the same branch as the code and say why -- do not
adjust it to match whatever was built.

## Automated Checks

The scoreboard command is the gate:

```bash
scripts/check_all.py
```

It must exit 0 on a clean tree and nonzero if any constituent check fails. All
of the following are run by it; each is also listed with the property it proves,
because a green scoreboard that proves nothing is the failure mode this
milestone exists to remove.

| Check | Proves |
|---|---|
| `scripts/check_platform.py` | Metadata, structure, ASCII, and, after group 4, contract lifecycle fields |
| `scripts/check_benchmark_baseline.py versions.yaml` | Every declared baseline scenario resolves to a file inside the repository |
| `scripts/generate_compat_report.py --check` | The generated compatibility report matches `versions.yaml` |
| `scripts/check_benchmark.py` | Benchmark documents conform to the benchmarking contract, over a nonzero file count |
| `scripts/check_benchmark_regression.py` | No measured metric exceeds the gates in `ops/policies.yaml` |
| `integration-tests/failure-modes/run.py` | The failure-mode matrix is well formed |
| `integration-tests/openai-generative-serving/run.py` | Generative serving smoke metadata is well formed |
| `integration-tests/opencv-boundary-v060/run.py` | OpenCV-boundary evidence artifacts are present |
| `integration-tests/rfdetr-pose-local-vs-kserve/run.py` | RF-DETR pose evidence artifacts are present |

Sibling-dependent checks, run manually and not part of the gate:

```bash
scripts/check_all.py --with-siblings
```

## Negative Checks

A gate that has never failed has not been tested. Each of these is performed by
hand during implementation, on a scratch change that is then reverted. Record
the observed error message in the pull request.

1. **Scoreboard reports every failure.** Break two checks at once. The run must
   fail, name both, and not stop after the first.
2. **Empty benchmark discovery fails.** Point discovery at a directory with no
   JSON. `scripts/check_benchmark.py` must exit nonzero, not print
   `no benchmark result files found` and succeed. This is the specific defect
   the milestone was opened for.
3. **Latency regression is caught.** Copy the converted ensemble baseline into
   `results/`, raise `latency_p50_ms` by 6 percent, and confirm
   `scripts/check_benchmark_regression.py` fails naming the scenario, metric,
   both values, and the overage. Repeat at 4 percent and confirm it passes.
4. **Throughput regression is caught in the right direction.** Lower
   `requests_per_second` by 6 percent and confirm failure; raise it by 50
   percent and confirm the gate passes. An improvement must never fail.
5. **Null baselines skip, visibly.** Run the gate against
   `rfdetr-pose-local`, whose baseline metrics are all null. It must pass and
   report the number of skipped comparisons rather than reporting a clean
   comparison it never made.
6. **Missing contract field is caught.** Remove the `Version:` line from one
   contract; `scripts/check_platform.py` must fail naming the file and field.
   Set `Status: Provisional`; it must fail naming the allowed values.
7. **CI runs what the developer runs.** Confirm
   `.github/workflows/platform-check.yml` contains exactly one validation step
   and that no validator is named anywhere in the workflow.

## Manual Checks

- Read `AGENTS.md` and `CONTRIBUTING.md` end to end and confirm no instruction
  tells a contributor to run a subset of checks, or to decide which checks apply
  based on what changed.
- Confirm `.github/CODEOWNERS` paths resolve to real files and directories, and
  that no path in it is one an implementing agent is expected to edit routinely.
- Confirm the converted ensemble baseline still reports the same measurements as
  the original file. The conversion is a reshaping, not a re-measurement; any
  changed number means a mapping error.
- Confirm `coordination/STATUS.md` links to the ensemble baseline rather than
  restating its numbers, so the derived values have one home.
- Verify every relative link added by this milestone resolves, per the
  documentation rule in `AGENTS.md`.

## Definition of Done

- `scripts/check_all.py` exists, runs the full hermetic set unconditionally, and
  is the only validation step in `.github/workflows/platform-check.yml`.
- `scripts/check_benchmark.py` validates a nonzero number of documents and fails
  when discovery is empty.
- `scripts/check_benchmark_regression.py` enforces every threshold declared in
  `ops/policies.yaml.performance_gates`, and each threshold has been observed to
  fail once and pass once.
- The `kserve-ensemble` preprocessing measurements conform to the benchmarking
  contract and are referenced by a compatibility set in `versions.yaml`.
- All ten contracts declare `Version` and a `Status` from the closed set, and
  `scripts/check_platform.py` fails if one does not.
- `.github/CODEOWNERS` covers contracts, scenario runners, baselines,
  `versions.yaml`, `ops/policies.yaml`, `specs/`, and `.agents/`.
- `AGENTS.md` states that gates and baselines are not editable in service of
  making a check pass.
- No threshold, contract field, or validator named in this repository is left
  without something that reads it. If one cannot be enforced yet, it is recorded
  as out of scope in [requirements.md](requirements.md) rather than left
  declared and inert.
- The pull request records the negative-check output, per
  `ops/PR_EVIDENCE_TEMPLATE.md`.
