# Plan

Milestone: Local TensorFlow GPU and remote TPU serving

Status: Implemented; compatibility evidence pending

## Task Groups

1. [x] Contract wording. Update `contracts/configuration-contract.md` to keep
   `device` local-only and to state that a remote TPU service is selected by
   endpoint/model, not by a client device value.
   Delivered: `device`, `precision`, and `use_gpu` are local-only, and remote
   selection is by endpoint, model name, version, and transport.

2. [x] TPU serving contract. Add `contracts/tpu-serving-contract.md` covering:
   - Service responsibility and trust boundary.
   - KServe V2 HTTP and optional gRPC transports.
   - Model artifact and version naming.
   - Input: Float32 NHWC `[1,224,224,3]`, BGR pixels in `[0,255]`.
   - Output: Float32 logits `[1,1000]`.
   - Health/readiness and error mapping.
   - What the client must not assume about the TPU runtime.
   Delivered and linked from the contracts index.

3. [x] Architecture note. Add the remote TPU serving mode to
   `docs/architecture/inference-modes.md`; link the owning packets in
   `neuriplo-tasks` and `neuriplo-infer`. Update
   `docs/architecture/gpu-hardware-considerations.md` only if a GPU/TPU boundary
   clarification is needed.
   Delivered in `docs/architecture/inference-modes.md`; the GPU hardware note
   did not need a change.

4. [x] Runbook. Add `ops/runbooks/tpu-serving.md` with:
   - Cloud TPU VM prerequisites and quota.
   - Service start/health check.
   - `neuriplo-infer` command for the TensorFlow classifier.
   - Expected top-5 output and how to compare with the CPU baseline.
   - Failure diagnosis: endpoint, model name, tensor shape, dtype, readiness.
   - Cost and teardown reminder.
   Delivered in `ops/runbooks/tpu-serving.md`, including evidence recording and
   the intentional absence of a compatibility set.

5. [ ] Compatibility tracking. After evidence exists, add a draft compatibility
   set to `versions.yaml` with the client and runtime pins and the TPU service
   identity. Do not promote it to active without attested hardware evidence.
   Deferred: no draft set is added because no attested GPU or TPU evidence
   exists. The missing compatibility set is intentional, not an omission.

6. [x] Roadmap. Add the packet to `specs/roadmap.md` and record its status.
   Delivered with status "Implemented; compatibility evidence pending".

## Review Order

- Contract review first: it decides whether the TPU service boundary is
  client-owned or server-owned.
- Runbook review second: an operator must be able to reproduce the evidence.
- Compatibility set last: it depends on the owning repositories' results.

## Observable Results

- A reader can tell from the configuration contract that `device` is local-only.
- A reader can tell from the TPU contract how to call the remote service and
  what tensor contract it must honor.
- An operator can run the TPU smoke from the runbook without reading the
  implementation repos first.
- Platform validation passes and no unsupported combination is marked active.
