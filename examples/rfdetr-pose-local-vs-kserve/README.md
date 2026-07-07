# RF-DETR Pose Local vs KServe

Validation status: Draft

Version set: `rfdetr-keypoint-pose-followup` from `versions.yaml`

## Purpose

Define one golden-path scenario that proves the same RF-DETR keypoint pose task
can run through local embedded inference and remote KServe gRPC inference without
changing the platform result contract.

## Repositories Involved

- [`neuriplo-tasks`](https://github.com/olibartfast/neuriplo-tasks): task type,
  preprocessing, postprocessing, and pose result schema.
- [`neuriplo`](https://github.com/olibartfast/neuriplo): backend abstraction,
  model execution, and backend capability reporting.
- [`neuriplo-infer`](https://github.com/olibartfast/neuriplo-infer): local
  embedded flow, remote KServe client flow, rendering, and benchmark command.
- [`neuriplo-kserve-client`](https://github.com/olibartfast/neuriplo-kserve-client):
  KServe V2 / Open Inference Protocol gRPC transport used by the app flow.
- [`neuriplo-kserve-runtime`](https://github.com/olibartfast/neuriplo-kserve-runtime):
  serving runtime, model lifecycle, request admission, and response encoding.
- [`videocapture`](https://github.com/olibartfast/videocapture): image/video
  source layer when the input is not a direct image path.

## Scenario

```text
input image or video
  -> local embedded inference through neuriplo-infer
  -> remote KServe gRPC inference through neuriplo-kserve-client/runtime
  -> compare result schema
  -> compare latency
  -> save rendered output
  -> save benchmark JSON
```

The owning execution command belongs in `neuriplo-infer`, for example:

```bash
neuriplo-infer bench --scenario rfdetr-pose-local
neuriplo-infer bench --scenario rfdetr-pose-kserve-grpc
```

`neuriplo-platform` owns the compatibility set, expected evidence shape, result
contract checks, and benchmark baseline references.

## Expected Evidence

A completed run should publish:

- rendered local output image or video
- rendered KServe output image or video
- local benchmark JSON conforming to
  [the benchmarking contract](../../contracts/benchmarking-contract.md)
- KServe gRPC benchmark JSON conforming to
  [the benchmarking contract](../../contracts/benchmarking-contract.md)
- compatibility report under
  `integration-tests/rfdetr-pose-local-vs-kserve/reports/`

## Contract Checkpoints

- both paths resolve `rfdetrpose`, `rfdetrkeypoint`, or `rfdetrkpt` through
  `neuriplo-tasks`
- local execution crosses the `neuriplo` backend abstraction
- remote execution crosses the KServe V2 gRPC transport
- both responses decode to the same pose result family
- rendered outputs are owned by `neuriplo-infer`; platform only records evidence
- benchmark JSON includes the compatibility set and scenario name
