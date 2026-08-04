# Ensemble Contract

Owner: `neuriplo-kserve-runtime`

Consumers: `neuriplo-kserve-client`, `neuriplo-infer`, `tritonic`, deployment
automation, integration tests

Status: Draft

## Purpose

Define the wire surface of a server-side ensemble: a model that accepts an
encoded image, runs preprocessing, inference, and optionally postprocessing on
the server, and returns either the inner model's raw tensors or a decoded result
envelope.

This contract is transcribed from
[tritonic](https://github.com/olibartfast/tritonic) v0.4.0, which serves
ensembles through NVIDIA Triton and DALI. Recording it here lets
[neuriplo-kserve-runtime](https://github.com/olibartfast/neuriplo-kserve-runtime)
and a Triton deployment be interchangeable behind the same client code. See
[ADR 0011](../docs/adr/0011-ensemble-pipeline-serving.md) for why the runtime
implements this natively rather than adopting Triton.

An ensemble is an ordinary KServe V2 model to its client. There is no ensemble
request type, no ensemble response type, and no separate endpoint. Everything
below is expressed in the metadata and inference surface that already exists.

## Model Metadata

An ensemble model reports:

```text
platform:         "ensemble"
max_batch_size:   1
inputs:           exactly one, named IMAGE, datatype UINT8, shape [-1]
outputs:          passthrough outputs, or one of the envelopes below
```

`platform: "ensemble"` is how a client tells an ensemble from a plain model.
`neuriplo-kserve-client` surfaces it as `ModelMetadata::platform`.

`max_batch_size: 1` is contractual, not incidental. Encoded images have no
common shape, so the runtime must not batch them. A server that dynamically
batches an ensemble is non-conforming.

## Input

```text
IMAGE   UINT8   [1, N]   raw encoded image bytes
```

`N` is the byte length of the encoded file. Only JPEG is in scope; a server may
accept more formats, but a client may not assume it.

The client is responsible for knowing the source image's pixel dimensions --
they are needed to map results back onto the original frame, and the server does
not return them. Reading them from the JPEG header is sufficient.

## Output: passthrough ensembles

A passthrough ensemble does server-side preprocessing only. Inference outputs
are forwarded unchanged, so the client postprocesses exactly as it does for a
directly served model.

The ensemble's outputs must equal the inner model's outputs -- same names, same
datatypes, same shapes, same order -- for the leading outputs the inner model
declares. An ensemble may append extra outputs after those.

This is what makes the inner "task model" necessary. The ensemble's own metadata
describes an encoded image, which tells a task layer nothing about tensor
layout. The client fetches the inner model's metadata separately, by name, and
uses it to build the task. The check that the two agree is what catches an
ensemble wired to the wrong inner model.

## Output: decoded envelopes

A postprocessing ensemble decodes results on the server and returns a fixed
tensor envelope. Detections are capped at 100.

Detection envelope, always present:

```text
NUM_DETECTIONS   INT32   [1]         number of valid detections, 0..100
BOXES            INT32   [100, 4]    x, y, width, height in source-image pixels
SCORES           FP32    [100]       confidence per detection
CLASSES          INT32   [100]       class id per detection
```

Only the first `NUM_DETECTIONS` rows of `BOXES`, `SCORES`, and `CLASSES` are
meaningful. The remainder is padding and must be ignored.

Instance segmentation adds one of two variants.

Packed masks:

```text
MASK_OFFSETS     INT64   [101]       prefix offsets into MASK_DATA
MASK_DATA        UINT8   [-1]        concatenated per-detection masks
```

`MASK_OFFSETS[0]` is 0 and `MASK_OFFSETS[i+1] - MASK_OFFSETS[i]` is the byte
length of detection `i`'s mask, which covers that detection's box. The array is
always 101 entries even when there are no detections -- a truncated
`MASK_OFFSETS` on a detection-free frame is the single most likely
implementation bug here, and it aborts video processing on the first empty
frame.

Polygons:

```text
INSTANCE_RING_OFFSETS   INT64   [101]      prefix offsets into RING_POINT_OFFSETS
RING_POINT_OFFSETS      INT64   [-1]       prefix offsets into POLYGON_POINTS
POLYGON_POINTS          INT32   [-1, 2]    x, y in source-image pixels
```

Two levels of prefix offsets: detection to its rings, ring to its points. Both
offset arrays start at 0 and increase monotonically. Every ring has at least
three points and non-zero area. A ring contained inside an earlier ring of the
same detection is a hole in it; all other rings are exteriors.

Shapes are written as the trailing dimensions. A server may declare leading
dimensions in front of them.

## Compatibility Rules

- Adding an output after the declared envelope outputs is backward compatible.
- Renaming an envelope tensor, changing its datatype, or changing its trailing
  shape is breaking.
- Changing the 100-detection cap is breaking; it is baked into the `[100, ...]`
  and `[101]` shapes.
- Changing the meaning of the offset arrays, including whether they start at 0,
  is breaking.
- Accepting an additional encoded format is backward compatible. Dropping JPEG
  is breaking.
- Adding a new envelope variant for a new task family is backward compatible
  when existing variants are untouched.
- Serving an ensemble with `max_batch_size` above 1 is breaking, whatever the
  server's batching implementation does.

## Validation Strategy

- `neuriplo-kserve-runtime` owns unit tests for envelope construction: the
  detection cap, the empty-detection case for both segmentation variants, and
  graph validation.
- `neuriplo-kserve-client` covers the transport level in its conformance oracle:
  ensemble metadata, a variable-length `UINT8` input, and the four envelope
  datatypes over both HTTP and gRPC.
- `neuriplo-infer` owns the envelope decoder and its failure cases, including
  metadata that disagrees with the inner task model.
- This repository owns the cross-repository check in
  `integration-tests/kserve-ensemble/`: the ensemble path and the
  client-preprocessed path must agree on detections for the same image. That
  agreement check is what caught tritonic's detection ranking, output cap, and
  channel stride defects, and it is the only test that can catch them.
