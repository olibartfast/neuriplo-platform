# Requirements

Milestone: Local TensorFlow GPU and remote TPU serving

Status: Implemented; compatibility evidence pending

## Goal

Record the accelerator architecture decision for the Neuriplo ecosystem and
define the cross-repository contract needed by [neuriplo](https://github.com/olibartfast/neuriplo),
[neuriplo-infer](https://github.com/olibartfast/neuriplo-infer), and
[neuriplo-tasks](https://github.com/olibartfast/neuriplo-tasks):

- GPU execution is local to the embedded backend, selected by the existing
  `use_gpu` contract.
- TPU execution is remote through a KServe V2 / Open Inference Protocol
  service, selected by endpoint and model name. The client does not own device
  placement.

The packet also records why [neuriplo-kserve-client](https://github.com/olibartfast/neuriplo-kserve-client)
and [neuriplo-kserve-runtime](https://github.com/olibartfast/neuriplo-kserve-runtime)
need no source change for this milestone.

## In Scope

- Update `contracts/configuration-contract.md` to distinguish local device
  selection from remote accelerator selection.
- Add `contracts/tpu-serving-contract.md` for the remote TPU service boundary:
  model artifact, KServe V2 transport, tensor contract, health, and errors.
- Add a TPU serving mode to `docs/architecture/inference-modes.md`, or link a
  dedicated note if the section would become too large.
- Add `ops/runbooks/tpu-serving.md` with the Cloud TPU VM setup, service
  verification, client invocation, and failure diagnosis.
- Add a draft compatibility set in `versions.yaml` only after the owning
  repositories have evidence; the set stays draft until the pins are attested.
- Add this packet to `specs/roadmap.md`.

## Out Of Scope

- In-process PJRT/XLA execution, StableHLO export, `libtpu` linkage, or a new
  `neuriplo` TPU backend. Those require a separate ADR and packet.
- TPU training, multi-host TPU slices, TPU7x, or non-Google accelerators.
- Changes to `neuriplo-kserve-client` or `neuriplo-kserve-runtime` source.
- Changes to repository ownership, GitFlow policy, or release pins.
- Hardware acquisition, cloud quota requests, or cost commitments.
- Declaring a GPU or TPU PASS without attested evidence.

## Decisions

- [D-1] GPU remains local and embedded. `use_gpu` is the selection contract;
  the backend owns session configuration and must fail explicitly when the
  requested device is unavailable.
- [D-2] TPU is remote serving. The client selects an endpoint, model name, and
  version; the TPU-side service owns the device, compiler, and runtime.
- [D-3] No TPU device field is added to the client configuration contract.
  `device: auto | cpu | cuda:<index>` remains local-only.
- [D-4] Existing KServe V2 is sufficient. No protocol extension, new tensor
  datatype, or client change is planned for the first TPU representative.
- [D-5] The first TPU representative is the TensorFlow ResNet-50 classifier,
  using the existing raw-BGR/logits task contract.
- [D-6] Compatibility evidence follows the existing platform evidence pattern;
  a draft set is not a supported combination.

## Constraints

- Platform files are ASCII-only and must pass `scripts/check_platform.py`.
- Repository names must link to GitHub on first mention outside code blocks.
- Do not duplicate implementation detail from the owning repositories; link to
  their packets instead.
- Do not move runtime implementation into this repository.
- TPU hardware claims require exact commands, runtime versions, and expected
  output. Metadata-only evidence is not a TPU pass.

## Assumptions

- [A-1] A TPU-side service can expose the classifier over KServe V2 HTTP
  without changing `neuriplo-infer` or `neuriplo-kserve-client`.
- [A-2] The TensorFlow classifier export remains task-compatible on TPU; the
  probe and validation live in the `neuriplo-tasks` packet.
- [A-3] The local GPU path can reuse the existing `--use-gpu` flag and does not
  require the Phase 3 device/provider contract.

## Open Questions

- [Q-1] Is a dedicated `contracts/tpu-serving-contract.md` justified, or should
  the TPU serving expectations live as a section in the configuration and
  runtime contracts? Recommendation: add the dedicated contract because the
  service boundary spans `neuriplo-infer`, the external service, and future
  operators.
- [Q-2] Which Cloud TPU generation and TensorFlow runtime become the first
  attested combination? Defer to the owning packet's probe result.
- [Q-3] Should the compatibility set include the TPU service image digest in
  addition to the client/runtime pins? Recommendation: yes, record the service
  image or commit because the server is outside the pinned C++ repositories.

## Repository Impact

| Repository | Change | Packet |
|---|---|---|
| `neuriplo` | TensorFlow `use_gpu` behavior, GPU image, tests | `specs/2026-11-09-tensorflow-gpu-remote-tpu/` |
| `neuriplo-tasks` | TPU export validation and recipe | `specs/2026-11-09-tensorflow-gpu-remote-tpu/` |
| `neuriplo-infer` | TensorFlow GPU e2e and remote TPU harness | `specs/2026-11-09-tensorflow-gpu-remote-tpu/` |
| `neuriplo-platform` | Contract, runbook, compatibility evidence | this packet |
| `neuriplo-kserve-client` | No source change; existing KServe V2 client is used | none |
| `neuriplo-kserve-runtime` | No source change; it is not the TPU server | none |
| `videocapture`, `neuriplo-track`, `neuriplo-ui` | No change | none |

## Dependencies

Order of work:

1. `neuriplo`: TensorFlow GPU backend behavior and image.
2. `neuriplo-tasks`: TPU export validation and recipe.
3. `neuriplo-infer`: GPU e2e and remote TPU harness.
4. This platform packet: contract, runbook, and compatibility evidence.

The platform packet does not block the code packets, but it must not claim a
supported combination before their evidence exists.
