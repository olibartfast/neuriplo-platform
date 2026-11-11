# Requirements

Milestone: MCP agent tools for Neuriplo inference

Status: Implemented (prototype) 2026-11-10. Codex review received same day:
treat the implementation as a prototype, not merge-ready. Correctness hardening
and host evidence move to the completion packet
[2026-11-10-mcp-adapter-hardening](2026-11-10-mcp-adapter-hardening/requirements.md).
Recorded results below are unchanged.

## Problem

Hermes Agent and OpenCode both speak the Model Context Protocol (MCP), but no
`neuriplo-*` component exposes an MCP surface. Agents therefore cannot discover
Neuriplo capabilities or run inference through a declared tool boundary; they
fall back to ad-hoc shell commands with no contract.

Two goals must not be confused:

- Goal A (this packet): let an agent invoke Neuriplo inference workflows as MCP
  tools.
- Goal B (out of scope): supply the agent's underlying LLM. That is an
  OpenAI-compatible server deployment (vLLM or `llama-server`), per ADR 0006,
  not a Neuriplo serving path.

## Findings That Shape The Scope

Established 2026-11-10 by reading the code, before any implementation:

1. [`neuriplo-infer`](https://github.com/olibartfast/neuriplo-infer) owns the
   application boundary that an MCP adapter needs: CLI parsing
   (`app/main.cpp`, `app/inc/CommandLineParser.hpp`), local and KServe wiring
   (`app/src/CLICommands.cpp`, `app/src/KserveEngine.cpp`), capability
   discovery (`app/src/Capabilities.cpp`, `--capabilities`), and
   machine-readable diagnostics (`app/inc/RunReport.hpp`,
   `data/output/run_report.json`). Verified against `develop` (`2c21898`).
2. [`neuriplo-tasks`](https://github.com/olibartfast/neuriplo-tasks) owns
   result types and semantics
   (`contracts/result-contract.md`, Owner: `neuriplo-tasks`). The serialized
   detection shape in that contract is Draft and no producer ships it yet
   ("No producer ships this yet", `contracts/result-contract.md:60-61`). The
   adapter therefore cannot return structured detections in MVP; it returns the
   run report, artifact paths, and bounded logs.
3. [`neuriplo`](https://github.com/olibartfast/neuriplo) owns backend
   execution; [`neuriplo-kserve-client`](https://github.com/olibartfast/neuriplo-kserve-client)
   owns transport. The adapter must shell out to the existing binary with an
   argument array and must not reimplement either.
4. [`neuriplo-ui`](https://github.com/olibartfast/neuriplo-ui) already fronts
   `neuriplo-infer` over HTTP (`GET /api/capabilities`, `POST /api/runs`), but
   it is a browser operator app with a Node.js adapter, not a local MCP
   stdio process. The MCP adapter belongs in `neuriplo-infer`, consistent with
   `docs/architecture/ownership.md:52-62` (local application flow).
5. Both hosts support local stdio servers with no new dependency: OpenCode
   `mcp.servers` `type: local` with `command` (`opencode.ai/v2/docs/mcp-servers/`,
   fetched 2026-11-10); Hermes `mcp_servers` with `command`/`args`/`env`
   (`hermes-agent.nousresearch.com/docs/reference/mcp-config-reference`,
   fetched 2026-11-10). Both default to the legacy `initialize` handshake,
   which is what the adapter implements. Streamable HTTP would need a server
   runtime, auth, and deployment work with no MVP benefit.

## In Scope

- R-1: A stdio MCP adapter owned by `neuriplo-infer`, dependency-free
  (Python 3.12 standard library only), exposing exactly two tools:
  `neuriplo_capabilities` (runs `neuriplo-infer --capabilities`) and
  `neuriplo_run` (runs one supported local still-image inference and returns
  the run report, artifact path, and bounded logs).
- R-2: The adapter reuses existing surfaces only: `--capabilities` JSON,
  existing CLI flags, `data/output/run_report.json`, rendered image artifacts.
  No new inference semantics, no new transport, no task-logic change
  (forbidden classes: `model-io-change`, `inference-logic-change`).
- R-3: Hermes and OpenCode local-stdio configurations that start the adapter,
  verified against the official docs cited above (config text only; live
  agent runs are attested separately, not claimed).
- R-4: Adapter unit tests that run with no GPU, no model download, and no
  sibling checkout (fake `neuriplo-infer` executable), covering the success
  path and the failure paths in `validation.md`.
- R-5: This platform packet records the boundary decision, the tool surface,
  and the evidence. Runtime implementation stays out of
  `neuriplo-platform` per ADR 0003.

## Out Of Scope

- Remote KServe runs through the adapter (`--kserve_endpoint`, multi-source,
  video, warmup/benchmark flags are rejected with an explicit error). Remote
  serving stays on the existing KServe V2 path; the adapter's one supported
  workflow is local still-image inference.
- Structured detection JSON output. Blocked on the Draft
  `contracts/result-contract.md` serialized shape gaining a producer; the
  adapter reports this gap instead of inventing a schema.
- Streamable HTTP transport, OAuth, elicitation, sampling, events. Deferred
  until a deployment needs shared/remote MCP.
- Goal B (agent LLM supply). Answered by ADR 0006: deploy vLLM or
  `llama-server`; no Neuriplo code change.
- Version-matrix changes. The adapter ships with the next `neuriplo-infer`
  release; no compatibility set is claimed by this packet.

## Constraints

- Ownership per `docs/architecture/ownership.md` and
  `ops/repo-meta/neuriplo-infer.yaml`: task semantics stay in `neuriplo-tasks`,
  backend execution in `neuriplo`, transport in `neuriplo-kserve-client`.
- `neuriplo-infer` GitFlow: work on `feature/*` from `develop`, `master` is
  release-only. `neuriplo-platform` work lands on `main` per `AGENTS.md`.
- No new system, package, or runtime dependency
  (`ops/policies.yaml:66-77`, `new-dependency` forbidden). Python standard
  library only.
- ASCII-only files; component names hyperlinked on first mention outside code
  blocks; `scripts/check_platform.py` passes.
- Do not commit or push; leave changes uncommitted for human review.

## Decisions

- D-1: Owner is `neuriplo-infer` (finding 1 and 4), not `neuriplo-ui`
  (browser/Node boundary), not `neuriplo-kserve-runtime` (serving path), and
  not `neuriplo-platform` (control plane holds no runtime code).
- D-2: Transport is stdio, legacy `initialize` handshake. Rationale: both
  hosts support it for local servers, zero deployment, matches the
  single-user local-inference use case. Documented configs use it.
- D-3: Two tools, not a full CLI mirror. `neuriplo_capabilities` +
  `neuriplo_run` is the smallest surface that lets an agent discover and run.
  Model management, repository ops, and benchmark flags are excluded from MVP.
- D-4: `neuriplo_run` returns diagnostics, not detections. The run report is
  the only stable machine-readable output today; the adapter surfaces the gap
  honestly rather than serializing typed results ad hoc.

## Open Questions

- Q-1: Should the follow-up structured-result mode live behind a new
  `neuriplo-infer` flag (for example `--result_json`) owned with the result
  contract, rather than in the adapter? Assumed yes; the adapter only carries
  whatever the binary emits.
- Q-2: Which local task/backend pair is the MVP reference (for example
  detection on NERT/OpenCV-DNN with a bundled test image)? Decided during
  implementation from whatever builds in CI without model downloads; the
  packet records the exact command.
