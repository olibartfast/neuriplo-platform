# Mission

Living document. Update it when the platform's purpose or boundaries change,
not when a milestone lands. Milestone history belongs in the dated packets
alongside this file.

Last updated: 2026-08-24

## Why This Repository Exists

Neuriplo is a GPU-first AI inference serving ecosystem split across seven
implementation repositories. The split is deliberate: task semantics, backend
execution, application wiring, operator interface, protocol client, serving
runtime, and video I/O each evolve at their own pace and are each useful on
their own.

The cost of that split is that no single repository can answer the questions
that matter most in production:

- Does this combination of versions actually work together?
- Who owns the interface that just changed, and who breaks when it does?
- Was that decision made, or merely assumed?
- Is the measured behavior better or worse than the last time anyone looked?

[`neuriplo-platform`](https://github.com/olibartfast/neuriplo-platform) exists to
answer those four questions and nothing else. It is the architecture control
plane: it holds the decisions, the cross-repository interfaces, the pinned
compatibility sets, and the evidence that closes them. It holds no runtime code,
and it never will.

## Who It Serves

| Audience | What they come here for |
|---|---|
| Platform maintainer (human) | Merge, release, and pin decisions; the compatibility matrix; the evidence attached to it |
| Implementing agents scoped to one sibling repo | The contract they must not break, the change classes they may use, the branch policy they work under |
| Integrators outside the ecosystem | What protocol is spoken, what a compatibility set guarantees, which serving shapes are supported |
| Reviewers of a cross-repo change | One packet per unit of work: what was asked, how it was cut up, what evidence closed it |

## What The Platform Owns

- Architecture decisions, one per [ADR](../docs/adr/README.md).
- Cross-repository interfaces, one per [contract](../contracts/README.md).
- The [version matrix](../versions.yaml): named compatibility sets over pinned
  refs, with their evidence and benchmark baselines.
- Ownership and dependency topology
  ([`ops/CLUSTER_MAP.yaml`](../ops/CLUSTER_MAP.yaml),
  [`ops/policies.yaml`](../ops/policies.yaml)).
- Hermetic integration checks and scenario evidence
  ([`integration-tests/`](../integration-tests/README.md)).
- Milestone packets: this directory.

## What The Platform Does Not Own

- Runtime, backend, model, or serving implementation. That stays in the owning
  repository, per [ADR 0003](../docs/adr/0003-keep-runners-in-owning-repos.md).
- Executable end-to-end runners. The platform describes and dry-runs them; the
  owning repo runs them.
- Release mechanics inside sibling repositories. It records the pins, it does
  not cut the tags.
- Model artifacts, generated outputs, or anything GPU-dependent in CI.

## Operating Principles

1. **One home per kind of thing.** An ADR records a decision, a contract records
   an interface, a spec packet records one unit of work. A fact restated in two
   places will drift; link instead.
2. **Evidence, not assertion.** `validation.md` is written before the work, so
   the bar is set by the specifier rather than by whatever turned out to be
   easy. Measured numbers live in artifacts under
   [`integration-tests/`](../integration-tests/README.md); prose links to them
   rather than repeating them.
3. **Nothing declared may be inert.** A threshold, contract field, or validator
   this repository names must have something that reads it. If it cannot be
   enforced yet, it is recorded as out of scope in a packet, not left declared
   and unenforced.
4. **Compatibility is a claim about pinned refs**, never about `latest`. A
   compatibility set without evidence is a draft, and says so.
5. **The control plane stays hermetic.** The gate must run on a machine with no
   GPU, no sibling checkouts, and no reachable serving endpoint. Checks that
   need any of those are opt-in and are not the gate.
6. **Implementation lands in the owning repository.** A platform change that can
   only be validated by editing a sibling repo has been scoped wrong.

## What Success Looks Like

- One command decides whether a change to this repository passes, and CI runs
  exactly that command.
- Every compatibility set in [`versions.yaml`](../versions.yaml) resolves to
  evidence and to benchmark baselines that a gate compares against.
- Every cross-repo interface in [`contracts/`](../contracts/README.md) declares
  its owner, consumers, version, and lifecycle status, and a validator enforces
  it.
- A reader arriving at any milestone packet can tell what was asked, what was
  built, and what proved it, without prior context.
- A regression in latency, throughput, or accuracy fails a check rather than
  being discovered in prose months later.

## Non-Goals

- **Becoming a monorepo.** The repository boundaries are the product of
  [ADR 0001](../docs/adr/0001-use-platform-as-architecture-control-plane.md) and
  [ADR 0002](../docs/adr/0002-centralize-cross-repo-control-plane.md); the
  control plane exists to make the split affordable, not to undo it.
- **Competing with vLLM or upstream KServe on LLM serving.** Generative
  workloads are served over OpenAI-compatible endpoints per
  [ADR 0006](../docs/adr/0006-generative-serving-over-openai-protocol.md); the
  serving differentiation stays on the predictive track.
- **Governing what has no cross-repo consequence.** A rule that only affects one
  repository belongs in that repository.
