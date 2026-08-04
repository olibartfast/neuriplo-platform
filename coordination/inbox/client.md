# Inbox: client

## [x] from:human 2026-08-04 -- ensemble conformance (small; wait for the runtime)
`contracts/ensemble-contract.md` is new: encoded-image input plus a fixed
decoded output envelope, transcribed from tritonic v0.4.0 so our runtime and a
Triton deployment are interchangeable behind one client. ADR 0011 has the
rationale.

Your lane is deliberately small, and the reason matters: the client stays a
pure protocol peer. Envelope decoding into task results belongs to the
neuriplo-infer adapter, not here -- do not pull `neuriplo_tasks` types into
`KserveTypes.hpp`.

Nothing on the wire is actually new to you. `UINT8` inputs and
`INT32`/`INT64`/`FP32` raw outputs are already handled
(`src/KserveProtocol.cpp:269-380`), and `ModelMetadata::platform` from v0.4.0
already carries `"ensemble"`. Inner-model metadata needs no API change either:
clients are per-model, so callers construct a second one.

What to add:
1. Verify variable-length `[1, N]` `UINT8` input payloads on both transports --
   that is the one path with no existing coverage.
2. Extend the `kserve-client-conformance` oracle with an ensemble leg:
   `platform: ensemble` in metadata, encoded-image infer round-trip, and all
   four envelope datatypes decoded from `raw_output_contents`.
3. README section on ensemble usage; CHANGELOG under `[Unreleased]`.

Sequencing: the runtime lands first (runtime-infer inbox), so you have a real
ensemble to point the oracle at. Nothing blocks you from writing the tests
against a stub in the meantime.

## [ ] from:neuriplo-agent 2026-06-12 -- after onboarding merges: rebase, commit, PR
Once the human merges neuriplo-kserve-client PR #3 (onboarding +
conformance dry-run): rebase `codex/grpc-raw-contents-conformance` onto
develop, commit your verified work (gRPC raw tests, kserve-client-conformance
oracle, runtime_conformance.sh, CI dry-run step, fp64 tolerance), and open
the PR to develop.

Heads-up on the fp64 tolerance you added: it is the correct workaround
today, and it papers over a real runtime spec deviation (all numeric
outputs widened to `fp64_contents`). The runtime-side fix
(`raw_output_contents = 6` in responses, respond-in-kind) is queued in
the runtime-infer inbox. When that merges, demote the tolerance to a
legacy-compat path in a follow-up -- don't remove it; old runtimes will
still send fp64.

Environment note: the stale process that caused your 404s on ports
19090/19091 was killed; default conformance ports are free again.
