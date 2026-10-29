# Validation

Milestone: Unified dependency manager as a standalone repo

Status: In progress (coldpac v0.1.2 released 2026-10-29; V-1 to V-7
evidence recorded. Videocapture PR #19 open, merge pending.)

## Results

### coldpac v0.1.2 + videocapture integration, 2026-10-29

Evidence is scheduler-job-shaped so it rebinds to `slurm` unchanged when
the heterogeneous-scheduler packet lands. Runs below were executed by
hand on this Ubuntu 24.04 box, so `executor` reads `local-hand`
(transitional: not yet in the contract enum; becomes `executor=slurm`
on re-run under a scheduled session).

- V-6 (R-1): `videocapture` branch `feat/coldpac-deps`
  ([PR #19](https://github.com/olibartfast/videocapture/pull/19))
  fetches `olibartfast/coldpac` at tag `v0.1.2` via
  `FetchContent_Declare` (`cmake/ColdpacFetch.cmake`), configures from a
  clean scratch dir, and `coldpac validate` passes (4 packages).
  `coldpac-status` output matches the hand-verified `dpkg -l` baseline:
  opencv `4.6.0+dfsg-13.1ubuntu1` ok, ffmpeg `7:6.1.1-3ubuntu5` ok,
  cmake `3.28.3-1build7` ok, gstreamer missing (optional backend, not
  installed -- `dpkg-query` confirms absent). Full build + ctest:
  21/21 pass.
  `evidence: outcome=pass, executor=local-hand, session=coldpac-v06-2026-10-29`.
- V-7 (R-3, R-4): scratch demo (discarded, `/tmp/v7demo`, not merged):
  bumped one apt baseline (`opencv` wanted `==4.6.1`) and one custom-url
  sha256. `status --offline` flags exactly those two entries --
  `drift: installed ... vs wanted ==4.6.1` and
  `stale lock (sha256 changed, re-run resolve)` -- and reports the third
  entry ok; exit 1. The stale-lock check was a coldpac gap found while
  writing this demo; it shipped in `v0.1.2` with a regression test.
  `evidence: outcome=pass, executor=local-hand, session=coldpac-v07-2026-10-29`.
- V-7 correction (packet rule: wrong evidence gets fixed here, with the
  reason): the check as first written said `status` reports
  `Update available`. That was wrong: a bumped baseline is drift and a
  changed pin is a stale lock; `Update available` only fires when the
  provider candidate exceeds a satisfying install. The Manual section
  below is updated to match.

### coldpac v0.1.0, 2026-10-29

- V-1: `scripts/check_platform.py` passes with the contract and packet
  present; all new files ASCII.
- V-2: `python3 tests/run.py` in `olibartfast/coldpac` at `v0.1.0`:
  6/6 pass (fixture validation, unknown-provider rejection,
  mixed-provider lock rejection).
- V-3: `python3 scripts/check_repo.py` passes: every golden fixture
  exports byte-identical `versions.env.expected`; generated files are
  shellcheck-clean `KEY=value` lines.
- V-4: mixed-provider lock entry fails closed (`refusing to silently mix
  providers`); `--offline` skips all network probes (apt/dpkg local reads
  only).
- V-5: `coldpac import` translates the four current `versions.env` key
  shapes (system, backend-binary, sibling, `_MIN_VERSION`/`_REVIEWED_VERSION`
  variants, metadata skips) per `docs/import-map.md`; round-trip verified
  by the export check.
- GitHub release `v0.1.0` published from `main` at `34d289e`.

Written before implementation. Each check names the requirement it closes.

## Automated Checks

- V-1 (R-5): `scripts/check_platform.py` passes with the new contract and
  packet present; all new files are ASCII.
- V-2 (R-2, R-4): A JSON-schema (or equivalent validator in the new repo,
  mirrored by a platform shape check) validates a sample `deps.yaml` /
  `deps.lock` pair covering all six providers (apt, snap, conan, vcpkg,
  custom-url, fetchcontent). Missing required fields fail with the entry
  name and remediation.
- V-3 (R-4): A fixture `deps.yaml` generates a `versions.env` that existing
  consumers can `source` (shellcheck-clean, no unbound vars), and
  `cmake/versions.cmake`-style mapping keys round-trip.
- V-4 (R-3): Provider precedence test: same logical package declared via
  two providers fails closed (no silent mixing), and offline mode performs
  zero network calls (guarded by a network-namespace or proxy-off harness
  in the owning repo; platform records the evidence path).
- V-5 (R-6): Backwards-compat check: current
  `neuriplo/versions.env`, `neuriplo-infer/versions.env`,
  `videocapture/versions.env`, and `neuriplo-kserve-runtime/versions.env`
  each translate losslessly into the new manifest schema (scripted
  comparison, recorded in the packet PR).

## Negative Checks

- No runtime/tool implementation lands in
  `neuriplo-platform`; only contract, ADR, packet, and validators.
- No new system/package dependency is introduced by the packet itself
  (forbidden change class `new-dependency`).
- The manager never redefines backend versions owned by `neuriplo` or task
  semantics owned by `neuriplo-tasks`; drift is reported, not overridden.

## Manual / Attested Checks

- V-6 (R-1): One C++ sibling (smallest: `videocapture`) fetches the new
  repo via `FetchContent_Declare` pinned to a tag, configures from clean,
  and its `status` output matches the hand-verified `dpkg -l` baseline.
- V-7 (R-3, R-4): Update detection demo: bump one apt baseline and one
  custom-url sha256 in a scratch branch; `status` flags exactly those two
  entries (drift for the baseline, stale lock for the pin) and reports
  the rest ok.

## Definition Of Done

V-1 to V-7 pass with dated evidence, the contract leaves `Draft`, the ADR
is `Accepted`, and the roadmap `Now` entry for this packet is marked
complete with the new repo URL and tag.
