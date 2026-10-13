# Plan

Milestone: Unified dependency manager as a standalone repo

Status: Specified, not implemented

Each group is independently implementable, reviewable, and ends in an
observable result. Implementation lands in the new standalone repo; platform
work lands here.

## Group 1: Contract and decision record (platform, this repo)

- Write `contracts/dependency-manifest-contract.md` (Draft): manifest,
  lockfile, `versions.env` projection, provider set, precedence/fallback,
  offline, diagnostics, compatibility rules, validation strategy, examples.
- Write ADR 0013 (standalone fetched repo vs platform code vs extending
  `neuriplo-infer` scripts); record D-1/D-2/D-3 from requirements.
- Register the packet in `specs/roadmap.md` Now; list the contract in
  `contracts/README.md`.
- Observable: V-1 passes (`scripts/check_platform.py`).

## Group 2: Schema and golden fixtures (new repo, specified here)

- Define `deps.yaml` schema (one entry: name, kind, wanted, providers[],
  components, linkage, platforms, license note) and `deps.lock` schema
  (resolved version, provider used, coordinates, sha256, source date).
- Ship golden fixtures covering apt, snap, conan, vcpkg, custom-url,
  fetchcontent, plus precedence-conflict and offline fixtures.
- Observable: V-2 passes in the new repo CI; platform records the tag.

## Group 3: versions.env projection and migration map (new repo)

- Implement `coldpac export versions.env` (and `cmake -D` override
  precedence preserved) plus `coldpac import` for the four existing
  `versions.env` files.
- Publish the losslessness table (old key -> manifest entry -> lock entry).
- Observable: V-3 and V-5 pass.

## Group 4: Status and update detection (new repo)

- Implement `coldpac status` (wanted vs installed vs update-available) and
  `coldpac check-updates` (apt candidate, conan/vcpkg registry, URL HEAD,
  sibling tag listing). No silent multi-provider mixing (V-4).
- Observable: V-4 passes; V-7 demo recorded as evidence YAML.

## Group 5: First consumer integration (videocapture, then neuriplo)

- `videocapture` fetches the manager via `FetchContent_Declare` pinned to
  a tag; `status` output matches `dpkg -l`; apt-baseline workflow in its
  docs points at the manager.
- Follow-up (not this packet): roll out to `neuriplo`, `neuriplo-infer`,
  `neuriplo-kserve-runtime`; retire duplicated `setup_*.sh` logic.
- Observable: V-6 passes; platform `versions.yaml` notes the consumer pin
  (tooling pin, not a compatibility set bump).
