# Plan

Milestone: MCP adapter hardening and host evidence

Status: Implemented (2026-11-10). Groups 2-5 executed, uncommitted; evidence
in `validation.md`.

Phases are thin and in order; each ends in an observable result. Prototype
code and this packet are uncommitted; implementation starts only after the
user approves this packet.

## Group 1 - Setup (intake, done uncommitted)

1. Branch `feature/mcp-agent-tools` created in `neuriplo-infer` from
   `develop`; prototype files carried over untouched (no commits).
2. This packet written on platform `main`: `requirements.md` (done), then
   this `plan.md`, then `validation.md` with acceptance criteria.
3. Roadmap Now table lists both packets; the parent packet records prototype
   status and review intake without altering its evidence.
4. Observable: `specs/2026-11-10-mcp-adapter-hardening/` holds all three
   files with traceable R-H/V-H identifiers.

## Group 2 - P0 correctness (owning repo: neuriplo-infer)

On `feature/mcp-agent-tools`, keeping the change reviewable:

5. R-H1: per-run directory for `neuriplo_run` (D-H1); freshness by
   construction. Regressions: prior-success-then-failure returns the failure
   with no stale report/artifact; success without a new report yields an
   explicit `report_error` and no artifact.
6. R-H2: absolutize `source`/`weights`/`labels` at validation against the
   adapter directory; absolutize the binary once at startup. Regression with
   files in one directory and the run rooted in another.
7. R-H3: strict validation layer: unknown-key rejection (keeping the
   explicit out-of-scope messages), strict `use_gpu` boolean, bool-rejecting
   numerics, type-checked `labels`/`workdir`/timeout, no-argument enforcement
   on `neuriplo_capabilities`, removal of the call-level binary override.
   Each failure names the flag and launches no process.
8. R-H4: streaming capture pump with a memory cap and bytes-safe timeout
   decoding. Regressions: noisy child (megabytes of output) stays bounded;
   timeout returns the timeout error with safely decoded tails.
9. R-H5: protocol review note in code/docs plus envelope tests: malformed
   JSON, missing method, absent versus null id, unknown method, non-object
   params, non-empty capabilities arguments, `server/discover` answered as
   unserved legacy-only.
10. Observable: `python3 scripts/test_mcp_neuriplo_adapter.py` passes with
    the new regressions; imports remain stdlib-only.

## Group 3 - Documentation sync

11. R-H6: `docs/McpAdapter.md` updated to the hardened semantics: run
    directories and retention (D-H4), path rules, legacy-only protocol,
    unchanged tool surface. Link checks pass.
12. Observable: doc and adapter agree on every behavior the validation
    covers.

## Group 4 - Evidence runs

13. R-H7: real inference through the adapter with the Q-H1 triple, recording
    binary revision, task/backend/flags, image, weights path, exit code,
    report status, and artifact; or the exact blocker (no vendored weights,
    no implicit downloads).
14. R-H8: sandboxed host runs: OpenCode v2.2.6 project-local config first
    (`opencode mcp list`, discovery, one `neuriplo_capabilities` call), then
    Hermes v0.23.0 where available. Record host version, negotiated protocol,
    input/output, failures. Never touch global user settings; unattested
    stays unattested.
15. Observable: dated evidence in `validation.md`; nothing presented as
    tested that was only probed.

## Group 5 - Verification and handoff

16. Run the checks in `validation.md`: adapter suite, `check_platform.py`,
    ASCII and link checks.
17. Report changed files, test results, and remaining gaps. No commit, push,
    tag, release, or merge. Await the user's restriction lift and packet
    approval before any of those.

## Group 6 - Follow-up hardening (orchestrated, agents)

18. Implementation agent: bounded capabilities capture (R-H9, D-H5) with
    noisy-capabilities and timeout regressions.
19. Protocol agent: strict envelope validation per inspected specs (R-H10)
    with negative tests; host discovery preserved.
20. Evidence agent: audit claims vs tests (R-H11); peak-memory check or
    narrowed claim, isolation claim narrowed, partial markings kept honest.
21. Orchestrator: review and integrate sequentially, run the full suite and
    required checks, attempt host tool invocation and weighted-model reuse
    within the stated boundaries, close the packet with an integrated review.
