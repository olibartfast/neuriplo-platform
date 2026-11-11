# Validation

Milestone: MCP agent tools for Neuriplo inference

Status: Implemented (prototype) 2026-11-10; review intake recorded below.
Written before implementation; each check names
the requirement it closes.

## Automated Checks

- V-1 (R-1, R-2): Adapter unit suite passes with no GPU, no downloads, no
  sibling checkout:
  `python3 scripts/test_mcp_neuriplo_adapter.py` in `neuriplo-infer`, exit 0.
  Covers: `initialize` handshake with `protocolVersion` negotiation and
  `tools/list` returning exactly `neuriplo_capabilities` and `neuriplo_run`;
  capabilities passthrough from a fake binary; run success returning
  `exit_code 0` with parsed `run_report` and `artifact`; missing source fails
  naming the flag; KServe/remote flags are rejected with an explicit MVP-scope
  error; unknown tool and malformed JSON-RPC return errors, not crashes.
- V-2 (R-1): No new dependency. The adapter imports standard-library modules
  only (verified by scanning imports); `ops/policies.yaml` forbidden class
  `new-dependency` is not triggered.
- V-3 (R-5): `scripts/check_platform.py` passes in `neuriplo-platform` with
  the packet present.
- V-4 (R-3): Every hyperlink added by the packet and the adapter doc resolves:
  relative paths exist (`ls`), absolute GitHub and vendor doc URLs are
  reachable (`curl -sI` or fetch, recorded below).

## Negative Checks

- N-1 (R-2): The adapter never uses shell string composition for the infer
  invocation (argv array only); a test asserts a source path with spaces and
  metacharacters is passed as one argv element.
- N-2 (R-2): No task semantics, backend, or transport code in the adapter: no
  imports from `neuriplo-tasks`/`neuriplo`/`neuriplo-kserve-client`, no ONNX or
  tensor logic; review of the diff confirms a thin process wrapper.
- N-3 (R-5): No runtime code in `neuriplo-platform`: the packet adds only
  `specs/2026-11-10-mcp-agent-tools/` prose.
- N-4 (Out of scope): `neuriplo_run` rejects `--kserve_endpoint`-style remote
  parameters and multi-source/video/warmup/benchmark requests with an explicit
  error; covered by a unit test.

## Manual / Attested Checks

- M-1 (R-1): Real-binary probe: the adapter's `neuriplo_capabilities` path
  against a working local `neuriplo-infer` build (for example
  `build-accel-test/app/neuriplo-infer --capabilities`, which exits 0 in this
  environment) returns `schema_version` 2 JSON. Record the exact binary path,
  byte count, and observed `schema_version`.
- M-2 (R-3): Hermes and OpenCode snippets are transcribed from the official
  docs fetched 2026-11-10 (`opencode.ai/v2/docs/mcp-servers/`,
  `hermes-agent.nousresearch.com/docs/reference/mcp-config-reference`) and the
  packet states that live agent runs (Hermes/OpenCode actually invoking the
  adapter end to end with model weights) were or were not performed.
- M-3 (Q-2): The one supported workflow is named exactly (task, backend,
  flags, image), or explicitly left to the owning-repo PR if weights are
  unavailable in this environment.

## Definition Of Done

V-1 to V-4, N-1 to N-4, and M-1 to M-3 pass with dated evidence below; changed
files, test output, and remaining gaps are reported; nothing is committed or
pushed.

## Results

### 2026-11-10 - implementation and evidence (this session)

Implemented on top of the specified packet, uncommitted, no push.

Changed files:

- `neuriplo-platform/specs/2026-11-10-mcp-agent-tools/requirements.md` (new)
- `neuriplo-platform/specs/2026-11-10-mcp-agent-tools/plan.md` (new)
- `neuriplo-platform/specs/2026-11-10-mcp-agent-tools/validation.md` (this file)
- `neuriplo-infer/scripts/mcp_neuriplo_adapter.py` (new, executable)
- `neuriplo-infer/scripts/test_mcp_neuriplo_adapter.py` (new)
- `neuriplo-infer/docs/McpAdapter.md` (new)

V-1: PASS. `python3 scripts/test_mcp_neuriplo_adapter.py` in `neuriplo-infer`:
12 tests, OK (0.5 s). Fake-binary stdio coverage for handshake, tool listing,
capabilities passthrough, run success (report + artifact), missing `--source`,
KServe-scope rejection, unknown tool, malformed JSON, binary failure, and
argv-array safety. Real C++ suite not re-run: no C++ file was touched and the
stale `build-test` binary in this checkout has a pre-existing ABI mismatch
(`build-test/app/neuriplo-infer` exits 127 on `--capabilities`); the adapter
suite is the affected surface.

V-2: PASS. Adapter imports are stdlib only
(`json, os, shutil, subprocess, sys, pathlib`); asserted by
`PureValidationTest.test_no_new_dependency_imports`.

V-3: PASS. `python3 scripts/check_platform.py` in `neuriplo-platform` prints
`platform metadata ok`, exit 0, with the packet present.

V-4: PASS. Relative targets exist (`contracts/result-contract.md`,
`docs/architecture/ownership.md`,
`docs/adr/0006-generative-serving-over-openai-protocol.md`,
`ops/policies.yaml`, `ops/repo-meta/neuriplo-infer.yaml`). Absolute URLs
return 200: all five GitHub repo URLs, the Hermes MCP config reference, and
`https://opencode.ai/docs/mcp-servers/` (the `/v2/` URL cited at fetch time
301-redirects to this canonical URL; the doc now cites the canonical one).

N-1: PASS. argv array only, no shell; covered by the metacharacter-filename
test. N-2: PASS by review: no task/backend/transport code in the adapter, it
spawns the binary and parses existing outputs. N-3: PASS: platform change is
the prose packet only. N-4: PASS: KServe keys rejected, covered by unit test.

M-1: PASS (probe, not a full inference run). Adapter against
`build-accel-test/app/neuriplo-infer --capabilities` returns `schema_version`
2, workflows `local` + `client_server`, 11 tasks, 9858 bytes. Note:
`build-test/app/neuriplo-infer` in this checkout is stale (ABI mismatch, exit
127) and was not used.
M-2: PASS (config text). Snippets transcribed from the official docs fetched
2026-11-10 (OpenCode local `type: local` + `command`; Hermes `mcp_servers`
`command`/`args`/`env` + `timeout`). Live Hermes/OpenCode sessions invoking
the adapter end to end were not performed; the doc marks them unattested.
M-3: Supported workflow named: local still-image inference
(`--type/--source/--weights/--no_display` as wrapped by `neuriplo_run`). A
live weighted run is left to the owning-repo PR; the doc records this.

Remaining gaps at implementation time: live agent runs, Streamable HTTP,
structured detections (blocked on the result-contract Draft). The
`roadmap.md` packet-index entry was added during review intake below.

### 2026-11-10 - Codex review intake (no code changes)

External review of the session analysis, this packet, and the adapter source:
ownership and local stdio MVP are appropriate; the implementation is a
prototype, not merge-ready. Findings P0 (correctness: stale-output
attribution, path semantics, schema enforcement, unbounded capture, protocol
envelope review) and P1 (evidence: branch discipline, roadmap entry, real
inference run, host validation) are replanned, not fixed here. The completion
packet is `specs/2026-11-10-mcp-adapter-hardening/`; its `validation.md`
holds the acceptance criteria. Trivial doc nits from the review (broken prose
in `docs/McpAdapter.md`, cross-repo relative link) were fixed directly in the
uncommitted draft. Everything remains uncommitted.
