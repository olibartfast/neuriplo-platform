# ADR 0008: Publish result events from neuriplo-infer, renderer as first consumer

Date: 2026-06-10

Status: Proposed

## Problem

`neuriplo-infer` produces typed inference results but can only deliver them
in-process: visualization overlays and local output formatting. Consumers that
live outside the inference process have no way to receive results as they are
produced:

- a renderer that draws results over video in a separate process or machine,
- agentic consumers such as `ghostgrid` reacting to detections (ADR 0007),
- recorders, alerting, dashboards, and other observers.

The immediate motivation is a renderer module that listens for published task
events and renders according to task purpose (detection boxes, segmentation
masks, pose skeletons, generative captions). But coupling the design to
rendering would repeat the mistake the result contract avoids: the durable
piece is the event publishing path, and the renderer is only its first
consumer. `neuriplo-infer` must be able to publish with no renderer attached,
and renderers must be able to attach and detach without touching inference.

## Constraints

- `neuriplo-infer` owns local application flow, visualization, and output
  formatting; publishing results is an output mode and belongs there.
- The serialized result shape is owned by the result contract
  (`contracts/result-contract.md`); the event path must carry it, not invent
  a second result encoding.
- Publishing must never block or slow inference: a slow or absent broker must
  cost at most a bounded queue and dropped events, never frame latency.
- Rendering needs pixels, but the event bus must not become a media bus by
  default; frame transport and result transport are separate planes.
- Candidate brokers differ widely (MQTT, RabbitMQ, Kafka, WebSocket); the
  ecosystem must not hard-couple to one wire protocol, but also must not pay
  for five adapters before a second consumer exists.
- Event consumers are downstream clients under the result contract rules:
  render, serialize, filter, transform, but never decode backend raw tensors
  or re-implement task pre/postprocessing (same boundary as ADR 0007).
- `neuriplo-platform` must not contain runtime code; it owns the envelope
  contract, ownership rules, and examples only.

## Options

1. Build the renderer as a direct in-process module of `neuriplo-infer`
   (rejected: already exists as visualization; does not serve out-of-process
   or remote consumers, and couples rendering cadence to inference cadence).
2. Define a result event contract; `neuriplo-infer` gains a fire-and-forget
   publisher sink behind a broker-agnostic interface; the renderer is an
   independent subscriber that correlates events with media it accesses
   itself.
3. Publish full frames with every event so consumers need no media access
   (rejected as default: turns the metadata plane into a media plane,
   inflates broker traffic, and ties event size to resolution; allowed only
   as an explicit opt-in thumbnail/crop attachment).

## Decision

Option 2. Two separable pieces:

```text
publisher:  neuriplo-infer result sinks (Strategy; N sinks active at once)
            |- visualization sink (existing overlay)
            |- machine-readable output sink (result contract follow-up)
            '- event publisher sink -> broker adapter (MQTT first)
                 bounded queue, drop-oldest, fire-and-forget

consumers:  renderer        -> subscribes, dispatches on task, draws
            ghostgrid       -> subscribes per ADR 0007 boundary rules
            future observers (recorders, alerting, dashboards)
```

Envelope and payload:

- A new event contract (`contracts/event-contract.md`) defines the envelope:
  schema version, source id, frame correlation (frame id plus capture and
  inference timestamps), task type, and the serialized result-contract
  payload.
- Media and metadata travel on separate planes. Consumers that draw on video
  obtain frames themselves (for example through `videocapture` on the same
  source) and correlate by `source_id` + `frame.id`, holding a small jitter
  buffer. An optional embedded thumbnail/crop is an explicit opt-in for
  consumers without media access.

Broker strategy:

- The publisher is written against a broker-agnostic publisher interface
  (Adapter per broker, mirroring the backend adapter pattern in `neuriplo`).
- Ship MQTT first: edge-vision default, small client dependency, QoS 0
  matches lossy latest-value rendering semantics. WebSocket is the expected
  second adapter if the first renderer is browser-based (and aligns with the
  ADR 0005 web target). Kafka/RabbitMQ are deferred until a consumer needs
  durable replay.
- Delivery semantics are at-most-once by default; rendering is a lossy
  latest-value consumer. Consumers needing stronger guarantees motivate a
  different adapter, not a change to the default.

Renderer placement:

- The renderer dispatches on the envelope `task` field through a renderer
  registry (detection boxes, segmentation masks, pose skeletons, generative
  captions), mirroring the task registry shape in `neuriplo-tasks`.
- Per the ADR 0005 sequencing rule, the renderer is prototyped where it is
  cheapest, inside `neuriplo-infer` behind an opt-in flag, consuming the
  event contract only. An event-subscriber transport is a natural third
  transport for `neuriplo-ui` (alongside native in-process and remote
  serving); a dedicated `neuriplo-renderer` repo is created only when a
  second consumer or second platform forces the seam.

Boundary rules for event consumers (all consumers, not just the renderer):

- Consume the envelope and the serialized result contract only; never decode
  backend raw tensors or re-implement task pre/postprocessing.
- Treat events as observations: a consumer must not require acknowledgement
  or feed back into the inference loop through the event bus.
- Out-of-ecosystem subscribers are secondary consumers: best-effort, no
  `versions.yaml` entry, protected only by envelope and result contract
  compatibility rules (same status as ADR 0007).

## Consequences

Positive:

- Inference and rendering are fully decoupled: `neuriplo-infer` publishes
  with or without consumers, and renderers attach without touching inference.
- The serialized result contract gains its first real producer and consumer,
  turning the draft into a validated shape.
- One envelope serves every observer (renderer, ghostgrid, recorders,
  dashboards); consumer boundary rules are written once.
- The fire-and-forget sink isolates inference latency from broker health.

Negative:

- Frame correlation moves complexity into consumers: renderers need media
  access, a jitter buffer, and correlation logic instead of receiving pixels.
- A new contract surface must be kept compatible alongside the result
  contract, and envelope versioning starts at day one.
- Segmentation results cannot ride the event path until the serialized
  result contract defines a mask encoding (RLE or polygons); the first
  iteration is effectively detection-only.
- MQTT-first means consumers wanting replay or durable history wait for a
  Kafka/RabbitMQ adapter.

Follow-up:

- Add `contracts/event-contract.md` defining envelope, topic layout,
  compatibility rules, and validation strategy.
- In `neuriplo-infer`: introduce the result sink abstraction, the bounded
  drop-oldest publisher, and the MQTT adapter; keep visualization as a sink.
- In `neuriplo-tasks` / result contract: define serialized encodings for
  segmentation masks and pose keypoints before those tasks publish.
- Prototype the subscriber renderer behind an opt-in flag in
  `neuriplo-infer`; record the extraction trigger (second consumer or second
  platform) before creating any new repo.
- Add an event-driven scenario under `examples/` once publisher and a
  minimal subscriber exist.
