# Requirements

Milestone: Unified dependency manager as a standalone repo

Status: In progress (coldpac v0.1.0 released 2026-10-29; consumer
integration pending)

## Problem

Dependency truth is fragmented across the six C++ siblings:

- [`neuriplo`](https://github.com/olibartfast/neuriplo) owns `versions.env`
  backend pins (`OPENVINO_VERSION`, `ONNX_RUNTIME_VERSION`, ...) plus
  per-backend `scripts/setup_*.sh` curl tarballs.
- [`neuriplo-infer`](https://github.com/olibartfast/neuriplo-infer) duplicates
  that logic in `scripts/setup_dependencies.sh`, maps sibling pins in its own
  `versions.env` (`NEURIPLO_VERSION`, `VIDEOCAPTURE_VERSION`, ...), and copies
  upstream pins via `scripts/update_backend_versions.sh`.
- [`videocapture`](https://github.com/olibartfast/videocapture) tracks Ubuntu
  apt baselines in `versions.env` and reports drift with
  `scripts/check_dependency_updates.sh` (`dpkg --compare-versions`).
- [`neuriplo-kserve-runtime`](https://github.com/olibartfast/neuriplo-kserve-runtime)
  pins siblings in a minimal `versions.env`.
- System deps (`find_package(OpenCV)`, `find_package(glog)`) are apt-only
  assumptions; sibling code is `FetchContent_Declare`. There is no snap,
  conan, or vcpkg coverage, and no single `status` view per project.

There is no place that answers: what does project X need, what is installed,
what is outdated, and how is each item fetched regardless of provider.

## In Scope

- R-1: A standalone repo (coldpac under
  `olibartfast`, no `neuriplo-` prefix per owner request) that is fetched by
  the C++ siblings (CMake `FetchContent` / submodule, same pattern as
  [`neuriplo-kserve-client`](https://github.com/olibartfast/neuriplo-kserve-client)).
- R-2: One manifest schema per project (`deps.yaml`): declared intent with
  provider-agnostic entries (name, wanted version/range, provider hint,
  components, linkage, platform constraints).
- R-3: Provider encapsulation behind one interface for v1: `apt`, `snap`,
  `conan`, `vcpkg`, `custom-url` (curl tarball/zip with pinned sha256), and
  `fetchcontent` (sibling pins). Precedence, fallback, and offline behavior
  are explicit per entry.
- R-4: Tracking outputs per project: resolved `deps.lock` plus generated
  `versions.env` (backwards compatible with existing `source versions.env`
  consumers), and a `status` report (wanted vs installed vs update-available).
- R-5: Platform contract (`contracts/dependency-manifest-contract.md`)
  defining manifest/lockfile/`versions.env` shapes, ownership, and validation
  strategy. Implementation stays in the new repo per ADR 0003.
- R-6: Migration path for the four existing `versions.env` files and the
  `setup_*.sh` / `check_dependency_updates.sh` scripts, without breaking
  `cmake -D > versions.env` precedence.

## Out Of Scope

- Moving backend version policy out of
  [`neuriplo`](https://github.com/olibartfast/neuriplo); the manager consumes
  that policy, it does not redefine it.
- Docker image builds, Helm charts, release tagging, or SBOM signing; those
  stay in owning repos per dependency-policy.
- A hosted update feed or auto-merge bot; update detection is local
  (`apt candidate`, registry query, URL HEAD) plus a human-reviewed bump.
- Python/Node package management; v1 covers C++/system deps only.
- Live GPU/benchmark evidence; the gate stays hermetic.

## Constraints

- Runtime/tool code stays out of
  [`neuriplo-platform`](https://github.com/olibartfast/neuriplo-platform);
  this packet records contract and evidence only.
- New system/package/runtime dependencies remain a forbidden change class
  for automation (`ops/policies.yaml`); bumps need human review.
- Files stay ASCII; scripts stay small, executable, Python 3.12 or POSIX sh.
- C++ siblings keep GitFlow (`develop` / `feat/*`, `master` release-only).
- Backwards compatibility: existing `source versions.env` and
  `cmake/versions.cmake` mappings keep working during migration.

## Decisions Taken

- D-1 (2026-10-13, owner): standalone repo, fetched where needed, not a
  `neuriplo-` prefixed name.
- D-2 (2026-10-13, owner): day-1 provider matrix includes conan and vcpkg,
  not just apt + custom URLs.
- D-3 (2026-10-13, owner): tracking shape is unified manifest + lockfile,
  not check-only and not a full installer on day one; install/upgrade
  executes only what the lockfile pins.

## Open Questions

- Q-1: Repo creation. Decided 2026-10-13 by the owner: `coldpac` under
  `olibartfast`, no `neuriplo-` prefix. Scaffold lives at
  `../coldpac`; creation as a GitHub repo plus first tag is the remaining
  step, with no consumer rollout in this packet.
- Q-2: Whether snap support ships in v0.1.0 or follows as v0.2.0; snap
  needs a host with snapd, which hermetic CI lacks.
