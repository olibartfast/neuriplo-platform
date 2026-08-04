# Configuration Contract

Owners: `neuriplo-infer`, `neuriplo-kserve-runtime`, `neuriplo`

Consumers: CLI users, deployment automation, integration tests

Status: Draft

## Purpose

Define shared configuration expectations for selecting tasks, model artifacts,
backends, runtime behavior, and output handling across local and serving modes.

## Task Domain and Task Selection

The task domain discriminator separates input-source and pipeline expectations.
Today only `cv` ships. The other domains are reserved by ADR 0010 and become
supported only when an owning repository implements and validates them.

```text
task_domain:   cv | nlp | audio | tabular | multimodal | rl
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
pose_estimation:        yolo26pose, yolov8pose, yolov11pose, vitpose, ecpose,
                        rfdetr_keypoint, rfdetr_kpt
classification:         resnet50, resnet101, vitclassifier, torchvisionclassifier,
                        tensorflowclassifier
depth_estimation:       depthanythingv2, yolo-depth, yolo26n-depth (any
                        YOLO-prefixed model type containing `depth`)
optical_flow:           raft
open_vocab_detection:   owlv2, owlvit, groundingdino
video_classification:   videomae, vivit, timesformer
image_understanding:    llama, gemma4, gemma, llamacpp, imageunderstanding
gaussian_splatting:     lgm, lgm-mini, grm, gaussiansplatting
```

Reserved future domains:

```text
nlp:         embeddings, text classification, token classification, ranking,
             translation, summarization
audio:       automatic speech recognition, text-to-speech, audio classification
tabular:     classification, regression, forecasting
multimodal:  image-text-to-text, visual question answering, document question
             answering, image-text retrieval
rl:          policy inference and environment-coupled workloads; out of scope
             for serving v1 until lifecycle semantics are defined
```

`task_type` is case-insensitive; `neuriplo-tasks` normalises to lowercase and
strips whitespace, hyphens, and underscores before matching.

Consumers select a task by setting `task_type`. The owning task library maps
the string to a `TaskType` enum (see `neuriplo/tasks/core/result_types.hpp`)
and dispatches to the correct preprocess/execute/postprocess pipeline.

When a non-cv `task_domain` ships, the owning task library must extend
`TaskFactory`, document new `task_type` strings here, and define the domain's
input contract, result contract, batching semantics, streaming support, backend
expectations, serving protocol, and example configuration.

## Serving Track

Serving protocol follows task behavior rather than repository history:

```text
predictive tensor tasks:  KServe V2 / Open Inference Protocol
generative chat/text:     OpenAI-compatible endpoints
embedded local tasks:     repository-owned implementation path
```

The KServe V2 track is the default for predictive workloads whose inputs and
outputs are bounded tensors, including current CV tasks and planned embedding or
tabular pilots. Generative `image_understanding` remains available in embedded
local mode, but remote generative serving is OpenAI-compatible per ADR 0006.

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

## Pipeline (Ensemble) Models

A pipeline model is declared by a JSON graph rather than a single model
artifact. It is loaded under `backend: ensemble` and its graph is supplied
through the model path or inline in the admin load body.

```text
steps:  ordered list; each step is
        kind:           model | preprocess | postprocess
        name:           unique step name within the graph
        model_name:     referenced registry model (kind: model)
        model_version:  optional; defaults to the model's default version
        input_map:      graph tensor name -> step input name
        output_map:     step output name -> graph tensor name
        params:         step-specific options (task_type, letterbox rule,
                        thresholds, envelope variant)
```

Rules:

- Every tensor a step consumes is produced by an earlier step or is the
  ensemble input. Graphs are validated at load time, not at first request.
- `model` steps resolve against the runtime's registry at inference time. A
  referenced model that is missing or not ready yields `MODEL_NOT_READY`;
  pipelines do not pin referenced models alive.
- `preprocess` and `postprocess` steps require the runtime to be built with
  its task-layer dependency enabled. Without it they must fail at load time
  with an explicit message, never silently degrade.
- Composed metadata is the first step's inputs and the last step's outputs.
- Dynamic batching configuration is rejected for pipeline models.

The input and output shape of the composed model is owned by
[ensemble-contract.md](ensemble-contract.md), not by this document.

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
- Changing a task's serving track is breaking unless a versioned compatibility
  window preserves the old protocol.

## Validation Strategy

- Owning repositories validate local configuration parsing.
- `neuriplo-tasks` tests validate that every registered `task_type` string
  maps to a valid `TaskType` and produces working preprocess/postprocess.
- This repository validates shared configuration examples against compatible
  repository versions.
- Integration tests exercise at least one `task_type` per supported backend
  in the compatibility matrix.
- Example configurations should be versioned with `versions.yaml`.
