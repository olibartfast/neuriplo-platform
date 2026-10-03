# Requirements

Milestone: Serve encoded-image requests against dynamic-dimension inputs

Status: In progress (Phase 1 in review)

## Problem

[`neuriplo-infer`](https://github.com/olibartfast/neuriplo-infer) v0.10.0
through v0.10.2 ship this known limitation:

> `--input_mode=encoded-image` against a model whose input declares a dynamic
> dimension is rejected by neuriplo-kserve-runtime v0.3.2, which requires the
> request shape to equal the metadata exactly.

The client sends one `UINT8` tensor named `IMAGE` whose shape carries the
concrete byte length of the encoded file. An ensemble serving encoded images
must declare that axis dynamic (for example `[1, -1]`), because the length
varies per request.

## Findings That Shape The Scope

Established on 2026-10-03 by reading the code, before any implementation:

1. In [`neuriplo-kserve-runtime`](https://github.com/olibartfast/neuriplo-kserve-runtime)
   v0.3.2, `shapeMatches()` in `src/KServeV2Codec.cpp` rejects any request
   dimension that differs from the metadata dimension, so a metadata `-1`
   never matches. That is the reported defect.
2. v0.3.2 has no pipeline (ensemble) model kind at all. Encoded-image serving
   arrived on `develop` with `15f54b3` (pipeline model kind, DALI/TensorRT
   chaining, GPU serving), which also made `shapeMatches()` and the
   `NeuriploExecutor` input check treat a negative metadata dimension as a
   wildcard. The fix is therefore implemented but unreleased: `develop` is 11
   commits ahead of `v0.3.2`.
3. The gRPC codec does no shape check of its own; validation happens in the
   executor, which already accepts wildcards on `develop`.
4. The wildcard rule has one direct test (`tests/PipelineTest.cpp`, an
   `IMAGE UINT8 {1, -1}` input). The HTTP JSON, HTTP binary-extension, and gRPC
   ingress paths, and the rejection cases, are not covered.
5. GitFlow drift: the `v0.3.2` merge on `master` was never back-merged into
   `origin/develop` (`origin/develop...origin/master` is `11 1`). The
   back-merge commit exists only in a local checkout.
6. The client needs no change: it already sends a concrete extent.

Conclusion: this is a lock-in-and-release packet, not a code-fix packet. A
`v0.3.3` patch cannot carry it, because the encoded-image path depends on the
pipeline model kind, which is a feature.

## In Scope

- R-1: The runtime accepts a request dimension `d >= 0` wherever the model's
  metadata dimension is negative, on all three ingress paths (HTTP JSON, HTTP
  binary tensor extension, gRPC), for both a plain model and a pipeline model.
- R-2: The runtime still rejects, with a 400 / `INVALID_ARGUMENT` naming the
  input: a rank mismatch; a concrete-dimension mismatch; a negative or
  non-integer request dimension; a payload whose element or byte count does not
  match the request shape.
- R-3: Model metadata endpoints keep reporting the declared negative dimensions.
  Accepting a request never rewrites metadata.
- R-4: A runtime release tag containing R-1 to R-3, cut through GitFlow with
  `origin/develop` and `origin/master` reconciled first (finding 5) and after.
- R-5: neuriplo-infer `--input_mode=encoded-image` runs end to end against a
  dynamic-dimension ensemble served by that release, over HTTP and gRPC.
- R-6: The limitation is removed where it is documented: neuriplo-infer
  `CHANGELOG.md` (`Unreleased`, then the next release), the platform
  `versions.yaml` matrix, the `kserve-ensemble` integration-test README version
  set, and `coordination/STATUS.md`.

## Out Of Scope

- Client changes in neuriplo-infer or
  [`neuriplo-kserve-client`](https://github.com/olibartfast/neuriplo-kserve-client):
  the client is already correct (finding 6).
- Batching `BYTES` or encoded-image requests (`--batch=1` stays required);
  `BatchCompatibility` keeps rejecting them.
- Dynamic dimensions in outputs, and output-shape validation.
- Encoded-image support for the task families neuriplo-infer excludes (video
  classification, optical flow, image understanding, open-vocabulary
  detection).
- Populating the null benchmark baselines (roadmap item "Populate the null
  baselines").

## Constraints

- Runtime code stays in the runtime repository; this packet only records the
  contract and evidence (`specs/mission.md`, ADR 0003).
- GitFlow for the C++ siblings: work on `feature/*` from `develop`, `master` is
  release-only, tags on the `master` merge commit, back-merge after.
- A release with code changes gets a pattern audit and a max-effort full-range
  review of `v0.3.2..develop` before the release PR, fixing findings in one
  batch (lesson from the neuriplo-infer v0.10.0 release loop).
- Never modify the maintainer's own sibling checkouts; build and test in
  scratch worktrees. The local runtime checkout has uncommitted work.

## Open Questions

- Q-1: Release number. Decided 2026-10-03 by the maintainer: `v0.4.0`
  (minor). The range adds the pipeline kind, model repository serving, and the
  KServe repository extension.
- Q-2: Whether `v0.4.0` should also wait for the uncommitted local work in
  `src/NeuriploExecutor.cpp` and `src/RealNeuriploAdapter.cpp`. Assumed no:
  release what is on `origin/develop`.
- Q-3: Evidence for R-5 needs a served ensemble and a model file, so it is
  human-attested, like the other GPU and C++ evidence in this repository.
