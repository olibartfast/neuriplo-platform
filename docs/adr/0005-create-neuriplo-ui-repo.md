# ADR 0005: Create a dedicated neuriplo-ui repository for the Qt UI

Date: 2026-06-08

Status: Proposed

## Problem

`neuriplo-infer` is the local application layer and today exposes inference
through a CLI runner. Some use cases (model selection, live video preview from
`videocapture`, and inspecting detection/segmentation results visually) are
awkward to drive from a CLI. We want a graphical Qt UI that targets Linux
desktop, Windows desktop, Android, and a browser web app, without violating the
ecosystem layering or turning `neuriplo-platform` into a runtime repository.

## Constraints

- `neuriplo-platform` must not contain UI, runtime, or backend execution code.
  It owns ADRs, ownership, contracts, examples, and the version matrix only.
- The UI is application-layer presentation; it belongs in an app-layer repo.
- The UI must depend downward only: onto `neuriplo` (backend abstraction) and
  `videocapture` (frame source) for native targets, and onto the serving
  contract for remote targets. It must not reach into backend execution or
  serving-internal (`neuriplo-kserve-runtime`) implementation code.
- Qt is a heavyweight build dependency (Qt/CMake/widgets) plus three extra
  toolchains (Windows, Qt for Android, Qt for WebAssembly). This must not leak
  into `neuriplo-infer`'s headless or container inference paths.
- The UI must target four platforms that do not share an inference deployment
  model (see matrix below).

## Platform / inference-deployment matrix

The decisive constraint is that not every target can embed native inference:

- Linux and Windows desktop: can run inference in-process through `neuriplo`
  native backends, or call a remote serving endpoint.
- Android: Qt builds for ARM, but native `neuriplo` backends must also exist as
  ARM builds; otherwise Android must use the remote-serving path.
- Web app (Qt for WebAssembly): runs in the browser sandbox and **cannot** load
  native backends, GPU drivers, or local model files. It must drive inference
  through a remote serving endpoint (`neuriplo-kserve-runtime`) over the network.

This forces a clean split between the inference *transport* (in-process native
vs. remote serving client) and the Qt presentation layer, selected per target.

## Options

1. Add the Qt UI as a second front-end inside `neuriplo-infer`, sharing the
   Composition Root and inference pipeline with the CLI.
2. Create a separate `neuriplo-ui` app-layer repository with its own release
   cadence and multi-platform toolchains.
3. Embed UI concerns in `neuriplo` or `videocapture` (rejected: violates the
   abstraction/source layer boundaries).

## Decision

Create a new `neuriplo-ui` repository as a sibling app-layer component. It owns
the Qt presentation layer and the four-target build toolchains (Linux, Windows,
Qt for Android, Qt for WebAssembly), and keeps Qt and its toolchains out of
`neuriplo-infer` entirely.

`neuriplo-ui` drives inference through an inference *transport* abstraction with
two implementations:

- a native in-process transport that consumes the `neuriplo` backend abstraction
  and `videocapture` frame source (desktop, and Android where ARM backends
  exist), and
- a remote serving client that targets the serving contract (mandatory for the
  web app, optional elsewhere).

The same Qt presentation layer binds to either transport. The web target always
uses the remote-serving transport.

Ownership and reuse:

- `neuriplo-ui` is added to the ownership model as the UI / multi-platform app
  layer and gets its own row in the version matrix.
- Shared inference wiring that is genuinely front-end agnostic stays in
  `neuriplo-infer` or `neuriplo`; `neuriplo-ui` reuses it rather than copying it,
  consistent with ADR 0003 (runners stay in owning repos).

Sequencing (avoid paying separation costs before they earn their keep):

- The separate repo is the committed *destination*, but it is created when the
  first non-desktop target (web or Android) is committed; that is the point
  where separation stops being theoretical and the remote-serving transport
  becomes the natural seam.
- Until then, prototype the Linux desktop GUI inside `neuriplo-infer` behind an
  opt-in build flag. This validates the UI without an empty repo, a new CI
  surface, a version-matrix pin, or up-front library extraction from
  `neuriplo`/`neuriplo-infer`.
- The deciding signal: if the web app is a real near-term commitment, create
  `neuriplo-ui` now; if it is aspirational, record this decision, prototype in
  `neuriplo-infer`, and extract on the first web/Android work.

## Consequences

Positive:

- Qt, the Android/WebAssembly toolchains, and UI release cadence are fully
  isolated from `neuriplo-infer`; headless and container inference stay lean.
- The UI can evolve its own lifecycle (live preview, model picker, result
  overlays, multi-platform packaging) without destabilizing the CLI app.
- Layering stays intact: native targets depend down onto `neuriplo` and
  `videocapture`; remote targets depend only on the serving contract.

Negative:

- A new repository adds cross-repo coordination: another version-matrix entry,
  another CI surface, and another compatibility pin to maintain here.
- The native transport must reuse `neuriplo`/`neuriplo-infer` building blocks
  without copying them; this requires those pieces to be consumable as a library,
  which may need refactoring in the owning repo.
- The web target hard-depends on `neuriplo-kserve-runtime`, which is still WIP;
  the web app cannot ship before a stable remote serving contract exists.

Follow-up:

- Create the `neuriplo-ui` repository and record its purpose and boundaries.
- Define the inference transport interface and a remote serving client; ship the
  Linux desktop + native transport target first.
- Confirm `neuriplo`/`neuriplo-infer` expose the inference building blocks
  `neuriplo-ui` needs as a consumable library; refactor in the owning repo if not.
- Confirm ARM `neuriplo` backend builds before committing to native Android
  inference; otherwise scope Android to the remote-serving path.
- Update `docs/architecture/ownership.md` to add `neuriplo-ui` as the UI /
  multi-platform app layer.
- Add `neuriplo-ui` to `versions.yaml` and the README ownership table.
- Add a UI scenario under `examples/` and integration coverage here once the
  minimal UI exists.
