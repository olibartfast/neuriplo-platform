# ADR 0012: Adopt browser-based neuriplo-ui as the operator application layer

Date: 2026-08-24

Status: Accepted

## Problem

ADR 0005 proposed a dedicated `neuriplo-ui` repository implemented with Qt and
native in-process inference transports. The repository boundary was sound, but
the proposed implementation did not match the product that entered the
ecosystem. [`neuriplo-ui`](https://github.com/olibartfast/neuriplo-ui) is now a
browser application with a local API adapter and must be represented accurately
in platform ownership, dependencies, contracts, and compatibility metadata.

The browser also needs one authoritative way to discover which tasks, models,
sources, parameters, and execution topologies a particular `neuriplo-infer`
binary supports. Duplicating those lists in TypeScript would drift from the
compiled runtime.

## Constraints

- A browser cannot launch native processes or access arbitrary local paths.
- `neuriplo-infer` remains the application composition root and the authority
  for inference behavior.
- The UI must support a local workflow and a client-server workflow without
  treating KServe as a local backend.
- The UI repository must not link the C++ backend, task, video, or KServe client
  libraries directly.
- Headless inference and serving repositories must not gain browser or Node.js
  dependencies.
- The first implemented cross-repository boundary is capability discovery; run
  execution and result rendering remain later UI roadmap phases.

## Options

1. Continue with the Qt multi-platform plan from ADR 0005.
2. Add browser presentation and HTTP routes directly to `neuriplo-infer`.
3. Keep a standalone browser repository with a thin local process adapter that
   invokes `neuriplo-infer` through versioned machine-readable contracts.

## Decision

Choose option 3.

`neuriplo-ui` is the operator application layer. It owns:

- the React and TypeScript browser application;
- the Node.js and Fastify local API adapter;
- browser-oriented configuration and result presentation; and
- Playwright end-to-end coverage.

The process boundary is:

```text
browser -> neuriplo-ui local adapter -> neuriplo-infer
```

The adapter invokes binaries with an argument array, never a shell-composed
command. Capability discovery uses `neuriplo-infer --capabilities`; schema
version 1 is owned and emitted by `neuriplo-infer` and validated by the adapter.
The full contract is recorded in
[`capabilities-contract.md`](../../contracts/capabilities-contract.md).

Execution topology is modeled before backend selection:

```text
local
  -> choose one compiled local backend
  -> provide local model artifacts

client_server
  -> choose an advertised protocol and transport
  -> configure the endpoint and remote model metadata
```

KServe V2 over HTTP or gRPC is currently the client-server protocol exposed by
`neuriplo-infer`; it is not a local backend. The browser receives this topology
from the binary rather than maintaining a second registry.

`neuriplo-ui` currently integrates normal work through `master`. It is not
added to the C++ sibling Gitflow group unless the owning repository later adopts
`develop` and release-only `master` branches explicitly.

## Consequences

Positive:

- The UI has an independent web release cadence and no C++ or Qt toolchain.
- The browser stays isolated from native process and filesystem privileges.
- One build-specific capability payload covers local-only, client-server-only,
  and combined binaries.
- Adding tasks, models, backends, protocols, or transports does not require a
  hard-coded UI registry update when the schema remains compatible.

Negative:

- Local browser use requires the Node.js adapter to be running.
- The adapter and `neuriplo-infer` must coordinate schema-version changes.
- The WIP UI adds another repository pin, validation surface, and ownership
  record to the platform control plane.

Follow-up:

- Add run-request and structured-result contracts when UI roadmap Phase 2
  lands.
- Add capability-driven browser controls in the UI roadmap Phase 3.
- Add a platform integration scenario once the browser can execute a real run.
- Revisit branch policy before the first `neuriplo-ui` release.
