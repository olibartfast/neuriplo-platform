# ADR 0013: Create the nert repository for the Neuriplo Engine Runtime

Date: 2026-10-10

Status: Accepted

## Problem

`neuriplo` gained a first-party ONNX inference runtime developed inside the
repository as `engine/`. The backend was first named `NATIVE`, then
`NEURIPLO_ENGINE`, and is now `NERT`. Keeping the runtime inside `neuriplo`
mixes two concerns in one repository: the backend abstraction layer (adapters
over third-party engines) and an inference engine implementation with its own
operator coverage, kernels, and correctness validation. The runtime also has
no dependency on any other ecosystem repository or vendor SDK, so it has no
reason to share a release cadence or build graph with `neuriplo`.

## Constraints

- `neuriplo` remains the backend abstraction layer; its default backend stays
  OPENCV_DNN and is not changed by this decision.
- The runtime is experimental and unreleased (0.1.0). It must not be presented
  as a production backend.
- The runtime must stay dependency-free: no other ecosystem repository and no
  vendor SDK.
- Commit history must be preserved.
- Existing compatibility sets and released pins must not change.

## Options

1. Keep the runtime as `engine/` inside `neuriplo`.
2. Extract it to a separate repository and consume it from `neuriplo` through a
   pinned version.
3. Extract it and have the runtime depend on `neuriplo` abstractions.

## Decision

Choose option 2. By maintainer decision, on 2026-10-10 the runtime was
extracted to [`nert`](https://github.com/olibartfast/nert) (public, MIT
licence) with history preserved.

`nert` owns:

- the ONNX loader (opset 18), static shape inference, and constant folding;
- single-arena memory planning;
- the CPU reference interpreter and naive kernels used as a correctness
  oracle; and
- operator coverage (float32 compute; int64 and bool shape data and I/O).

`neuriplo` consumes it as the experimental backend `NERT` through a pinned
`NERT_VERSION` in its `versions.env` and CMake FetchContent, on neuriplo branch
`feature/nert` merging into `develop`. The dependency direction is
`neuriplo -> nert`, never the reverse. The `NERT` backend adapter stays in
`neuriplo`.

The platform registers `nert` as a WIP repository (`version: wip`, pinned by
commit SHA) with the owner `inference-runtime-layer`. It is not part of any
compatibility set.

## Consequences

- `nert` can evolve, be tested, and be released independently of `neuriplo`.
- `neuriplo` gains one more pinned dependency, but only when the `NERT`
  backend is selected; the default build is unaffected.
- The platform gains a leaf node in the dependency graph and a new edge
  `neuriplo -> nert` in `ops/CLUSTER_MAP.yaml`.
- Operator coverage claims belong to `nert`. It has been validated against ONNX
  Runtime through `neuriplo` on the YOLO families (v5-v12, YOLO11, YOLO26
  detection, segmentation, and pose), ViT, ViTPose, Depth Anything V2,
  VideoMAE, ViViT, TimeSformer, and the DETR family (RT-DETR v4, D-FINE/DEIM,
  DEIMv2, RF-DETR, RF-DETR-Seg). RAFT, OWLv2, and Grounding DINO are in
  progress. These claims are made by the owning repository and are not
  platform-attested compatibility evidence.
- Follow-up: promote `nert` to a released version and a compatibility set only
  after a tagged release and attested evidence.
