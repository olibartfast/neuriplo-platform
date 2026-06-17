# GPU Capability Contract

Owner: `neuriplo`

Consumers: `neuriplo-infer` (embedded local mode), `neuriplo-kserve-runtime`,
integration tests, deployment automation

Status: Draft

## Purpose

Define the GPU device capability surface that backends must report so consumers
can reason about hardware resources without vendor-specific SDK calls. This
contract sits beneath the backend contract: backends implement it, runtimes and
applications consume it.

## Reported Capabilities

`neuriplo` backends must report per-device:

```text
device_count:        uint32
device_index:        uint32 (0..device_count-1)
device_name:         string (e.g. "NVIDIA L40S", "AMD Instinct MI300X")
compute_capability:  major.minor version or equivalent (CUDA CC, ROCm gfx target)
memory_total_mib:    uint64
memory_free_mib:     uint64 (best-effort snapshot; not a reservation guarantee)
memory_bandwidth_gbs: float (peak theoretical)
tensor_cores:        bool
fp16_supported:      bool
bf16_supported:      bool
int8_supported:      bool
fp8_supported:       bool
nvlink_peers:        []uint32 (peer device indices with NVLink/Infinity Fabric)
pcie_gen:            uint32
pcie_width:          uint32
topology_numa_node:  int32 (-1 if unknown)
```

Per-backend aggregated:

```text
backend_name:        string (e.g. "tensorrt", "onnxruntime_cuda", "openvino_gpu")
peak_compute_tflops_fp16: float (per device, sum across devices)
peak_compute_tflops_fp8:  float (per device, sum across devices)
recommended_batch_size:   uint32 (per device; heuristic, not a hard limit)
```

## Responsibilities

`neuriplo` owns:

- GPU device enumeration and capability query.
- Normalizing vendor-specific capability fields into the contract shape.
- Reporting device availability after initialization.
- Exposing capability through a stable C++ interface (not through raw CUDA/ROCm
  API types).

Consumers may:

- Query device count, memory, compute capability, and precision support before
  model loading.
- Use device affinity hints (NUMA node, NVLink peers) for placement decisions.
- Log and expose GPU telemetry through the observability contract.

Consumers must not:

- Call vendor GPU APIs directly (CUDA, HIP, oneAPI) outside `neuriplo`.
- Assume a specific GPU vendor from capability fields alone.
- Reserve GPU memory through the capability interface; it is read-only
  observation.

## Compatibility Rules

- Adding a capability field is backward compatible.
- Adding a backend that reports capabilities is backward compatible.
- Removing a capability field is breaking.
- Changing the semantic meaning of a capability field (e.g. switching
  memory_total_mib from total to usable) is breaking.
- Unsupportable capabilities (e.g. fp8 on a GPU without fp8 hardware) must be
  reported as `false`/`null`, not omitted.

## Validation Strategy

- Unit tests in `neuriplo` validate capability query against at least one real
  GPU backend and one CPU backend (CPU reports `device_count=0`).
- Integration tests in this repository validate that the capability surface is
  readable from `neuriplo-infer` and `neuriplo-kserve-runtime`.
- GPU-free CI environments must tolerate `device_count=0` and skip GPU-specific
  assertions.

## Relationship to Other Contracts

- `backend-contract.md`: the execution interface. GPU capability is a read-only
  discovery surface beneath it.
- `observability-contract.md`: runtime GPU telemetry (utilization, memory
  pressure, temperature) flows through observability, not through capability.
- `benchmarking-contract.md`: performance baselines are measured against known
  GPU capabilities documented here.
