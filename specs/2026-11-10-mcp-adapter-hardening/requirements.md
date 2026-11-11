# Requirements

Milestone: MCP adapter hardening and host evidence

Status: Implemented 2026-11-10; initial commit was 2026-11-11; continuation
updated 2026-11-11. Weighted success passes for the named local RF-DETR Nano
triple; host-side tool invocation remains unattested. Review fixes remain
uncommitted on `neuriplo-infer` `feature/mcp-agent-tools`. No push, tag, merge,
or release occurred during the continuation. Validation was written before
implementation.

Parent prototype: [2026-11-10-mcp-agent-tools](2026-11-10-mcp-agent-tools/requirements.md),
implemented the same day and reviewed as prototype, not merge-ready.

## Problem

The prototype adapter (`neuriplo-infer` `scripts/mcp_neuriplo_adapter.py` on
uncommitted `feature/mcp-agent-tools`) can attribute stale outputs to the
current run, resolves paths inconsistently across working directories, trusts
callers to match the advertised schemas, buffers unbounded child output, and
has no reviewed claim about which protocol behaviors it actually honors. Host
evidence (OpenCode, Hermes) and a real weighted inference run are unattested.

## Findings That Shape The Scope

Codex review received 2026-11-10 (P0 correctness, P1 evidence). Recon the
same day, read-only, no downloads:

1. `model.onnx` at the `neuriplo-infer` root is 0 bytes: no vendored weights
   exist, so a live weighted run needs a maintainer-supplied weights path.
   Unrelated `.onnx` files under `/tmp/opencode` are not vetted
   task/backend-matched exports and must not be picked up implicitly.
2. The working local binary (`build-accel-test/app/neuriplo-infer`) reports
   local backend `nert` and 11 tasks through the adapter (`schema_version` 2).
3. Both hosts are installed and versioned: OpenCode v2.2.6, Hermes Agent
   v0.23.0. Sandboxed host validation (isolated configs, no global user
   settings) is feasible and required before any compatibility claim.
4. Branch `feature/mcp-agent-tools` exists in `neuriplo-infer` from `develop`
   with the prototype as uncommitted files; platform work stays on `main`.

## In Scope

- R-H1: Per-run isolation. Every `neuriplo_run` executes in a unique run
  directory, so `run_report.json` and rendered artifacts are always fresh and
  each run's outputs are unique by construction (requests are served one at a
  time; overlapping execution is not exercised and not claimed). Prior-success-then-failure and success-without-new-report cases are covered by
  regression tests.
- R-H2: Consistent path semantics. `source`/`weights`/`labels` are validated
  against the adapter process directory and normalized to absolute paths
  before the child changes directory; the binary path is absolutized once at
  server startup. Differing-directory cases are covered by tests.
- R-H3: Server-side schema enforcement. Unknown keys are rejected, `use_gpu`
  must be a real boolean (the string `"false"` is truthy and must not enable
  it), booleans are not accepted as numbers, and wrong-typed
  `labels`/`workdir`/timeout fields fail with the flag named. Executable
  selection moves to server startup/env configuration only; the undocumented
  call-level binary override is removed, and `neuriplo_capabilities` enforces
  its advertised no-argument shape. All validation failures happen before any
  process is launched.
- R-H4: Bounded capture. Child stdout/stderr are pumped with a memory cap
  (bounded tails retained); the timeout path decodes safely even when the
  child emits bytes. Noisy-child and timeout regressions included.
- R-H5: Protocol envelope review. The adapter documents exactly what it
  honors: legacy `initialize` handshake over stdio (claimed revisions
  `2025-11-25` and earlier fallbacks), `notifications/initialized`,
  `ping`, `tools/list`, `tools/call`; the 2026-07-28 revision
  (`server/discover`) is explicitly not served and both hosts default to the
  legacy handshake. Envelope tests cover malformed input, missing method,
  absent versus null ids, unknown methods, and non-empty capabilities
  arguments.
- R-H6: Documentation sync. `docs/McpAdapter.md` describes the hardened
  semantics (run directories, retention, path rules, legacy-only protocol);
  packet statuses stay consistent with what was actually run.
- R-H7: One real inference run through the adapter with a named
  task/backend/image/weights triple and recorded revisions, or an exact
  documented blocker if weights remain unavailable. No implicit downloads.
- R-H8: Host validation from the installed OpenCode v2.2.6 first, then Hermes
  v0.23.0 where available, with isolated test configs. Record host version,
  protocol version, input, output, and failures. Absent evidence stays
  explicitly unattested; a real-binary capabilities probe is not presented as
  end-to-end inference.

Follow-up scope (orchestrated 2026-11-10, implements review remainders):

- R-H9: Bounded capabilities capture. `run_capabilities` reuses the
  bounded-capture discipline with an explicit maximum document size: a complete
  valid capabilities JSON within the limit passes through; oversized or
  truncated output is rejected clearly rather than parsed as a full document.
  Launch failure and timeout report in the same tool-error shape as other
  failures. Noisy-capabilities and timeout regressions included.
- R-H10: Strict JSON-RPC envelope. `jsonrpc` must be exactly `"2.0"`; request
  ids are strings and integers only - null is rejected because the served
  2025-11-25 revision forbids null request ids (bool, float, and containers
  likewise rejected); malformed messages, structurally invalid requests, and
  valid notifications are distinguished (-32700 vs -32600 vs no response).
  Working host discovery is preserved.
- R-H11: Honest evidence claims. The peak-memory bound is backed by a
  peak-allocation check or restated as the retained-buffer bound it proves;
  run isolation is stated as uniqueness-by-construction with sequential
  processing (no overlapping-execution claim); weighted success and host tool
  invocation stay partial/unattested until exercised.
- R-H12: Process-tree cleanup on timeout. The child runs in its own process
  group; on timeout (and on readers lingering after normal exit) the adapter
  terminates the group, so descendants holding the pipes cannot keep reader
  threads alive. Proven by an orphan-grandchild regression test.

## Out Of Scope

- Structured result production (P2): owned by
  [`neuriplo-tasks`](https://github.com/olibartfast/neuriplo-tasks) semantics
  and [`neuriplo-infer`](https://github.com/olibartfast/neuriplo-infer)
  serialization; specified after this packet.
- Remote KServe, video/batch workflows, progress/cancellation, Streamable
  HTTP (P3): only after validated demand; reuse of the existing
  [`neuriplo-ui`](https://github.com/olibartfast/neuriplo-ui) HTTP adapter is
  reassessed then.
- Version-matrix pins and compatibility claims: release-time work only.

## Constraints

- [`neuriplo-infer`](https://github.com/olibartfast/neuriplo-infer) GitFlow:
  implementation on `feature/mcp-agent-tools` from `develop`; `master` is
  release-only. Platform changes stay on `main`.
- No new dependency (`ops/policies.yaml` forbids `new-dependency`): Python
  standard library only.
- No implicit model downloads; every weighted run names its weights path.
- ASCII-only files; component names hyperlinked on first mention outside code
  blocks; `scripts/check_platform.py` passes.
- No commit, push, release, or merge until the user's restriction is lifted.

## Decisions

- D-H1 (proposed, reviewer confirms): per-run directory created per call
  (under the system temp area, or under the caller-given `workdir` when one
  is supplied), used as the child working directory so the fixed
  `data/output/run_report.json` path is inherently fresh.
- D-H2: executable selection is startup/env configuration only; call-level
  binary override is removed rather than documented.
- D-H3: the adapter serves the legacy handshake only and says so; hosts must
  use their default legacy mode (both do).
- D-H4: the adapter never deletes run directories; the caller copies out
  needed artifacts. Disk growth is documented, not silently managed.
- D-H5 (proposed): capabilities document limit 1 MiB, generous against the
  ~10 KiB actual size; anything larger is an anomaly and fails loudly.

## Open Questions

- Q-H1: reference asset triple for R-H7. Blocked: `model.onnx` is 0 bytes
  and no vendored weights exist. The implementation phase specifies the exact
  command template and runs it only against a maintainer-supplied weights
  path, or records the blocker verbatim.
- Q-H2: run-directory retention limits (age/size caps, host-visible cleanup
  tool). Deferred; D-H4 documents the current no-delete rule.


## Authorization update (2026-11-11)

The maintainer authorized a read-only search of already-downloaded local model
weights, with no downloads. That search found an existing RF-DETR Nano ONNX
export matching its checked-in export manifest and task preprocessing and
postprocessing contract. The resulting real weighted adapter run and its
provenance are recorded in `validation.md`; Q-H1 is resolved for this local
evidence triple. No general model discovery or implicit download behavior was
added to the adapter.
