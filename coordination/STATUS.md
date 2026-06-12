# Ensemble status board

Last updated: 2026-06-12 (claude, releases cut)

## Lanes

| Agent | Repo(s) | Current work | State |
|---|---|---|---|
| claude | neuriplo | Releases cut: neuriplo v0.6.0, runtime v0.1.0, client v0.3.0, infer v0.6.0; all back-merged | Idle |
| cursor | neuriplo-kserve-runtime, neuriplo-infer | gRPC raw_output_contents track done (runtime #9, infer #24); uncommitted WIP noted in runtime tree (Step 13-2 branch) and neuriplo tree (ROADMAP "Platform Components" + docs paths-ignore CI edit) | Idle / WIP |
| codex | neuriplo-kserve-client | Conformance track closed (client #4, #5); optional backlog: repo-extension conformance, strict OIP live test, workflow_dispatch live CI | Idle |
| human | merges, releases | Queue empty. Release summary in `inbox/human.md` | - |

## Recently landed

- **Release wave 2026-06-12**: neuriplo v0.6.0 (multi-backend builds, plugin
  C ABI, raw-output API), runtime v0.1.0 (first release), client v0.3.0,
  infer v0.6.0 (pins -> neuriplo v0.6.0 + client v0.3.0, validated). All
  release PRs merged (neuriplo #17, client #6, runtime #10), tags pushed,
  master back-merged into develop in all four repos (client develop also
  caught up the previously un-back-merged v0.2.0 commits).
- neuriplo PR #16 (library roadmap + ORT EP plan docs) -> develop.
- gRPC output-encoding track closed end to end: runtime PR #9, client PR #4
  + #5, infer PR #24. Live conformance HTTP + gRPC PASS.

## Known issues / debt

- neuriplo TensorRT metadata test disabled due to crash
  (`backends/tensorrt/test/TensorRTInferTest.cpp:119`) -- top roadmap item.
- Uncommitted agent WIP sitting in two trees: neuriplo (ROADMAP Platform
  Components section + ci.yml docs paths-ignore) and runtime
  (feature/step-13-2-infer-data-plane). Owners should commit or drop.
- Runtime CI checks out neuriplo@develop; consider pinning the v0.6.0 tag
  on release branches.
- Local hygiene: `git pull` on develop in all checkouts (release wave moved
  every develop).
