# Validation

Milestone: MCP adapter hardening and host evidence

Status: Ready for further review; MVP acceptance INCOMPLETE (2026-11-10).
Automated checks pass with dated evidence below; M-H1 remains PARTIAL
(failure path attested, weighted SUCCESS blocked) and per-host tool
invocation remains unattested (discovery only: connectivity, not successful
tool execution). This packet is not a merge approval. Nothing committed, pushed, tagged, or merged.

## Automated Checks

- V-H1 (R-H1): regression suite passes. Prior-success-then-failure: seed a
  run directory state with a valid report/artifact from run N, fail run N+1,
  and assert the response carries the failure with no report/artifact from
  run N. Success-without-new-report: fake binary exits 0 without writing a
  report; assert explicit `report_error` and null artifact. Isolation proven
  is uniqueness-by-construction (tempfile.mkdtemp per call, fresh run dir)
  plus sequential request processing (one call at a time in arrival order);
  sequential calls return disjoint run directories. Overlapping execution
  was not exercised and is not claimed.
- V-H2 (R-H2): differing-directory regression passes. Source, weights, and
  labels live in directory A while the run roots in directory B; the child
  receives absolute paths (asserted via echoed argv) and the run succeeds.
  Relative `NEURIPLO_INFER_BIN` resolves against the server startup directory.
- V-H3 (R-H3): strict-validation regressions pass without launching any
  process (fake binary counts invocations; count stays zero). Cases: unknown
  key rejected naming the key; `use_gpu: "false"` (string) rejected;
  `use_gpu: 1` rejected; `min_confidence: true` rejected;
  `labels: 123`, `workdir: 123`, `timeout_s: "300"` rejected with the flag
  named; `neuriplo_capabilities` with any argument rejected; no binary
  override key accepted.
- V-H4 (R-H4): bounded-capture regressions pass. A child emitting megabytes:
  retained buffers stay capped by construction (TAIL_BYTES 256 KiB per
  stream on the run path via TailBuffer discarding beyond the cap;
  CAPABILITIES_MAX_BYTES 1 MiB on the capabilities path with oversize
  rejected) and returned tails hold only the bounded suffix (TAIL_CHARS
  4000 chars via tail()). No peak-allocation measurement was made; the
  noisy-child test asserts returned tail length, not peak capture memory.
  A sleeping child under a short timeout returns the timeout error with
  safely decoded (never crashing) tails, including bytes output.
- V-H5 (R-H5): envelope regressions pass. Malformed JSON yields parse error
  and the server survives; missing method yields Invalid Request; absent id
  yields no response; explicit null id yields a response carrying null id per
  JSON-RPC; unknown method yields Method Not Found; non-object params on
  `tools/call` yield Invalid Params; non-empty capabilities arguments yield
  Invalid Params; `server/discover` is answered as unserved (legacy-only
  documented).
- V-H6 (R-H1..R-H5, R-H9..R-H10): full adapter suite passes:
  `python3 scripts/test_mcp_neuriplo_adapter.py` in `neuriplo-infer`, exit 0,
  with no GPU, no downloads, no sibling checkout.
- V-H7 (R-H6, constraints): `scripts/check_platform.py` passes in
  `neuriplo-platform`; all touched files are ASCII; every added hyperlink
  resolves (relative `ls`, absolute fetch).

## Negative Checks

- N-H1: no shell string composition anywhere in the spawn path; the
  spaces-and-metacharacters argv test still passes after the rework.
- N-H2: no task semantics, backend, or transport logic in the adapter; no
  new imports beyond the Python standard library.
- N-H3: no runtime code in `neuriplo-platform`; the change is the two packet
  directories plus roadmap rows.
- N-H4: out-of-scope inputs (KServe keys, multi-source, video, warmup,
  benchmark) are still rejected with the explicit MVP-scope error.

## Manual / Attested Checks

- M-H1 (R-H7): one real inference run through the adapter. Record: binary
  path and revision, task/backend/flags, image path, weights path, exit code,
  run-report status, artifact path. If weights are unavailable (current
  state: root `model.onnx` is 0 bytes, no vendored weights), record the exact
  blocker and the exact command template instead; do not download weights
  implicitly. A capabilities probe is not an inference run.
- M-H2 (R-H8): sandboxed host validation. OpenCode v2.2.6 first with a
  project-local config in a scratch directory (`opencode mcp list`,
  discovery, one `neuriplo_capabilities` call); then Hermes v0.23.0 where
  available. Record host version, negotiated protocol version, input,
  output, and failures for each. Global user settings are untouched. Any host
  not exercised is named as unattested, not implied.
- M-H3 (R-H6): post-hardening capabilities probe against a working local
  binary re-confirms `schema_version` and workflow/task counts.

## Definition Of Done

V-H1 to V-H7, N-H1 to N-H4, V-H9 to V-H13, and M-H3 pass with dated
evidence below; M-H2 passes for discovery with per-host tool invocation
explicitly unattested; M-H1 is PARTIAL (failure path attested, weighted
SUCCESS blocked with exact blocker recorded); every requirement is
implemented or explicitly deferred with its reason; changed files, test
output, and remaining gaps are reported. Passing these checks means ready
for further review, not accepted: MVP acceptance stays incomplete until
weighted inference and host tool invocation are exercised. Nothing is
committed, pushed, tagged, released, or merged.

## Results

### 2026-11-10 - implemented, uncommitted (this session)

Groups 2-5 executed on `feature/mcp-agent-tools` (uncommitted) and platform
`main` (uncommitted). No commits, pushes, tags, releases, or merges.

Changed files:

- `neuriplo-infer/scripts/mcp_neuriplo_adapter.py` (rewritten): per-run
  directories (D-H1), absolute path semantics with startup-only binary
  resolution (D-H2), strict schema validation with no-spawn rejections and no
  call-level binary override (D-H3), streaming capture pump with 256 KiB
  per-stream cap and bytes-safe timeout kill (R-H4), legacy-only protocol
  with `server/discover` answered as unserved (R-H5), bounded capabilities
  capture with 1 MiB limit (R-H9, D-H5), strict JSON-RPC envelope with
  documented request-id policy (R-H10), version 0.2.1.
  During implementation the rework exposed a real defect in the prototype:
  space-separated valued flags misparse in this binary (source reads as
  "true"); the adapter now emits the repo's own `--key=value` convention
  (verified against `docker_run_inference_example.sh` and the app tests),
  guarded by a regression test.
- `neuriplo-infer/scripts/test_mcp_neuriplo_adapter.py` (rewritten): 36
  tests, all passing in ~4 s with no GPU, downloads, or sibling checkouts.
- `neuriplo-infer/docs/McpAdapter.md`: hardened semantics (run dirs,
  retention, path rules, legacy-only protocol), evidence below, `.json` vs
  `.jsonc` pickup note.
- This packet: requirements/plan/validation plus packet statuses.

V-H1: PASS with narrowed isolation claim. `test_prior_success_not_attributed_to_later_failure` (fresh
rundir per run, no leakage of the prior report/artifact, failure carries its
own `report_error`), `test_success_without_report_is_explicit_not_silent`,
disjoint run dirs across sequential calls. Proven: uniqueness-by-construction
(tempfile.mkdtemp per call) plus sequential processing; overlapping execution
not exercised, not claimed.
V-H2: PASS. `test_paths_resolved_absolute_across_directories` (assets in one
directory, run rooted in another, child receives absolute `--source=`).
V-H3: PASS. `test_capabilities_rejects_arguments_without_spawning`,
`test_unknown_key_rejected`, ten strict-type sub-cases, all with zero fake
spawns via the marker file.
V-H4: PASS with narrowed memory claim. `test_noisy_child_output_stays_bounded` (5 MB child, returned tails stay
within 4000 chars, server alive) proves returned-tail bound, not peak memory.
Proven: retained buffers capped by construction (TAIL_BYTES 256 KiB per stream
via TailBuffer; CAPABILITIES_MAX_BYTES 1 MiB on the capabilities path) and
returned tails capped at TAIL_CHARS 4000 via tail(). `test_timeout_kills_child_and_stays_alive`
(timeout error names `--timeout_s`, follow-up ping answered).
V-H5: PASS. Envelope tests: malformed input, missing method, absent-id
silence, explicit-null-id response, unknown method, non-object params,
non-empty capabilities arguments, `server/discover` legacy-only answer.
V-H6: PASS. Full suite: 36 tests, OK.
V-H7: PASS. `scripts/check_platform.py` prints `platform metadata ok`;
all touched files ASCII; no new hyperlinks added (doc edits reuse the verified
absolute URLs).
V-H9: PASS. `test_capabilities_noisy_is_oversized_error` (2 MB child rejected
with 1 MiB limit named, never parsed as a document), `test_capabilities_truncated_is_parse_error`,
`test_capabilities_slow_times_out` (same tool-error shape, server alive),
`test_capabilities_passthrough` (valid document within limit byte-identical).
V-H10: PASS. Envelope tests: `jsonrpc` missing/wrong value/wrong type yields
-32600 with no dispatch; invalid id types (bool, float, list, dict) yield -32600
with null id; absent id stays silent while explicit null id echoes null id;
malformed input stays -32700; older protocol versions still negotiate;
OpenCode/Hermes discovery handshake preserved.
V-H11: PASS (this audit, retained-buffer restatement chosen). No
peak-allocation check was added: the noisy-child stdio test runs the adapter
in a separate process, so test-side tracemalloc cannot observe adapter heap,
and an in-process tracemalloc probe would measure only Python heap (not total
RSS or OS pipe buffers) with a flaky threshold. The honest proven bound is
retained buffers capped by construction plus returned tails capped, cited
above. Isolation narrowed to uniqueness-by-construction plus sequential
processing. M-H1 and per-host invocation stay PARTIAL/unattested below.

N-H1: PASS. argv array only (spaces/metacharacters test plus `=`-form test).
N-H2: PASS by review plus `test_no_new_dependency_imports` (stdlib only:
`json, os, shutil, subprocess, sys, tempfile, threading, pathlib`).
N-H3: PASS. Platform change is two packet directories plus roadmap rows.
N-H4: PASS. KServe/multi-source/video/warmup/benchmark rejections intact.

M-H1: PARTIAL (failure path attested, weighted SUCCESS blocked). Real-binary
run through the adapter against `build-accel-test/app/neuriplo-infer`
(backend `nert`): `type=yolo`, `source=data/dog.jpg`, `weights=model.onnx`
exits 1 with a fresh `/tmp/neuriplo-mcp-*` run dir, parsed failed report
(`status failed`, stage `model_load`), no artifact, and the binary's own
`empty model file` error. Weighted SUCCESS blocked: the vendored
`model.onnx` is 0 bytes; no CV-task ONNX weights exist anywhere in the
workspace (only transformer node-test models in an unrelated uv cache and
RF-DETR `.pt`/`.pth` checkpoints unusable with the NERT ONNX backend); no
downloads performed. Command template for the owning-repo PR:
`neuriplo_run` with `{type, source=<image>, weights=<maintainer weights>}`.
M-H2: PASS (discovery) with explicit invocation boundary. OpenCode v2.2.6,
sandbox project-local `opencode.json` (`opencode mcp list` reports `neuriplo
connected`); real user configs verified untouched. Hermes v0.23.0, scratch
`HOME` (real `~/.hermes` verified untouched, 0 neuriplo lines):
`hermes mcp test neuriplo` reports connected in 523 ms with 2 tools
discovered. Per-host TOOL INVOCATION was attempted but not achieved: three
`opencode run` sessions against the local Ollama `qwen2.5-coder:7b` (the only
provider available without external credentials; sandbox project config,
sessions ses_e38f9fb3cffeumEzLxXlCOCdZn/ses_mcp_probe_01/ses_mcp_probe_02)
showed the host presenting the tools - the model named
`neuriplo_capabilities` in its output - but emitting text pseudo-calls
instead of invoking (no `tool_result` event; one reply hallucinated
`schema_version 1.0`, actual 2). No external provider session exists here and
none was configured; no credentials touched. Discovery success is not
presented as end-to-end inference.
M-H3: PASS. Post-hardening capabilities re-probe: schema 2, `local` +
`client_server`, 11 tasks, server version 0.2.1.

## Follow-up acceptance criteria (Group 6, implemented; results in V-H9..V-H11 above)

The criteria below were written before implementation and are now closed by
the Group 6 orchestration: Agent 1 (bounded capabilities, via `general`
subagent after two `worker` starts failed with an unavailable model),
Agent 2 (strict envelope, spec-inspected), Agent 3 (evidence audit, claim
narrowing, warning-clean suite). All agent changes were reviewed by the
orchestrator, conflicts resolved by sequencing (no parallel edits to shared
files), and the full suite re-run independently after each agent.

- V-H9 (R-H9): bounded-capabilities regressions pass. A capabilities child
  emitting megabytes: the adapter rejects with a clear oversized error naming
  the 1 MiB limit and never parses a tail as a document. A hanging
  capabilities child under a short timeout reports the same tool-error shape
  as other failures, and the server stays alive. A complete valid document
  within the limit still passes through byte-identical.
- V-H10 (R-H10): envelope regressions pass. A message with `jsonrpc` missing
  or not exactly `"2.0"` yields Invalid Request (-32600), never a method
  dispatch. Request ids outside the valid types yield -32600. Valid ids are
  strings and integers only (bool, float, null, and containers rejected);
  absent id on an otherwise valid message yields no response. Unparseable
  input stays -32700. The OpenCode/Hermes discovery handshake is re-verified
  unchanged.
- V-H11 (R-H11): evidence audit applied. Either a peak-allocation check
  bounds capture memory during the noisy run, or the claim is restated as
  the retained-buffer bound with the code argument cited; isolation is stated
  as uniqueness-by-construction with sequential processing; M-H1 success and
  per-host tool invocation remain partial/unattested with exact blockers.

Remaining gaps: weighted success-path run (Q-H1, needs maintainer weights);
run-directory retention limits (Q-H2, current rule documented: never delete);
P2 structured results; P3 remote/video/HTTP; release-time pins.

## Follow-up round 2 (review findings, written before implementation)

- V-H12: null request ids are rejected. An explicit `id: null` yields
  -32600 (the served 2025-11-25 revision forbids null request ids); no
  method is dispatched and the server stays alive. A new regression test
  replaces the old null-id echo expectation.
- V-H13: timeout cleanup covers the process tree. Descendants holding the
  pipes cannot keep reader threads alive: on timeout (and on lingering
  readers after normal exit) the adapter terminates the child's process
  group, joins the readers, and returns. A new orphan-grandchild regression
  test proves the grandchild is dead, no reader threads linger, and the
  response arrives promptly.

### Round-2 results (2026-11-10, orchestrator-implemented, uncommitted)

V-H12: PASS. `is_valid_request_id` accepts only `str` and exact `int`
(`type(value) is int`, so `bool` stays rejected); present `null` yields
-32600 with a null id and no dispatch. `test_null_id_rejected` replaces the
old echo expectation; the absent-id notification test is unchanged, as is
host discovery (initialize/tools/list untouched).
V-H13: PASS. `start_new_session=True` plus `_kill_tree` (killpg with
child-only fallback) in both `spawn_bounded` and `run_capabilities`;
`_join_readers` with a 2 s linger window on the normal path.
`test_orphan_grandchild_reaped_no_lingering_readers` (grandchild inherits
the pipes and outlives the child): response arrives promptly with
`report_error` set, the grandchild pid is dead on re-check, and no
`mcp-drain-*` threads linger. Full suite: 37 tests, OK, warning-clean
(`-W error::ResourceWarning`).
M-H2 note: per-host tool invocation was additionally attempted via a local
Ollama model; the host presented the tools but the model emitted text
pseudo-calls without invoking. Recorded in `docs/McpAdapter.md` and above;
invocation remains unattested, discovery stands.
