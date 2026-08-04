# Inbox: runtime-infer

## [x] from:human 2026-08-04 -- ensemble serving + neuriplo-tasks v0.8.0 alignment
Two lanes, both specified in the platform repo.

**Lane 1, neuriplo-infer <- neuriplo-tasks v0.8.0** (independent, do first).
Branch `feat/tasks-v080-alignment` exists locally with the work applied and
32/32 CTest passing: pin bump to v0.8.0, `contains(normalized, "depth")`
routing so the YOLO26 depth family stops falling through to Detection, and a
new `--segmentation_output=mask|polygon` flag wired to
`TaskConfig::segmentation_output` with polygon rendering in both renderers.
Changelog entry is under `[Unreleased]`; VERSION is untouched because
`scripts/cut_release.sh` owns it. Review, then PR to develop.

**Lane 2, ensemble/pipeline serving in neuriplo-kserve-runtime.** Read
`contracts/ensemble-contract.md` first -- it is transcribed from tritonic
v0.4.0 and is the surface both servers get validated against. ADR 0011 records
why we are not adopting Triton/DALI. Shape of the work:

1. `src/PipelineConfig.{hpp,cpp}` -- JSON graph of ordered steps
   (kind: model | preprocess | postprocess), validated at load time.
2. `src/PipelineExecutor.{hpp,cpp}` implementing `Executor`, registered in
   `BackendRegistry.cpp` under backend `ensemble`. `model` steps need registry
   access, which `ExecutorFactory(config, error)` does not give you -- rather
   than widen that public type, have `ModelRegistry::loadModelLocked` wrap the
   factory for ensemble configs and inject a resolver bound to
   `findHandleVersion`.
3. Built-in preprocess/postprocess steps behind `NEURIPLO_RUNTIME_WITH_TASKS`,
   linking `neuriplo-tasks::vision-stb` for JPEG decode and never
   `vision-opencv`. This inverts the current layering (the runtime sits below
   the task layer today) -- keep the OFF path building exactly what it builds
   now.
4. Composed metadata = first step inputs + last step outputs,
   `platform = "ensemble"`, overriding the `"neuriplo_" + backend` default in
   `ModelLifecycle.cpp`. `BatchCompatibility` must reject batching for
   ensembles.
5. Tests: graph validation, step routing, detection cap, and the
   empty-detection envelope for both segmentation variants. tritonic shipped a
   truncated `MASK_OFFSETS` on detection-free frames and it aborted any video
   whose first frame was empty -- pin that case.

**Lane 3, neuriplo-infer adapter.** Branch `feat/kserve-ensemble` (off
`feat/tasks-v080-alignment`) has the self-contained half done, 49/49 CTest
passing: the three CLI flags with tritonic's validation rules,
`app/inc/EncodedImage.hpp` (JPEG dimensions, request builder, ensemble-vs-task
model validation) and `app/inc/KserveEnvelope.hpp` (detection, mask and polygon
decoders), all unit tested including the truncated-offsets rejection.

**What is left, and it is the part that makes the feature work:** routing the
encoded-image path through `app/src/NeuriploInferProcessing.cpp`. That file
repeats `task->preprocess` -> `engine->get_infer_results` ->
`task->postprocess` in five places; encoded-image mode must skip the first
(send the file bytes instead) and, under `--postprocess_mode=gpu`, skip the
third (decode the envelope instead). It was left undone rather than half-wired
through the hot path. `KserveEngine` will also need the second client for the
task model's metadata -- no client API change needed, clients are per-model.

## [ ] from:neuriplo-agent 2026-06-12 -- raw_output_contents in gRPC responses
The client<->runtime live conformance surfaced a response-side wire gap
(request side is clean: both protos agree on `raw_input_contents = 7`).

Current state in neuriplo-kserve-runtime:
- `src/GrpcV2Codec.cpp:47` widens every numeric output into `fp64_contents`
  regardless of declared dtype -- KServe v2 spec deviation, 2x bandwidth for
  FP32, and the reason the client-agent had to add an fp64 tolerance.
- The vendored `proto/kserve_grpc.proto` has no `raw_output_contents` field
  on `ModelInferResponse` at all.

Proposed fix (sequencing rule: runtime first, then client):
1. Add `repeated bytes raw_output_contents = 6;` to `ModelInferResponse`
   -- field number 6 to match the client's proto
   (neuriplo-kserve-client `proto/kserve_grpc.proto:165`).
2. Emit `OutputTensor.bytes` there directly (they're already typed bytes
   since Step 15 -- this is the response-side mirror of the Phase 3.1 win).
3. Respond in kind: raw outputs iff the request used `raw_input_contents`;
   otherwise keep typed contents, but fix the fallback to use the
   spec-correct field per dtype (`fp32_contents` for FP32, etc.).
4. Ping client-agent when merged so the client's fp64 tolerance can be
   demoted to a legacy-compat note.
