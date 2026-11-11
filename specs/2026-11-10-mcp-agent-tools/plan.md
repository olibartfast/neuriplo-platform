# Plan

Milestone: MCP agent tools for Neuriplo inference

Status: Implemented (prototype) 2026-11-10. Codex review received same day;
Groups 2-4 below delivered the prototype. Hardening (P0) and host evidence
(P1) are replanned in
[2026-11-10-mcp-adapter-hardening](2026-11-10-mcp-adapter-hardening/plan.md).

Phases are thin and in order: each ends in an observable result. Work that
touches `neuriplo-infer` code follows that repo's GitFlow (`feature/*` from
`develop`); platform packet work stays on `main` and is not committed by the
agent.

## Group 1 - Platform packet (this directory)

1. Write `requirements.md` (done), then `validation.md` before any adapter
   code, then this `plan.md`.
2. Keep the packet ASCII-only, hyperlinked per `AGENTS.md`, and scoped so
   `scripts/check_platform.py` passes unchanged (no new examples or
   integration-test directories in this packet).
3. Observable: `specs/2026-11-10-mcp-agent-tools/` holds all three files with
   traceable R/V identifiers.

## Group 2 - Adapter implementation (owning repo: neuriplo-infer)

Branch `feature/mcp-agent-tools` from `develop` in `neuriplo-infer`.

4. Add `scripts/mcp_neuriplo_adapter.py` (executable, Python 3.12, standard
   library only): stdio JSON-RPC loop implementing `initialize`,
   `notifications/initialized`, `ping`, `tools/list`, `tools/call`; tools
   `neuriplo_capabilities` and `neuriplo_run` exactly as specified.
   `neuriplo_run` builds an argv array (no shell), enforces single still-image
   local inference, passes `--no_display`, applies a timeout, and returns
   `exit_code`, parsed `run_report`, `artifact`, and bounded `stdout`/`stderr`
   tails. Unknown methods, tools, and bad params return JSON-RPC errors.
5. Add `scripts/test_mcp_neuriplo_adapter.py` (unittest, stdlib only): fake
   `neuriplo-infer` executable tests for handshake, tool listing, capabilities
   passthrough, run success (report + artifact), missing-source failure naming
   the flag, KServe-flag rejection, unknown-tool error, and malformed-request
   handling. No GPU, no downloads, no sibling checkout.
6. Add `docs/McpAdapter.md` in `neuriplo-infer`: tool reference, Hermes
   `mcp_servers` snippet and OpenCode `mcp.servers` snippet per the official
   docs, timeout guidance for long inference, and an explicit statement of
   what is tested versus proposed (no structured detections in MVP).
7. Observable: `python3 scripts/test_mcp_neuriplo_adapter.py` passes; the
   adapter drives a real `neuriplo-infer --capabilities` binary for at least
   the capabilities path in manual verification.

## Group 3 - Documentation and contract notes

8. In `docs/McpAdapter.md`, cite the exact official doc URLs consulted and the
   fetch date; mark live agent runs as unattested if no live Hermes/OpenCode
   run with model weights was available.
9. Note the `contracts/result-contract.md` Draft gap in the doc and in the
   adapter's `neuriplo_run` description so agents do not expect detections.
10. Observable: every hyperlink added resolves (`ls` for relative,
    `curl -sI`/fetch for absolute).

## Group 4 - Verification

11. Run the checks declared in `validation.md` and record dated evidence
    there: adapter unit tests, `scripts/check_platform.py`, link checks, and
    the real-binary capabilities probe.
12. Report changed files, test results, and remaining gaps. Do not commit or
    push; do not merge, tag, or cut a release.
