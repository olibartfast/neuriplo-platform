# Local Inference E2E

Validation status: Draft

Version set: `initial-architecture-baseline` from `versions.yaml`

## Purpose

Describe the local end-to-end inference flow across platform repositories without
making `neuriplo-infer` the owner of cross-repository compatibility policy.

## Repositories Involved

- `neuriplo-tasks`: task contract, preprocessing, postprocessing, result semantics.
- `neuriplo`: backend abstraction and execution.
- `neuriplo-infer`: CLI, configuration, runtime wiring, visualization, local
  app flow.
- `videocapture`: video or stream source handling when the input is not a simple
  image file.

## Owning Runner

The executable Docker runner remains in `neuriplo-infer`:

- `neuriplo-infer/docker_run_inference_e2e_example.sh`

That script owns app-local CLI flags, Docker image selection, export command
shape, and backend-specific invocation details. This platform example owns the
cross-repository scenario definition and compatibility expectations.

## Scenario Matrix

Representative local inference scenarios:

| Preset | Task | Backend | Platform concern |
| ------ | ---- | ------- | ---------------- |
| `rtdetrv4` | object detection | TensorRT | detection result contract and backend conversion |
| `owlv2` | open-vocabulary detection | ONNX Runtime | tokenizer assets, text prompts, open-vocab result contract |
| `yoloseg` | instance segmentation | ONNX Runtime or TensorRT | mask result semantics |
| `raft` | optical flow | ONNX Runtime | dense output shape and visualization path |
| `vitpose` | pose estimation | ONNX Runtime | keypoint result semantics |
| `depth_anything_v2` | depth estimation | ONNX Runtime | depth result normalization |
| `videomae` | video classification | ONNX Runtime | video source sampling and classification result semantics |
| `gemma4` | image understanding | llama.cpp | multimodal task tensor contract |

## Inputs And Artifacts

This example assumes:

- a local `neuriplo-infer` checkout
- a local `neuriplo-tasks` checkout when export tooling is required
- model artifacts under `neuriplo-infer/models/e2e` or another caller-provided
  model directory
- sample inputs under `neuriplo-infer/data` or another caller-provided data
  directory
- labels or tokenizer files when the selected task requires them

Large model files and generated artifacts should not be copied into
`neuriplo-platform`.

## Command Shape

Dry-run the owning app runner from `neuriplo-infer`:

```bash
bash docker_run_inference_e2e_example.sh --preset owlv2 --dry-run
```

Run a concrete preset from `neuriplo-infer` after backend dependencies and
model artifacts are available:

```bash
bash docker_run_inference_e2e_example.sh --preset rtdetrv4 --neuriplo-tasks-dir ../neuriplo-tasks
```

## Expected Contract-Level Output

The exact rendering belongs to `neuriplo-infer`. Platform validation should
focus on contract-level behavior:

- task type resolves through `neuriplo-tasks`
- preprocessing produces the expected task input tensors
- `neuriplo` executes the selected backend without bypassing its abstraction
- postprocessing returns the expected typed result family
- `neuriplo-infer` renders or serializes the result without redefining task
  semantics

## Concrete Flow

```text
local image
  |
  v
neuriplo-infer
  |- parses CLI/config
  |- opens the source image directly or through videocapture
  '- selects model preset and backend settings
  |
  v
neuriplo-tasks
  |- resolves task type
  |- preprocesses image into task input tensors
  '- records task metadata needed for postprocessing
  |
  v
neuriplo
  |- selects backend adapter
  |- loads or reuses the model artifact
  '- executes inference and returns raw output tensors
  |
  v
neuriplo-tasks
  |- postprocesses raw tensors
  '- returns typed result family
  |
  v
neuriplo-infer
  |- serializes or renders result
  '- writes output artifact owned by the app workflow
```

Contract checkpoints:

- source image path is an app input, not a platform artifact
- task type and result family come from `neuriplo-tasks`
- backend selection crosses the `neuriplo` abstraction
- output rendering does not redefine task or result semantics

## Future Automation

A future integration test should read `versions.yaml`, verify local checkouts and
pinned refs, then run one small preset in dry-run mode before executing expensive
model export or inference steps.
