# Heterogeneous Hardware Placement

This document maps backends to generic hardware profiles for validation and
benchmarking. It names profiles, never machines: no personal IPs,
hostnames, account labels, machine identifiers, credentials, or private
local paths appear here. The profile-to-host inventory is operator-owned
and lives outside tracked files (see `.gitignore`).

Last updated: 2026-10-29

## Profiles

| Profile | OS / arch | Accelerator | Backends validated |
|---|---|---|---|
| `P-LNX-NVIDIA` | Linux x86_64 | NVIDIA GPU | TENSORRT, ONNX_RUNTIME (CUDA), LIBTORCH (CUDA), NERT, OPENCV_DNN, llama.cpp CUDA variant |
| `P-LNX-CPU` | Linux x86_64 | CPU / Intel GPU | OPENVINO, ONNX_RUNTIME (CPU), NERT, OPENCV_DNN |
| `P-LNX-EDGE-CPU` | Linux x86_64 | CPU only (edge laptop) | ONNX_RUNTIME (CPU), LIBTORCH (CPU), LITERT, EXECUTORCH |
| `P-LNX-ARM-EDGE` | Linux aarch64 | Edge SoC GPU | TENSORRT (Jetson-class build), LITERT, EXECUTORCH, ONNX_RUNTIME (CPU), OPENCV_DNN |
| `P-WIN-CPU` | Windows x64 | CPU only | OPENCV_DNN with OpenCV 5, ONNX_RUNTIME; optional native llama.cpp only if required |
| `P-CLD-AMD` | Linux x86_64 (cloud) | AMD GPU, ROCm | MIGRAPHX (ONNX only) |
| `P-CLD-BURST` | Linux x86_64 (cloud, ephemeral) | NVIDIA GPU | ONNX_RUNTIME, LIBTORCH, NERT |

Notes:

- TensorRT engines are not portable across profiles: an x86_64 engine and
  a Jetson-class engine are separate exports. The scheduler distinguishes
  them by profile (`P-LNX-NVIDIA` vs `P-LNX-ARM-EDGE`), never by filename.
- A Linux profile and a Windows profile observed on similar hardware must
  not be counted as two concurrent workers without local verification;
  they may be dual-boot views of one physical machine.
- In-flight execution scope is unchanged by this document: Jetson-class
  testing skipped and AMD hardware testing deferred in the current UI
  release-validation campaign remain true. The profiles above plan future
  coverage; they do not expand that campaign.

## Windows x64 CPU Profile

`P-WIN-CPU` covers OpenCV DNN with OpenCV 5 and ONNX Runtime on native
Windows x64. The initial execution route is a native CI runner outside any
cluster. A Windows desktop/laptop OS is not a supported Kubernetes worker
(supported native Windows worker OSes are Windows Server 2022/2025), so
cluster membership for this profile is not assumed. The optional native
llama.cpp Windows build follows only if a consumer requires it; Linux
artifacts are never reused as native Windows binaries.

## SDK Cache Placement

Prebuilt backend/SDK retention follows the build host, not the consumer:

- Linux x86_64 is the main CPU SDK cache for GGML, TVM, and llama.cpp
  shared recipes.
- A CUDA llama.cpp variant is built and tested independently on a
  `P-LNX-NVIDIA` worker; the shared CPU recipe does not cover it.
- AMD HIP and ARM variants need their own compatible builds and
  validation on `P-CLD-AMD` and `P-LNX-ARM-EDGE` respectively.
- Linux artifacts are never reused as native Windows or ARM binaries.

Two hard limits stay attached to any SDK plan:

1. GGML and TVM backends currently return placeholder outputs. A packaged
   SDK is not inference support. No GPU SDK variants for these backends
   are built or distributed before real execution is implemented and
   validated.
2. Current shared SDK recipes build CPU profiles with CUDA disabled.
   Publishing an SDK image does not validate CUDA or HIP execution; that
   needs an executor run on the matching profile with evidence attached
   per the scheduler job contract.

## Scheduler Evaluation

| Scheduler | Fit | Notes |
|---|---|---|
| Slurm | First batch executor | GRES/Features map jobs to profiles; power saving supports on-demand workers; controller starts per scheduled session |
| Kubernetes | Evaluated for serving | Linux control plane; GPU scheduling via device plugin; batch via Job controller; no desktop-Windows workers (see above) |
| HTCondor / OpenPBS | Documented alternatives | Revisit only if Slurm plus Kubernetes leave a gap; never run all schedulers simultaneously |

Jobs and evidence stay executor-neutral per
`contracts/scheduler-job-contract.md`: the same job identity binds to
Slurm constraints today and to Kubernetes Job labels tomorrow without
changing the evidence envelope.

## On-Demand Policy

- Offline workers wait in a planned/on-demand state; they are never
  counted as inference failures.
- Control-plane services (Slurm controller, artifact registry, result
  collection) start only for scheduled sessions, unless an
  always-available queue is actually needed.
- No hardware purchase is recommended now: existing hardware covers the
  `P-LNX-*` and `P-WIN-CPU` profiles, while `P-CLD-AMD` and `P-CLD-BURST`
  stay on on-demand cloud. Revisit only when recurring cloud spend exceeds
  the amortized cost of owned hardware for a pinned profile.

## Executor Appendix

One executor runs at a time. The table below records the fit found during
evaluation; the binding section of the scheduler job contract stays the
only per-executor detail a session needs.

| Executor | Role | Fit for this fleet |
|---|---|---|
| Slurm | First batch executor | GRES/Features map jobs to profiles; power saving covers on-demand and cloud workers; controller starts per scheduled session |
| Kubernetes | Evaluated for serving | Linux control plane; GPU scheduling via device plugin; batch via Job controller; no desktop-Windows workers, so `P-WIN-CPU` stays on a native runner. Adopt only when an always-available serving queue is actually needed |
| HTCondor | Documented alternative, pilot candidate | ClassAd matchmaking on profile IDs; no root required; designed for machines that power on only for a session, which matches the on-demand policy and the intermittent edge-laptop profiles; GPU discovery via the GPU discovery tool |
| OpenPBS | Documented alternative | Classic server plus scheduler plus execution hosts with cgroups; solid for the static on-prem part, awkward for ephemeral/offline nodes; no advantage over Slurm here |

Guidance: Slurm covers the static batch core (`P-LNX-NVIDIA`,
`P-LNX-CPU`, `P-LNX-ARM-EDGE` when powered). If intermittent profiles
become the bottleneck, pilot HTCondor for exactly those profiles. Adopt
Kubernetes when serving must stay up; until then, serve via scheduled
sessions or directly on the node.

## External Provisioning and Scheduling References

- NVIDIA DeepOps (`https://github.com/NVIDIA/deepops`): Ansible
  automation for building GPU clusters, covering both Slurm and
  Kubernetes (via Kubespray) on Ubuntu 22.04/24.04. Candidate
  provisioning path for the first Slurm runs (packet Group 5). Note its
  stated limits: no tested or supported configuration runs Kubernetes
  and Slurm on the same physical cluster, and heterogeneous-OS nodes are
  not supported. Both limits reinforce the one-executor-at-a-time rule
  and the homogeneous-OS-per-cluster assumption in this document.
- NVIDIA Run:ai (`https://github.com/dsx-ai-factory/run-ai`):
  open-source GPU-aware workload orchestration on Kubernetes
  (fair-share, fractional GPUs, quotas, multi-cluster, KServe
  integration). Evaluation candidate for the Kubernetes serving phase:
  when an always-available `neuriplo-kserve-runtime` queue is needed,
  Run:ai is the GPU scheduling layer to assess before building custom
  scheduling. Until then it stays a reference, not a dependency.
- Nebius Physical AI (`https://github.com/nebius/nebius-physical-ai`):
  agent control plane running YAML workflows on Nebius Kubernetes via
  SkyPilot, with Terraform-managed clusters and a GHCR image catalog.
  Useful as a pattern reference, not adoptable infra: workflow
  validate/plan/submit phases mirror the runbook session flow; the
  image/GPU matrix distinguishes tested hardware from expected
  compatibility, as the benchmarking contract requires; teardown
  discipline (cancel jobs first, read-only destroy preview) matches the
  stop-and-verify step; credentials and private identifiers stay out of
  public issues, as the privacy rule requires. Cloud- and
  robotics-specific parts do not transfer to the edge and Windows
  profiles.
- Nebius Soperator (`https://github.com/nebius/soperator`):
  Kubernetes operator that runs Slurm clusters on Kubernetes from one
  `SlurmCluster` resource, with ephemeral autoscaling workers, health
  checks, Pyxis/Enroot runtimes, and Tailscale SSH support. Convergence
  option to reassess when the Kubernetes serving phase starts: Slurm
  jobs could then run inside Kubernetes instead of on a separate
  bare-metal Slurm. Not for now: it needs a Kubernetes control plane,
  Ubuntu 24.04 node images, and the GPU Operator, and it targets
  datacenter/cloud GPUs rather than the intermittent edge, ARM, and
  Windows profiles. Current limits to recheck at that time include
  single-partition and GPU-only or CPU-only cluster constraints.
