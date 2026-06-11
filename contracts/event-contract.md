# Event Contract

Owner: `neuriplo-platform` (envelope), `neuriplo-tasks` (result payload
semantics via the result contract)

Producer: `neuriplo-infer` (event publisher sink, see ADR 0008)

Consumers: renderer (first consumer),
[`ghostgrid`](https://github.com/olibartfast/ghostgrid) (ADR 0007), recorders,
alerting, dashboards, other observers

Status: Draft

## Purpose

Define the envelope in which serialized inference results are published to a
message broker, so that out-of-process consumers can observe results without
coupling to the inference process. The envelope carries the serialized result
contract payload; it does not define result semantics.

## Schema

Envelope:

```json
{
  "schema_version": "1",
  "source_id": "cam-front-01",
  "frame": {
    "id": 18412,
    "ts_capture": "2026-06-10T14:03:22.481Z",
    "ts_inference": "2026-06-10T14:03:22.512Z"
  },
  "task": "object_detection",
  "result": {
    "task": "object_detection",
    "model": "yolov8n",
    "image": {"width": 1920, "height": 1080},
    "detections": [
      {
        "class_id": 0,
        "label": "person",
        "class_confidence": 0.93,
        "bbox": {"x": 100, "y": 50, "width": 220, "height": 410}
      }
    ]
  }
}
```

Field semantics:

- `schema_version`: envelope version, independent of result-contract
  versioning. Consumers must ignore unknown envelope fields.
- `source_id`: stable identifier of the input source (camera, file, stream)
  configured in the producer. Consumers must treat it as opaque.
- `frame.id`: monotonically increasing per `source_id` within a producer run.
  Used with `source_id` for media correlation; not globally unique and not
  durable across producer restarts.
- `frame.ts_capture` / `frame.ts_inference`: UTC wall-clock timestamps for
  frame capture and result production. Consumers use `ts_capture` for media
  correlation and the difference for staleness decisions.
- `task`: task type discriminator, duplicated from the result payload so
  consumers can dispatch without parsing `result`.
- `result`: a serialized result-contract payload, verbatim. Its shape and
  compatibility rules are owned by `contracts/result-contract.md`.

Optional media attachment (opt-in, off by default):

- `frame.thumbnail`: base64 JPEG of the input frame or a crop, for consumers
  without media access. Producers must keep the event path metadata-only by
  default; the event bus is not a media bus.

## Topic Layout

```text
neuriplo/{source_id}/{task}
```

- Renderers subscribe per source: `neuriplo/cam-front-01/+`.
- Task-oriented consumers subscribe per task: `neuriplo/+/object_detection`.
- Topic names are part of this contract; renaming segments is breaking.

## Delivery Semantics

- At-most-once by default (MQTT QoS 0). Events are observations of a live
  stream; rendering and monitoring are lossy latest-value consumers.
- Producers publish fire-and-forget behind a bounded drop-oldest queue and
  must never block inference on broker health.
- Consumers must tolerate gaps, reordering within the jitter window, and
  duplicate `frame.id` after producer restarts.
- Consumers must not acknowledge events into the inference loop; the event
  plane is one-way.

## Frame Correlation

Media and metadata travel on separate planes. A consumer that draws on video:

- obtains frames itself (for example through `videocapture` on the same
  source),
- correlates by `source_id` + `frame.id` when it shares the producer's frame
  numbering, or by `ts_capture` otherwise,
- holds a small jitter buffer and drops events older than its staleness
  threshold.

## Compatibility Rules

- Adding optional envelope fields is backward compatible.
- Removing or renaming envelope fields is breaking.
- Changing `frame.id` or timestamp semantics is breaking.
- Changing the topic layout is breaking.
- Result payload compatibility is governed by the result contract; an
  envelope `schema_version` bump is not required for compatible result
  changes.

## Validation Strategy

- Golden envelope fixtures verify the serialized envelope shape.
- Round-trip tests confirm the `result` payload is carried verbatim against
  result-contract fixtures.
- A publisher/subscriber smoke test (local broker) validates topic layout,
  drop-oldest behavior under a stalled consumer, and that inference latency
  is unaffected with the broker down.
