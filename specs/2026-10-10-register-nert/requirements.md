# Requirements

Milestone: Register nert in the multi-repository architecture

Status: Complete

## Goal

Make [`nert`](https://github.com/olibartfast/nert), the Neuriplo Engine Runtime,
a first-class component in the Neuriplo architecture control plane and record
its dependency relationship with `neuriplo`.

## In Scope

- Add repository, checkout, ownership, dependency, and automation metadata.
- Pin the current public repository state as WIP in `versions.yaml` (version
  0.1.0 is unreleased; ref `81b6b1f824655403742e727853afe05261dae5d0`).
- Record the extraction decision in ADR 0013.
- Document the `neuriplo -> nert` dependency rule and the `NERT` experimental
  backend relationship.

## Out Of Scope

- nert implementation changes.
- A released `nert` version or inclusion in any compatibility set.
- A cross-repository contract document: nert is consumed as a source library
  through a pinned version and exposes no process, wire, or capabilities
  contract of its own.
- Changes to `neuriplo` itself (branch `feature/nert`) or to its default
  backend, which stays OPENCV_DNN.

## Decisions

- `nert` is a standalone, dependency-free, experimental ONNX inference runtime
  (C++17, CPU reference interpreter, opset 18) owned by the
  `inference-runtime-layer`.
- The dependency direction is `neuriplo -> nert`, never the reverse.
- `nert` depends on no other ecosystem repository and no vendor SDK.
- History: developed in `neuriplo` as `engine/` (backend NATIVE, then
  NEURIPLO_ENGINE, now NERT) and extracted on 2026-10-10 with history
  preserved.
- `nert` is recorded outside the C++ Gitflow group as a single-branch
  repository with default branch `main`; work lands on `main`.

## Constraints

- Keep all platform files ASCII-only.
- Link to the owning repository for implementation and operator-coverage
  details.
- Preserve existing compatibility claims and released pins.
- Do not present nert's ONNX Runtime comparisons as platform-attested evidence.
