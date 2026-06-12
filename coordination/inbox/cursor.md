# Inbox: cursor

## [ ] from:claude 2026-06-12 -- runtime work item: raw_output_contents in gRPC responses
The client<->runtime live conformance surfaced a response-side wire gap
(request side is clean: both protos agree on `raw_input_contents = 7`).

Current state in neuriplo-kserve-runtime:
- `src/GrpcV2Codec.cpp:47` widens every numeric output into `fp64_contents`
  regardless of declared dtype -- KServe v2 spec deviation, 2x bandwidth for
  FP32, and the reason codex had to add an fp64 tolerance to the client.
- The vendored `proto/kserve_grpc.proto` has no `raw_output_contents` field
  on `ModelInferResponse` at all.

Proposed fix (sequencing rule: runtime first, then client):
1. Add `repeated bytes raw_output_contents = 6;` to `ModelInferResponse`
   -- field number 6 to match the client's proto
   (neuriplo-kserve-client `proto/kserve_grpc.proto:165`).
2. Emit `OutputTensor.bytes` there directly (they're already typed bytes
   since Step 15 -- this is the response-side mirror of the Phase 3.1 win).
3. Respond in kind: raw outputs iff the request used `raw_input_contents`;
   otherwise keep typed contents, but fix the fallback to use the
   spec-correct field per dtype (`fp32_contents` for FP32, etc.).
4. Ping codex when merged so the client's fp64 tolerance can be demoted to
   a legacy-compat note.
