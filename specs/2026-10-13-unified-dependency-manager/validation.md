# Validation

Milestone: Unified dependency manager as a standalone repo

Status: Specified, not implemented

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
  custom-url sha256 in a scratch branch; `status` reports
  `Update available` for exactly those entries.

## Definition Of Done

V-1 to V-7 pass with dated evidence, the contract leaves `Draft`, the ADR
is `Accepted`, and the roadmap `Now` entry for this packet is marked
complete with the new repo URL and tag.
