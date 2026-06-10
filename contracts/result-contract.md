# Result Contract

Owner: `neuriplo-tasks`

Consumers: `neuriplo-infer`, `neuriplo-kserve-runtime`, downstream clients

Status: Draft

## Purpose

Define typed inference outputs that remain stable across local and serving
contexts.

## Responsibilities

`neuriplo-tasks` owns:

- Result type definitions.
- Field semantics.
- Coordinate systems and units.
- Confidence score semantics.
- Serialization expectations where applicable.

Consumers may:

- Render results.
- Serialize public result fields.
- Filter, sort, or transform results for presentation.

Consumers must not:

- Infer semantics from positional tuple ordering when named fields exist.
- Change coordinate systems without making that transformation explicit.
- Treat backend raw outputs as public results.

## Compatibility Rules

- Adding optional result fields is backward compatible.
- Removing fields is breaking.
- Changing coordinate systems is breaking.
- Changing score semantics is breaking.
- Adding a new result type is backward compatible when existing types remain
  stable.

## Serialized Detection Results (Draft)

Status: Draft. No producer ships this yet; field semantics mirror the typed
results owned by `neuriplo-tasks` (`Detection`, `OpenVocabDetection`).

External consumers (agentic frameworks per ADR 0007, scripts, services) need
a machine-readable result form. The serialized shape mirrors the typed
result fields exactly; no consumer-side postprocessing is implied.

Object detection:

```json
{
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
```

Open-vocabulary detection:

```json
{
  "task": "open_vocab_detection",
  "model": "owlv2",
  "image": {"width": 1920, "height": 1080},
  "detections": [
    {
      "label": "red forklift",
      "prompt_index": 0,
      "score": 0.41,
      "bbox": {"x": 640, "y": 220, "width": 180, "height": 260}
    }
  ]
}
```

Semantics:

- `bbox` is in pixels in the original input image space, top-left origin,
  matching `BoundingBox{x, y, width, height}`.
- `class_confidence` and `score` keep the semantics of the typed results.
- `label` is resolved from the model's label set or runtime prompts;
  consumers must not re-derive it from `class_id`.

Expected producers (follow-up work in owning repos):

- `neuriplo-infer`: a machine-readable result output mode alongside
  visualization.
- `neuriplo-kserve-runtime`: an optional task-aware response mode, as
  already done for generative text output.

## Validation Strategy

- Golden output fixtures should verify serialized result shape.
- Visualization tests should consume typed result objects, not backend tensors.
- Serving tests should validate that wire output preserves result semantics.
- Serialized detection fixtures should round-trip against the typed results
  once a producer exists.
