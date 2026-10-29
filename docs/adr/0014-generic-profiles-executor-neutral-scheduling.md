# ADR 0014: Heterogeneous placement on generic profiles with executor-neutral scheduling

Date: 2026-10-29

Status: Accepted

## Problem

Validation work spans a heterogeneous, mostly operator-owned fleet (Linux
x86_64 with NVIDIA GPUs, Intel CPU machines, x86_64 edge laptops, ARM edge
boards, a Windows x64 machine, on-demand cloud GPUs including AMD and
ephemeral burst). The platform must answer which generic profile validates
which backend, which scheduler maps jobs to profiles, and where prebuilt
SDKs live, without publishing private operator detail and without mandating
an always-on fleet or a hardware purchase.

## Constraints

- Tracked files carry generic OS/architecture/accelerator profiles only;
  personal IPs, hostnames, account labels, machine identifiers,
  credentials, and private local paths are forbidden in the repo.
- No provisioning, spending, rebooting, power cycling, or cluster joins
  merely to create a plan; offline is a planned state, not a failure.
- Kubernetes control planes are Linux; supported native Windows worker
  OSes are Windows Server 2022/2025, so a Windows desktop/laptop is not a
  supported Kubernetes worker.
- GGML and TVM backends currently return placeholder outputs; current
  shared SDK recipes build CPU profiles with CUDA disabled. Packaging an
  SDK image validates neither inference nor CUDA/HIP execution.
- In-flight execution scope is unchanged: Jetson-class testing skipped and
  AMD hardware testing deferred in the current UI release-validation
  campaign; this decision plans profiles, it does not expand that campaign.
- Evaluated references: Kubernetes Windows nodes, GPU scheduling, and Job
  controllers; Slurm GRES and power saving; HTCondor overview; llama.cpp
  build docs; TVM source-install docs; NVIDIA embedded FAQ; NVIDIA
  DeepOps (GPU cluster provisioning for Slurm and Kubernetes, with no
  supported same-cluster hybrid or heterogeneous-OS setups); NVIDIA
  Run:ai (GPU-aware orchestration on Kubernetes, KServe integration,
  candidate only for the future serving phase).

## Options

1. Mandate one scheduler (Slurm everywhere, including cloud and Windows).
   Rejected: Windows desktop OS and ephemeral cloud nodes do not fit one
   scheduler, and running every scheduler simultaneously is waste.
2. Track per-machine entries with IPs and hostnames in platform files.
   Rejected: leaks private operator detail into public history and rots on
   every DHCP or tailnet change.
3. Buy missing hardware (datacenter NVIDIA, AMD GPU) and run an always-on
   fleet. Rejected: existing hardware plus on-demand cloud covers the
   profiles; idle machines cost money and attention.
4. Generic profiles plus an executor-neutral job/evidence contract, one
   executor at a time, on-demand sessions only. Selected.

## Decision

- Placement is expressed as generic profiles (`P-LNX-NVIDIA`,
  `P-LNX-CPU`, `P-LNX-EDGE-CPU`, `P-LNX-ARM-EDGE`, `P-WIN-CPU`,
  `P-CLD-AMD`, `P-CLD-BURST`) mapped to backends in
  `docs/architecture/heterogeneous-placement.md`. The private
  profile-to-host inventory lives outside tracked files.
- Jobs and evidence follow `contracts/scheduler-job-contract.md`, which is
  executor-neutral: the same job identity binds to Slurm constraints today
  and to Kubernetes Job labels tomorrow without changing the evidence
  envelope.
- Slurm is the first batch executor for backend-to-profile mapping;
  Kubernetes (Linux control plane) is evaluated for serving; HTCondor and
  OpenPBS stay documented alternatives. Executors run one at a time.
- Windows x64 CPU validation (OpenCV DNN with OpenCV 5, ONNX Runtime)
  enters through a native CI runner, not through the cluster; optional
  native llama.cpp follows only if required.
- No purchase is recommended; AMD and datacenter-NVIDIA gaps stay on
  on-demand cloud. Control-plane services start for scheduled sessions
  only, unless an always-available queue is actually needed.

## Consequences

What improves: backend coverage is attributable to profiles instead of
tribal machine knowledge; scheduler choice stops blocking validation
planning; private detail stays out of public history; no idle fleet.

What gets harder: the first run on each executor needs an operator-owned
binding (profile-to-node map, native Windows runner) that this repo
describes but cannot execute; evidence stays decentralized until those
sessions are scheduled.

Follow-up work: Group 5 of packet
`specs/2026-10-29-heterogeneous-scheduler-placement/` (first Slurm-bound
runs, Windows native-runner pilot) becomes a roadmap candidate when an
operator schedules it.
