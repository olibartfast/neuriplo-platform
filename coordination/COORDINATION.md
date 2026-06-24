# Agent coordination protocol

Message bus for the agents working across the neuriplo ensemble.
**Brand-agnostic**: roles are assigned by the human; any agent brand
(Opencode, Cursor, Kilocode, Hermes, Claude Code, OpenClaw, etc.)
can fill any role. An agent identifies itself by its assigned role,
not its brand.

Agent roles and their repos:

| Agent role | Primary repo(s) |
|---|---|
| neuriplo-agent | neuriplo |
| runtime-infer-agent | neuriplo-kserve-runtime, neuriplo-infer |
| client-agent | neuriplo-kserve-client |
| human | merges, releases, platform |

Ownership of record: `ops/CLUSTER_MAP.yaml`.

Replaces relaying messages through the human.

## Layout

```
coordination/
  COORDINATION.md   this protocol
  STATUS.md         shared board: lanes, in-flight PRs, blockers
  inbox/
    neuriplo.md      messages FOR the neuriplo agent
    runtime-infer.md messages FOR the runtime+infer agent
    client.md        messages FOR the client agent
    human.md         decisions/questions only the human can resolve
```

## Rules

1. **Read your inbox at session start and before ending a turn.**
2. **Write, don't relay.** Anything you would have asked the human to
   copy to another agent goes in that agent's inbox instead.
3. **Append-only for senders; recipients own their file.** Anyone may
   append a message to any inbox. Only the recipient checks messages off
   or prunes handled ones (keep the last few for context; history lives
   in git anyway).
4. **Update `STATUS.md`** whenever your lane's state changes (PR opened,
   merged, blocked, handed off).
5. **Sync etiquette:** `git pull --rebase` before pushing mailbox
   changes; commit only `coordination/` files in mailbox commits.
6. **Direct pushes to `main` are allowed for `coordination/` only.**
   This directory is a message bus, not a reviewed artifact. Everything
   else in this repo (contracts, versions, `.agents/`, `docs/`, scripts)
   still goes feature branch -> PR.
7. **The human is still the wake signal.** Idle agents don't see new
   mail; after writing to an inbox, expect delivery when the human nudges
   the recipient ("check your inbox") or the recipient next runs.

## Message format

Append to the recipient's inbox:

```markdown
## [ ] from:<sender-role> <YYYY-MM-DD> -- <subject>
<body: context, ask, links to PRs/commits. Be specific enough that the
recipient needs no other context to act.>
```

The recipient flips `[ ]` to `[x]` when handled (add a one-line
resolution note if the sender will care).

## Cross-repo ground rules

Canonical source: `.agents/rules/always-apply.md` and `AGENTS.md`.
Key rules restated for coordination context:

- GitFlow everywhere (coding repos): feature branch -> PR -> develop (or main).
- Wire-contract changes: runtime first, then client, then infer adapter.
- Releases, version pins, and PR merges are human-owned.
- Never work in another agent's checkout; use worktrees.
- Don't push to a branch whose CI is mid-run (concurrency cancellation).
