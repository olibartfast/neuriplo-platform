# ADR 0009: Evolve platform focus to AI Infrastructure and GPU-first serving

Date: 2026-06-18

Status: Accepted

## Problem

neuriplo is documented as a computer vision inference ecosystem: CV task
contracts (detection, segmentation, pose, depth, classification) with video
capture as a first-class source. That label no longer matches what the codebase
is or where 2026 demand sits.

What the ecosystem already ships is serving infrastructure:

```text
neuriplo-kserve-runtime  KServe V2 server: admission, scheduling, dynamic batching
neuriplo                 backend abstraction over ONNX Runtime, TensorRT, OpenVINO
neuriplo-kserve-client   KServe V2 / Open Inference Protocol client (HTTP + gRPC)
```

There is already measured serving evidence. The EdgeCrafter `ecdet` transport
benchmark (`integration-tests/kserve-runtime-edgecrafter-e2e/BENCHMARK.md`)
isolated a ~1.27 s gap between HTTP/JSON and binary/gRPC tensor transport on a
~4.7 MB image tensor, with server compute held near 100 ms. That is an
infrastructure result, not a CV-model result.

The "CV inference" framing therefore misleads on three counts:

1. It hides the serving and GPU-backend investment from the AI infrastructure
   audience that 2026 hiring and European sovereign-AI compute spend are aimed
   at.
2. It implies a CV ceiling on `neuriplo-tasks`, which can serve any model that
   fits the preprocess/execute/postprocess contract (NLP embeddings, audio,
   tabular, generative postprocessing).
3. It undersells the predictive/generative serving split (ADR 0006), which is a
   serving-quality differentiator, not a model-family feature.

## Constraints

- `neuriplo-platform` is the control plane (ADRs, contracts, version matrix,
  tests, examples) and holds no runtime code. This ADR changes positioning and
  documentation only.
- Repository boundaries and names are unchanged; ADR 0004 already settled the
  `vision-*` to `neuriplo-*` rename.
- CV stays a fully supported task domain. De-emphasis is about framing, not
  removal.
- Claims must separate implemented from planned. Multi-GPU scheduling,
  multi-node scale-out, and GPU capability reporting are roadmap gaps, not
  shipped features, and must be stated as such.

## Options

1. **Keep the CV framing** and let the infrastructure work speak for itself.
   Rejected: a platform that ships a KServe runtime, dynamic batching, and an
   Open Inference Protocol client should say so at the top.
2. **Reposition as an AI infrastructure / GPU-first serving platform with CV as
   the first task domain.** Selected.
3. **Split CV tasks into a separate repo now.** Rejected as premature: no
   second task domain exists yet, so the split would add repo overhead with no
   payoff. Revisit when a non-CV domain ships.

## Decision

Adopt Option 2. Lead all platform-level docs with AI inference serving, GPU
backend abstraction, and the Open Inference Protocol; present CV as the first
task domain rather than the platform identity.

Concrete changes (all landed with this ADR):

```text
positioning   README, overview, ownership, inference-modes reframed
roadmap       production-roadmap sections 12-15 added:
              12 GPU optimization and multi-GPU scheduling
              13 AI datacenter deployment (incl. multi-node / HPC scale-out)
              14 benchmarking contract and performance regression
              15 GPU hardware architecture considerations
contracts     gpu-capability-contract.md   (owner: neuriplo)
              benchmarking-contract.md      (owner: platform; repos own benchmarks)
architecture  gpu-hardware-considerations.md
evidence      benchmarking contract drafted; transport latency comparison
               (HTTP JSON vs binary vs gRPC) recorded in
               integration-tests/kserve-runtime-edgecrafter-e2e/BENCHMARK.md
```

Boundaries preserved: `videocapture` stays a valid (CV-domain) source layer,
CV task contracts stay supported, and both embedded-local and remote-KServe
inference modes remain.

Non-goals: renaming repos, removing CV support, adding runtime/GPU code to the
platform repo, or claiming any roadmap gap (multi-GPU, scale-out, capability
reporting) is implemented.

## Consequences

Positive:

- Platform language matches the shipped serving infrastructure and the measured
  transport benchmark, so the AI-infrastructure thesis is backed by evidence,
  not assertion.
- `neuriplo-tasks` is freed from an implied CV ceiling; new domains are
  extensions, not exceptions.
- Infrastructure gaps (multi-GPU scheduling, benchmarking baselines, throughput
  SLAs, multi-node scale-out) are named and tracked in the roadmap and its
  Definition of Done.

Negative / cost:

- CV-oriented docs are reframed, creating brief inconsistency until every
  reference is updated.
- A future non-CV domain forces a deferred decision on task-layer repo
  structure (single repo vs. per-domain repos).
- The benchmarking contract is enforceable but thinly populated: one
  single-stream baseline on one machine. Throughput sweeps and percentile data
  remain to be collected.

Remaining work (deferred, not blocking this ADR):

- Implement GPU capability reporting in `neuriplo` against the contract.
- Collect a throughput sweep (batch 1/4/8/16, requests/sec, GPU utilization) to
  fill the null metrics in the baseline result.
- Wire benchmark baselines into a `versions.yaml` compatibility set.
- Decide task-layer repo structure when a second task domain ships.
