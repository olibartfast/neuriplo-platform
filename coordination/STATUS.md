# Ensemble status board

Last updated: 2026-06-12 (claude)

## Lanes

| Agent | Repo(s) | Current work | State |
|---|---|---|---|
| claude | neuriplo | PR [#16](https://github.com/olibartfast/neuriplo/pull/16) library roadmap + ORT EP plan docs (reconciled cursor/codex drafts) | CI running |
| cursor | neuriplo-kserve-runtime, neuriplo-infer | gRPC raw_output_contents track done (runtime #9, infer #24) | Idle |
| codex | neuriplo-kserve-client | Conformance track closed (client #4, #5); optional backlog: repo-extension conformance, strict OIP live test, workflow_dispatch live CI | Idle |
| human | merges, releases | Merge queue: neuriplo PR #16; then release cuts (client + runtime tags, neuriplo v0.6.0, bump versions.env pins in infer) | - |

## Recently landed

- gRPC output-encoding track closed end to end: runtime PR #9
  (raw_output_contents in responses), client PR #4 + #5 (oracle, fp64
  tolerance demoted to legacy-compat), infer PR #24 (compat matrix:
  runtime gRPC validated). Live conformance HTTP + gRPC PASS.
- neuriplo PR #15 (CI disk-space fix) -> develop, post-merge CI green.
- platform PR #3 (this coordination mailbox) -> main.

## Known issues / debt

- neuriplo TensorRT metadata test disabled due to crash
  (`backends/tensorrt/test/TensorRTInferTest.cpp:119`) -- top roadmap item.
- Pending releases: neuriplo v0.6.0 + runtime/client release cuts
  (develop -> master) -- human-owned.
- Local hygiene: `git pull` on develop in client/infer/runtime checkouts.
