# KServe Ensemble Agreement Test

Validation status: Scaffold; metadata leg implemented, agreement leg pending the
runtime and adapter work

Version set: unpinned. Adds to a compatibility set once
[neuriplo-kserve-runtime](https://github.com/olibartfast/neuriplo-kserve-runtime)
tags a release containing the pipeline model kind.

Owning repos:

- `neuriplo-platform`: this cross-repository check and the ensemble contract.
- [neuriplo-kserve-runtime](https://github.com/olibartfast/neuriplo-kserve-runtime): serves the ensemble.
- [neuriplo-kserve-client](https://github.com/olibartfast/neuriplo-kserve-client): protocol transport.
- [neuriplo-infer](https://github.com/olibartfast/neuriplo-infer): both client paths under comparison.
- [neuriplo-tasks](https://github.com/olibartfast/neuriplo-tasks): the preprocessing and postprocessing being relocated.

## Purpose

An ensemble moves preprocessing, and optionally postprocessing, from the client
to the server. The whole claim is that this does not change the answer. This
test is where that claim is checked, because it is the only place that runs both
paths against the same image with the same model.

It checks agreement rather than a golden output on purpose. The defects this
feature class produces are self-consistent: detections ranked before instead of
after the score sort, an output cap applied in the wrong order, a channel stride
hardcoded to one anchor count, a truncated offset array on a detection-free
frame. Every one of those reproduces stably into a golden file and every one
fails an agreement check against the client-preprocessed path. All four were
real defects in [tritonic](https://github.com/olibartfast/tritonic) v0.4.0,
found exactly this way.

## Contract Under Test

[`contracts/ensemble-contract.md`](../../contracts/ensemble-contract.md), and
[ADR 0011](../../docs/adr/0011-ensemble-pipeline-serving.md) for why the runtime
implements ensembles natively rather than through Triton.

## Usage

From `neuriplo-platform`:

```bash
integration-tests/kserve-ensemble/run.py
```

Against a specific deployment:

```bash
integration-tests/kserve-ensemble/run.py \
  --endpoint http://127.0.0.1:8080 \
  --ensemble-model yolo_ensemble \
  --task-model yolo
```

## What It Checks

Implemented:

- the ensemble reports `platform: ensemble`
- it exposes exactly one `IMAGE` / `UINT8` input
- when it declares a decoded envelope, every envelope tensor has the datatype
  the contract requires

Pending, with the neuriplo-infer adapter:

- the same JPEG through the ensemble path and through the client-preprocessed
  path yields the same detections within tolerance
- a detection-free frame returns a well-formed envelope on both segmentation
  variants rather than a truncated offset array

## Current Limitations

- No endpoint reachable means the test reports "skipped" and exits 0, so it can
  sit in CI before the runtime feature exists. It never reports agreement it did
  not observe.
- Requires a running server and a loaded model repository; it neither builds
  binaries nor downloads models.
