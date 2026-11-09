# Validation

Milestone: Local TensorFlow GPU and remote TPU serving

Status: Implemented; compatibility evidence pending

## Automated Checks

1. Run `python3 scripts/check_platform.py` and require exit code 0. This
   validates YAML metadata, required docs, ASCII content, and version policy.
2. If `versions.yaml` changes, run `python3 scripts/generate_compat_report.py --check`
   and confirm the committed report matches.
3. Run the repository's ASCII check through `scripts/check_platform.py`; do not
   add non-ASCII punctuation to contracts or runbooks.
4. Run the link check used by the platform docs for every new relative link and
   absolute GitHub URL.

## Negative Checks

- The configuration contract must not add `tpu` as a client `device` value.
- No platform text may claim an in-process TPU backend.
- No platform text may require `neuriplo-kserve-client` or
  `neuriplo-kserve-runtime` source changes for this milestone.
- No compatibility set may be marked `active` before the GPU and TPU evidence
  from the owning repositories is attested.
- No repository ownership or dependency direction may move into
  `neuriplo-platform`.

## Manual Checks

- [x] [M-1] Review the TPU serving contract as a client author. Confirm it
  states who owns device placement, model naming, health, and errors.
  Reviewed; the service owns placement, compiler, runtime, and lifecycle, while
  the client selects endpoint/model/version and owns task preprocessing.
- [x] [M-2] Review the runbook as an operator. Confirm it includes prerequisites,
  exact commands, expected output, teardown, and cost notes.
  Reviewed; `ops/runbooks/tpu-serving.md` includes quota, create/SSH/SCP/delete
  commands, CPU and TPU artifact checks, service checks, client invocation,
  top-5 comparison, diagnosis, cost/teardown, and evidence recording.
- [x] [M-3] Confirm the architecture note does not imply that TPU is a local
  accelerator option.
  Reviewed; the note places TPU inside remote KServe client mode, not embedded
  local mode.
- [ ] [M-4] Confirm the compatibility set records the TPU service identity, not
  only the C++ client/runtime pins.
  Deferred; no compatibility set exists because no attested GPU or TPU evidence
  exists. This is intentional and is recorded in the plan and runbook.

## Definition Of Done

- [x] `contracts/configuration-contract.md` distinguishes local GPU from remote
  TPU.
- [x] `contracts/tpu-serving-contract.md` exists and is linked from the
  contracts index.
- [x] `docs/architecture/inference-modes.md` and
  `ops/runbooks/tpu-serving.md` describe the same service boundary.
- [ ] `versions.yaml` has a draft compatibility set only after evidence exists.
  Correctly not added: no attested GPU or TPU evidence exists. The missing
  compatibility set is intentional, not an omission.
- [x] `specs/roadmap.md` lists this packet with an honest status.
- [x] Platform validation passes.
- [x] Results are recorded in this file, including checks that could not run.

## Results

- `python3 scripts/check_platform.py`: PASS (exit 0, output
  `platform metadata ok`). YAML metadata, required docs, runbooks, ASCII
  content, and version policy passed.
- `versions.yaml` is unchanged in this branch, so
  `python3 scripts/generate_compat_report.py --check` was not run and the
  committed compatibility report is unaffected.
- Relative links in `contracts/tpu-serving-contract.md`,
  `contracts/configuration-contract.md`, `contracts/README.md`,
  `docs/architecture/inference-modes.md`, `ops/runbooks/tpu-serving.md`, and this
  packet were verified to resolve to existing files. Absolute GitHub URLs are
  left as published references.
- GPU and TPU live hardware checks were not executed in this environment. No
  local GPU or remote TPU service was available, so no runtime evidence is
  claimed.
- The compatibility set is intentionally absent: `versions.yaml` has no draft or
  active set for this milestone because no attested GPU or TPU evidence exists.

## Deviations

- Deferred hardware evidence: GPU and TPU live checks were not run, so none of
  the owning repositories' hardware results are attested here. The contract,
  architecture note, and runbook describe the intended boundary only.
- Deferred compatibility evidence: the intentional missing `versions.yaml`
  compatibility set is a deviation from "add a draft compatibility set" in the
  plan. It is deliberate; a set may be added only after the GPU and TPU evidence
  from the owning repositories is recorded, and it must not be promoted to
  `active` without attested hardware results.

