# Roadmap

Living document. It sequences platform work into milestone packets and records
why the order is what it is. It is deliberately short: the backlog of
production-readiness gaps lives in
[`docs/architecture/production-roadmap.md`](../docs/architecture/production-roadmap.md),
and this file only says which of those gaps are being cut into packets next.

Last updated: 2026-08-19

## How To Read This

- **Production roadmap** = the standing list of what production readiness
  requires. It changes when the definition of done changes.
- **This roadmap** = what is being worked on and what comes next, as packets.
  It changes when a packet opens or closes.
- **A packet** = one dated directory here, holding `requirements.md`,
  `plan.md`, and `validation.md`. It is the unit that gets branched, reviewed,
  and merged.

A production-roadmap item is not a packet. It becomes one when someone can state
what the work is, cut it into independently verifiable groups, and say in
advance what evidence closes it.

## Now

| Packet | State |
|---|---|
| [2026-08-17-control-plane-validation-hardening](2026-08-17-control-plane-validation-hardening/requirements.md) | Specified, not implemented. `scripts/check_all.py` does not exist yet. |

The thesis of the current packet is that this repository declares more checks
than it enforces: a benchmark validator that discovers zero files and exits 0,
two hermetic scenario checkers CI never runs, performance gates in
[`ops/policies.yaml`](../ops/policies.yaml) that nothing compares against, and
ten contracts with no validator reading them. Until one command decides pass or
fail, every later packet has to argue about which checks it should have run.
That is why it is first.

## Next

Candidate packets, in the order they should be cut. Each names the item it
closes. Nothing below is committed until it has a dated directory.

1. **Spec-packet validation.** A validator for `specs/` itself: the living
   documents exist, every dated directory holds all three files, and each
   declares its milestone and status. Deferred out of the current packet on the
   grounds that one packet is not a convention; with a second packet it is.
2. **Populate the null baselines.** All three baselines referenced by
   [`versions.yaml`](../versions.yaml) hold null metrics. The current packet
   makes the regression gate skip nulls visibly; this one runs the hardware and
   removes the skips. Closes the measurement half of production-roadmap item 14.
3. **Cross-repository build and test CI.** Clone the pinned refs, configure,
   build, run unit tests, and run one local and one KServe smoke per
   compatibility set, so a set cannot be declared compatible without being built
   from source. Production-roadmap item 2. This one is not hermetic and needs a
   deliberate decision about where it runs.
4. **Contract promotion.** The current packet adds `Version` and a closed
   `Status` set; every contract still says `Draft`. Promoting one to `Review` or
   `Stable` is a per-contract human review, and is worth a packet because the
   promotion criteria have to be written down once.
5. **Live serving evidence for the generative path.** The OpenAI-compatible path
   is decided ([ADR 0006](../docs/adr/0006-generative-serving-over-openai-protocol.md))
   and has a metadata smoke scaffold; it has no live `llama-server` or
   vLLM-backed evidence. Production-roadmap item 11.
6. **Executable failure-mode evidence.** The failure matrix in
   [`integration-tests/failure-modes/`](../integration-tests/failure-modes) is
   metadata only. Attach runtime and client evidence for the public serving
   failures. Production-roadmap item 8.
7. **Observability contract.** Names, dimensions, and error fields for logs,
   metrics, and traces, so serving signals are comparable across repos.
   Production-roadmap item 4.
8. **Agent role definitions and handoff packets.** Generate per-role definitions
   with write allowlists from [`ops/CLUSTER_MAP.yaml`](../ops/CLUSTER_MAP.yaml),
   and move the `coordination/` inbox to a handoff-packet shape. Both were
   deferred out of the current packet.

## Later

Tracked in
[`docs/architecture/production-roadmap.md`](../docs/architecture/production-roadmap.md)
and not yet close enough to cut: release and deprecation policy (item 3),
reliability and backpressure (5), security (6), deployment shape (7),
architecture fitness tests (9), production runbooks (10), multi-GPU scheduling
(12), AI-datacenter deployment (13), and GPU hardware considerations (15).

## What Could Reorder This

Open defects and drift recorded in
[`coordination/STATUS.md`](../coordination/STATUS.md) can pull an item forward.
The two that would: the heap corruption in the GPU-postprocess ensemble, which
blocks trusting any ensemble measurement, and the five backends still inheriting
the slow default raw-results path, which makes any latency baseline taken on
them misleading. Neither is platform work, but both change what a platform
baseline means.

## Opening A Packet

1. Create `specs/YYYY-MM-DD-milestone-name/`.
2. Write `requirements.md`: the goal, what is in scope, what is explicitly out
   of scope and why, the decisions taken, and the constraints inherited.
3. Write `validation.md` before implementing: automated checks, negative checks,
   manual checks, and the definition of done. If a check turns out to be the
   wrong evidence, change it there and say why -- do not adjust it to match what
   was built.
4. Write `plan.md`: task groups that are independently implementable,
   independently reviewable, and each end in an observable result.
5. Add the packet to **Now** above, and remove whatever it closed from **Next**.
6. Update the packet in the same branch as the change it describes.
