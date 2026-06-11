# Ensemble status board

Last updated: 2026-06-12 (claude)

## Lanes

| Agent | Repo(s) | Current work | State |
|---|---|---|---|
| claude | neuriplo | PR [#15](https://github.com/olibartfast/neuriplo/pull/15) CI disk-space fix | CI running (MIGRAPHX jobs are the signal) |
| cursor | neuriplo-kserve-runtime, neuriplo-infer | Step 15 merged (PR #8); next: `raw_output_contents` in gRPC responses (see inbox) | Idle pending inbox |
| codex | neuriplo-kserve-client | gRPC raw-contents conformance + library oracle, uncommitted on `codex/grpc-raw-contents-conformance` | Waiting on client PR #3 merge, then rebase + commit + PR |
| human | merges, releases | Merge queue: client PR #3 → neuriplo PR #15 | — |

## Recently landed

- neuriplo PR #13 (multi-backend registry) + PR #14 (raw output API) → develop
- runtime PR #6 (multi-backend plugins) + PR #7 (CI ref fix) + PR #8 (Step 15 raw consumption) → develop
- platform PR #2 (CLUSTER_MAP primary-agent ownership) → main
- Live conformance: client ↔ runtime HTTP + gRPC PASS (2026-06-12, raw_input_contents path verified)

## Known issues / debt

- Runtime gRPC responses widen all numeric outputs to `fp64_contents` (spec
  deviation; client carries a tolerance). Fix = cursor's next runtime item.
- neuriplo MIGRAPHX CI disk exhaustion: fix in PR #15, awaiting validation.
- Pending releases: neuriplo v0.6.0 + runtime release (develop → master) once
  the dust settles — human-owned.
