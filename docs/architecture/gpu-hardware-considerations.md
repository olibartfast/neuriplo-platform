# GPU Hardware Considerations

This document describes platform-level GPU hardware expectations for the neuriplo
AI infrastructure platform. Backend-specific implementation details and
vendor-SDK code remain in `neuriplo` and the owning repositories.

## Device Discovery and Topology

The platform expects backends to enumerate GPU devices and report topology:

```text
PCIe topology:  which GPU is on which PCIe root complex (NUMA affinity)
NVLink/NVSwitch: peer-to-peer GPU connectivity and bandwidth
MIG (Multi-Instance GPU): partition count and profile when enabled
CPU-GPU affinity: NUMA node mapping for pinned memory and DMA efficiency
```

`neuriplo` normalizes this into the `gpu-capability-contract.md` surface.
Consumers use capability fields (`pcie_gen`, `pcie_width`, `nvlink_peers`,
`topology_numa_node`) for placement decisions.

## Memory Allocation Strategies

GPU memory management is a first-class concern for serving throughput:

```text
Arena/pool allocation:  pre-allocate a working set arena per model; avoid
                        per-request cudaMalloc which fragments and stalls

Unified memory:         acceptable for models that exceed device memory with
                        low-access pages; not a substitute for capacity planning

Peer access:            enable when NVLink peers are detected and models span
                        multiple GPUs; disable otherwise to avoid silent DMA
                        fallback

Memory budget:          each model declares a peak working set in the model
                        manifest; the scheduler enforces the budget when placing
                        models onto devices

OOM policy:             the runtime must surface OOM as an admission failure,
                        not crash the process; the GPU capability contract
                        reports free memory to help pre-flight checks
```

## Kernel Launch and Stream Concurrency

```text
Stream model:       stream-per-model (default for serving): each model gets a
                    dedicated CUDA stream; batching within a model serializes
                    on that stream

Stream-per-request: acceptable for single-stream latency benchmarks but risks
                    oversubscription in multi-model serving

Concurrency limit:  the scheduler should cap concurrent GPU operations to
                    avoid kernel launch overhead dominating useful work

Event-based sync:   prefer CUDA events over stream synchronization for
                    cross-stream dependencies; avoid device sync in hot paths
```

## Mixed-Precision and Quantization

```text
Per-backend policy:
  TensorRT:    FP16 default, INT8 with calibration cache, FP8 on Ada/Hopper+
  ONNX Runtime: FP16 where provider supports it, INT8 via QDQ
  OpenVINO:    FP16 default on GPU plugin, INT8 with calibration

Per-model override:  a model manifest may specify precision; the backend
                     capability contract declares what precisions the device
                     supports

Platform rule:       if a model requests a precision the device does not
                     support, the backend must fail at load time with a clear
                     error, not silently fall back
```

## Accelerator Portability

The platform abstracts GPU backends through `neuriplo` adapters. Vendor
boundaries are explicit:

```text
CUDA (NVIDIA):       primary development target; TensorRT and ONNX Runtime CUDA
ROCm (AMD):          planned; ONNX Runtime ROCm provider as first path
oneAPI (Intel):      planned; OpenVINO GPU plugin as first path
CPU fallback:        all backends must support a CPU path for CI and
                     development; CPU reports device_count=0

Portability rule:    task code and application code must not include vendor GPU
                     headers; backend-specific code lives only in `neuriplo`
                     backend adapters
```

## GPU Health and Telemetry

Runtime GPU telemetry feeds the observability contract and operational endpoints:

```text
Utilization:      SM occupancy, memory controller utilization (sampled, not polled per-request)
Memory pressure:  device memory used vs. total, fragmentation estimate
Temperature:      GPU die and memory junction (throttle warning threshold)
ECC errors:       corrected and uncorrected counts (hardware health signal)
Clock status:     current SM and memory clock vs. base; throttling reason if any
NVLink status:    link up/down, bandwidth degradation
```

Telemetry collection is owned by `neuriplo-kserve-runtime` in serving mode and by
`neuriplo-infer` in embedded local mode. `neuriplo` provides the raw query
surface; runtimes decide sampling rate and exposure.

## Multi-GPU Scheduling

```text
Placement policy:
  round-robin:       distribute models evenly across available GPUs (simple, stateless)
  NUMA-aware:        place models on GPUs closest to the CPU socket handling
                     their network/IO
  bin-packing:       fill one GPU before using the next (density-optimized)
  custom affinity:   operator-specified GPU-to-model mapping

Platform rule:       the scheduler must support at minimum round-robin and
                     explicit affinity; NUMA-aware and bin-packing are documented
                     extensions
```

## AI Datacenter Considerations

At datacenter scale, GPU infrastructure concerns extend beyond a single node:

```text
Model distribution:  model artifacts pulled from a registry (OCI, S3, NFS);
                     lazy-pull on first load, cached on node-local NVMe

Node pools:          group nodes by GPU generation (H100 pool, L40S pool);
                     route model placement requests to compatible pools

Inter-node networking: tensor-parallel and pipeline-parallel strategies need
                       RoCE or InfiniBand fabric; the platform documents
                       bandwidth expectations but does not implement the fabric

Power management:    GPU clock throttling under power cap is a datacenter
                     concern; the platform surface should expose clock and
                     throttle reason for operators
```

These concerns are platform-level documentation. Implementation (node agents,
model registries, fabric configuration) remains in deployment-layer tooling and
owning repositories.
