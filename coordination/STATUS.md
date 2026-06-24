# Ensemble status board

Last updated: 2026-06-24

## Lanes

| Agent role | Repo(s) | Current work | State |
|---|---|---|---|
| neuriplo-agent | neuriplo | Post-release: TensorRT metadata crash (top item), EngineOptions device-selection | Idle |
| runtime-infer-agent | neuriplo-kserve-runtime, neuriplo-infer | raw_output_contents gRPC response fix (see inbox) | WIP |
| client-agent | neuriplo-kserve-client | Post-conformance: rebase and PR after PR #3 merges (see inbox) | Idle |
| human | merges, releases, platform | Queue empty | -- |

## Recently landed

- **Release wave 2026-06-12**: neuriplo v0.6.0 (multi-backend builds, plugin
  C ABI, raw-output API), runtime v0.1.0 (first release), client v0.3.0,
  infer v0.6.0 (pins -> neuriplo v0.6.0 + client v0.3.0, validated). All
  release PRs merged, tags pushed, master back-merged into develop.

## Known issues / debt

- neuriplo TensorRT metadata test disabled due to crash
  (`backends/tensorrt/test/TensorRTInferTest.cpp:119`) -- top roadmap item.
- Uncommitted agent WIP in neuriplo tree (ROADMAP + CI docs paths-ignore)
  and runtime tree (feature/step-13-2-infer-data-plane). Owners should
  commit or drop.
- Runtime CI checks out neuriplo@develop; consider pinning the v0.6.0 tag
  on release branches.
