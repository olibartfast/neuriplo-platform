# Local Inference E2E

Validation status: Draft

Version set: `initial-architecture-baseline` from `versions.yaml`

## Purpose

Describe the local end-to-end inference flow across platform repositories without
making `vision-inference` the owner of cross-repository compatibility policy.

## Repositories Involved

- `vision-core`: task contract, preprocessing, postprocessing, result semantics.
- `neuriplo`: backend abstraction and execution.
- `vision-inference`: CLI, configuration, runtime wiring, visualization, local
  app flow.
- `videocapture`: video or stream source handling when the input is not a simple
  image file.

## Owning Runner

The executable Docker runner remains in `vision-inference`:

- `vision-inference/docker_run_inference_e2e_example.sh`

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

- a local `vision-inference` checkout
- a local `vision-core` checkout when export tooling is required
- model artifacts under `vision-inference/models/e2e` or another caller-provided
  model directory
- sample inputs under `vision-inference/data` or another caller-provided data
  directory
- labels or tokenizer files when the selected task requires them

Large model files and generated artifacts should not be copied into
`vision-platform`.

## Command Shape

Dry-run the owning app runner from `vision-inference`:

```bash
bash docker_run_inference_e2e_example.sh --preset owlv2 --dry-run
```

Run a concrete preset from `vision-inference` after backend dependencies and
model artifacts are available:

```bash
bash docker_run_inference_e2e_example.sh --preset rtdetrv4 --vision-core-dir ../vision-core
```

## Expected Contract-Level Output

The exact rendering belongs to `vision-inference`. Platform validation should
focus on contract-level behavior:

- task type resolves through `vision-core`
- preprocessing produces the expected task input tensors
- `neuriplo` executes the selected backend without bypassing its abstraction
- postprocessing returns the expected typed result family
- `vision-inference` renders or serializes the result without redefining task
  semantics

## Future Automation

A future integration test should read `versions.yaml`, verify local checkouts and
pinned refs, then run one small preset in dry-run mode before executing expensive
model export or inference steps.
