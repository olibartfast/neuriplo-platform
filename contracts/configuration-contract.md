# Configuration Contract

Owners: `neuriplo-infer`, `neuriplo-kserve-runtime`, `neuriplo`

Consumers: CLI users, deployment automation, integration tests

Status: Draft

## Purpose

Define shared configuration expectations for selecting tasks, model artifacts,
backends, runtime behavior, and output handling across local and serving modes.

## Task Domain and Task Selection

The task domain discriminator separates input-source and pipeline expectations.
Today only `cv` ships; `nlp`, `audio`, and `tabular` are reserved for future
domains that fit the same preprocess/execute/postprocess contract.

```text
task_domain:   cv | nlp | audio | tabular
task_type:     model-type string routed by neuriplo-tasks TaskFactory
model_artifact:  path or URI to the model file or directory
```

`task_type` values are owned by `neuriplo-tasks` and registered in its
`TaskFactory`. Current registered strings (cv domain):

```text
object_detection:       yolo26, yolov8, yolov10, yolov11, rtdetr, rtdetrv2,
                        rfdetr, dfine, deim, ecdet, ecdet_s, ecdet_m,
                        ecdet_l, ecdet_x, edgecrafter, edgecrafter-det,
                        yolonas, yolo-nas, yolov4, yolov5, yolov6, yolov7,
                        yolov7e2e, yolov9, yolov12
instance_segmentation:  yolo26seg, yolov10seg, yoloseg, rfdetrseg, ecseg
pose_estimation:        yolo26pose, yolov8pose, yolov11pose, vitpose, ecpose
classification:         resnet50, resnet101, vitclassifier, torchvisionclassifier,
                        tensorflowclassifier
depth_estimation:       depthanythingv2
optical_flow:           raft
open_vocab_detection:   owlv2, owlvit, groundingdino
video_classification:   videomae, vivit, timesformer
image_understanding:    llama, gemma4, gemma, llamacpp, imageunderstanding
gaussian_splatting:     lgm, lgm-mini, grm, gaussiansplatting
```

`task_type` is case-insensitive; `neuriplo-tasks` normalises to lowercase and
strips whitespace, hyphens, and underscores before matching.

Consumers select a task by setting `task_type`. The owning task library maps
the string to a `TaskType` enum (see `neuriplo/tasks/core/result_types.hpp`)
and dispatches to the correct preprocess/execute/postprocess pipeline.

When a non-cv `task_domain` ships, the owning task library must extend
`TaskFactory` and document new `task_type` strings here.

## Model Artifact Reference

```text
model_artifact:  file path, directory path, or model repository-relative name

embedded local:   absolute or relative path to a model file (e.g., model.onnx)
remote KServe:    model name as registered in the server's model repository
                  (e.g., ecdet_s_tensorrt); path resolution is server-owned
```

`neuriplo-infer` resolves model artifacts: direct filesystem paths in embedded
local mode, model names in remote KServe client mode. `neuriplo-kserve-runtime`
resolves model artifacts from its configured model repository root.

## Backend Selection

```text
backend:  onnx_runtime | tensorrt | openvino | executorch | litert

embedded local:  backend selects the neuriplo adapter at application init
remote KServe:   backend is server-owned; clients do not set it
```

`neuriplo` owns backend capability discovery and adapter construction. The
`backend` field selects which adapter `neuriplo-infer` (embedded local) or
`neuriplo-kserve-runtime` (serving) constructs.

Backend-specific options (precision, device index, stream count) are
namespaced under the backend name and owned by `neuriplo`. Consumers treat
them as opaque passthrough.

## Device and Precision

```text
device:          auto | cpu | cuda:<index>
precision:       fp32 | fp16 | int8 | auto

auto:            backend selects best available device and precision from
                 its capability query (see gpu-capability-contract.md)
cuda:<index>:    explicit GPU device index (0-based)
```

If a requested precision is unsupported by the selected device, the backend
must fail at load time with a clear error, not silently fall back.

## Runtime Behavior

Serving-mode fields owned by `neuriplo-kserve-runtime`:

```text
batch_size:        uint32 (max batch; 0 = dynamic, scheduler-decided)
batch_timeout_us:  uint32 (max wait before flushing a partial batch)
queue_max_size:    uint32 (admission reject point)
grpc_port:         uint16 (when gRPC transport is enabled)
```

These fields are serving-only and must not affect embedded local mode behavior.

## Output Handling

Shared across local and serving modes:

```text
output_dir:     directory for rendered images or serialized results
labels_file:    path to class labels file (CV domain: coco.names or equivalent)
visualize:      bool (render annotated output images; cv domain only)
serialize:      bool (emit machine-readable result payload; see result-contract.md)
```

## Compatibility Rules

- Adding optional configuration fields is backward compatible.
- Renaming fields is breaking.
- Changing defaults can be breaking when observable behavior changes.
- Backend-specific configuration must be namespaced or capability-gated.
- Serving-only configuration must not leak into local CLI contracts unless the
  local application consumes it.
- Adding a new `task_type` string owned by `neuriplo-tasks` is backward
  compatible.
- Adding a new `task_domain` value is backward compatible when existing values
  are unchanged.
- Renaming or removing a `task_type` string owned by `neuriplo-tasks` is
  breaking; coordinate through the task contract.

## Validation Strategy

- Owning repositories validate local configuration parsing.
- `neuriplo-tasks` tests validate that every registered `task_type` string
  maps to a valid `TaskType` and produces working preprocess/postprocess.
- This repository validates shared configuration examples against compatible
  repository versions.
- Integration tests exercise at least one `task_type` per supported backend
  in the compatibility matrix.
- Example configurations should be versioned with `versions.yaml`.
