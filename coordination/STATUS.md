# Ensemble status board

Last updated: 2026-06-12 (claude, release prep)

## Lanes

| Agent | Repo(s) | Current work | State |
|---|---|---|---|
| claude | neuriplo | Release prep done: neuriplo PR #17 (release/v0.6.0), client PR #6 (release/0.3.0), runtime PR #10 (develop->master v0.1.0); infer cut waits on tags | Waiting on human |
| cursor | neuriplo-kserve-runtime, neuriplo-infer | gRPC raw_output_contents track done (runtime #9, infer #24); uncommitted WIP noted in runtime tree (Step 13-2 branch) and neuriplo tree (ROADMAP "Platform Components" + docs paths-ignore CI edit) | Idle / WIP |
| codex | neuriplo-kserve-client | Conformance track closed (client #4, #5); optional backlog: repo-extension conformance, strict OIP live test, workflow_dispatch live CI | Idle |
| human | merges, releases | Release queue in `inbox/human.md`: merge neuriplo #17 + tag v0.6.0, client #6 + tag v0.3.0, runtime #10 + tag v0.1.0, then infer `cut_release.sh 0.6.0` | - |

## Recently landed

- neuriplo PR #16 (library roadmap + ORT EP plan docs) -> develop, full CI green.
- Release branches cut and PRs opened: neuriplo #17, client #6, runtime #10.
- gRPC output-encoding track closed end to end: runtime PR #9, client PR #4 + #5,
  infer PR #24. Live conformance HTTP + gRPC PASS.
- platform PR #4 (status refresh) -> main.

## Known issues / debt

- neuriplo TensorRT metadata test disabled due to crash
  (`backends/tensorrt/test/TensorRTInferTest.cpp:119`) -- top roadmap item.
- Uncommitted agent WIP sitting in two trees: neuriplo (ROADMAP Platform
  Components section + ci.yml docs paths-ignore) and runtime
  (feature/step-13-2-infer-data-plane). Owners should commit or drop.
- Runtime CI checks out neuriplo@develop; release builds should pin the
  v0.6.0 tag once it exists.
- After each develop->master release merge: immediate back-merge into
  develop (client master still carries un-back-merged v0.2.0 commits).
