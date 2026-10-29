# Requirements

Milestone: Heterogeneous hardware placement and executor-neutral scheduling

Status: Specified, not implemented

## Problem

Validation and benchmarking work for the ecosystem is spread across a
heterogeneous, mostly operator-owned fleet: Linux x86_64 workstations with
NVIDIA GPUs, Intel CPU machines, x86_64 edge-class laptops, ARM edge boards,
a Windows x64 machine, and on-demand cloud GPUs (including AMD and ephemeral
burst capacity). There is no platform-owned answer to three questions:

- Which generic hardware profile validates which backend, and what is still
  uncovered or needs cloud instead of a purchase?
- Which scheduler maps a validation job to a profile (Slurm, Kubernetes,
  HTCondor/OpenPBS), and what stays executor-neutral so executors are not
  run simultaneously?
- Where do prebuilt SDKs (GGML, TVM, llama.cpp) live, and which of them are
  real inference support versus packaging only?

A private operator inventory exists locally. It must never enter tracked
public files: no personal IPs, hostnames, account labels, machine
identifiers, credentials, or private local paths.

## In Scope

- R-1: A native Windows x64 CPU validation profile covering OpenCV DNN with
  OpenCV 5 and ONNX Runtime. Initial execution route is a native CI runner
  outside any cluster; a desktop/laptop Windows OS is not assumed to be a
  supported Kubernetes worker (supported native Windows worker OSes are
  Windows Server 2022/2025).
- R-2: A coverage and purchase assessment: which profiles cover which
  backends, which gaps stay on on-demand cloud/worker use, and an explicit
  statement that no hardware purchase is justified now. Existing hardware
  first; no unused machine is left running to serve a plan.
- R-3: An SDK cache placement recommendation for prebuilt GGML, TVM, and
  llama.cpp backends/SDKs: Linux x86_64 as the main CPU SDK cache; an
  independently built and tested CUDA llama.cpp variant on an NVIDIA worker;
  Windows priority stays OpenCV 5 plus ONNX Runtime, then optional native
  llama.cpp only if required; AMD HIP and ARM variants need their own
  compatible builds and validation; Linux artifacts are never reused as
  native Windows or ARM binaries. Records that GGML and TVM backends
  currently return placeholder outputs, so packaging success is not
  inference support and no GPU SDK variants are distributed before real
  execution is implemented and validated. Records that current shared SDK
  recipes build CPU profiles (CUDA disabled), so publishing an SDK image
  does not validate CUDA/HIP execution.
- R-4: A scheduler evaluation (Slurm with GRES/Features and power saving,
  Kubernetes with a Linux control plane, HTCondor/OpenPBS as alternatives)
  and an executor-neutral job/evidence contract, so one executor runs at a
  time instead of every scheduler simultaneously.
- R-5: An on-demand policy: offline workers wait in a planned/on-demand
  state and are never counted as inference failures; control-plane services
  start only for scheduled sessions unless an always-available queue is
  actually needed.
- R-6: A privacy rule with enforcement: tracked files carry generic
  OS/architecture/accelerator profiles only; the operator inventory stays in
  an untracked local directory ignored by git.
- R-7: Publication in this repository: ADR, architecture placement doc,
  executor-neutral job/evidence contract, scheduled-session runbook,
  packet registration in the roadmap.
- R-8: No silent change to in-flight execution scope: Jetson-class testing
  skipped and AMD hardware testing deferred in the current UI
  release-validation campaign remain true; this packet plans profiles, it
  does not expand that campaign.

## Out Of Scope

- Provisioning, spending, rebooting, powering machines on or off, or joining
  machines to a cluster merely to create a plan.
- Editing `neuriplo` or `neuriplo-ui` implementation branches; that work
  continues in its own sessions under owning-repo instructions.
- Running Slurm, Kubernetes, HTCondor, and OpenPBS simultaneously.
- Windows desktop/laptop machines as Kubernetes workers.
- Building or distributing GPU SDK variants for backends whose execution
  still returns placeholder outputs.
- Counting a Linux profile and a Windows profile observed on similar
  hardware as two concurrent workers without local verification (possible
  dual-boot views of one physical machine).
- Backend execution, model artifacts, serving implementation, and CI runner
  provisioning; those stay in owning repositories and operator hands.

## Decisions Taken

- D-1: Generic profiles, not machines. Tracked files name profile IDs
  (`P-LNX-NVIDIA`, `P-LNX-CPU`, `P-LNX-EDGE-CPU`, `P-LNX-ARM-EDGE`,
  `P-WIN-CPU`, `P-CLD-AMD`, `P-CLD-BURST`). The private inventory mapping
  profiles to hosts lives outside the repo.
- D-2: Executor-neutral contract first, one executor at a time. Slurm is
  the first batch executor for backend-to-profile mapping; Kubernetes is
  evaluated for serving with a Linux control plane. HTCondor/OpenPBS stay
  documented alternatives.
- D-3: No purchase, no always-on fleet. Gaps (AMD GPU, datacenter NVIDIA)
  are covered by on-demand cloud; offline is a planned state.
- D-4: Windows enters through a native runner, not through the cluster.

## Constraints Inherited

- One home per kind of thing: ADR records the decision, the contract
  records the interface, the packet records the work; link, do not restate.
- Nothing declared may be inert: every profile must map to at least one
  backend, and every contract field must have a reader (the runbook or a
  future executor adapter).
- Compatibility is a claim about pinned refs, never about `latest`.
- Implementation lands in the owning repository; this packet is docs,
  contract, and validators only, per ADR 0003.
- All files stay ASCII; `scripts/check_platform.py` must pass.
- Adding a system, package, or runtime dependency anywhere is a forbidden
  change class for automation; this packet adds none.
