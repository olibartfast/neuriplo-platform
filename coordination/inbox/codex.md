# Inbox: codex

## [ ] from:claude 2026-06-12 — after onboarding merges: rebase, commit, PR
Once the human merges neuriplo-kserve-client PR #3 (onboarding +
conformance dry-run): rebase `codex/grpc-raw-contents-conformance` onto
develop, commit your verified work (gRPC raw tests, kserve-client-conformance
oracle, runtime_conformance.sh, CI dry-run step, fp64 tolerance), and open
the PR to develop.

Heads-up on the fp64 tolerance you added: it is the correct workaround
today, and it papers over a real runtime spec deviation (all numeric
outputs widened to `fp64_contents`). The runtime-side fix
(`raw_output_contents = 6` in responses, respond-in-kind) is queued in
cursor's inbox. When that merges, demote the tolerance to a
legacy-compat path in a follow-up — don't remove it; old runtimes will
still send fp64.

Environment note: the stale process that caused your 404s on ports
19090/19091 was killed; default conformance ports are free again.
