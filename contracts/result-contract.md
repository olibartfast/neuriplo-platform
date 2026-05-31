# Result Contract

Owner: `vision-core`

Consumers: `vision-inference`, `neuriplo-kserve-runtime`, downstream clients

Status: Draft

## Purpose

Define typed inference outputs that remain stable across local and serving
contexts.

## Responsibilities

`vision-core` owns:

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

## Validation Strategy

- Golden output fixtures should verify serialized result shape.
- Visualization tests should consume typed result objects, not backend tensors.
- Serving tests should validate that wire output preserves result semantics.
