# KServe Ensemble Agreement Test

Validation status: Scaffold; metadata leg implemented, agreement leg pending the
runtime and adapter work

Version set: `kserve-encoded-image-v040` in `versions.yaml`:
[neuriplo-kserve-runtime](https://github.com/olibartfast/neuriplo-kserve-runtime)
v0.4.0, the first release with the pipeline model kind, with neuriplo-infer
v0.10.3. The encoded-image serving leg (V-7 of
`specs/2026-10-03-kserve-dynamic-dim-encoded-image`) is attested in
[`evidence-encoded-image-v040.yaml`](evidence-encoded-image-v040.yaml); the
agreement leg below is still pending.

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

## Preprocessing comparison and benchmark

Two runnable artifacts compare ensembles that differ only in where
preprocessing runs (same inference model on both sides, so preprocessing is the
only variable):

```bash
# Symmetric one-to-one detection matching, JSON report
integration-tests/kserve-ensemble/compare_preprocessing.py \
  --reference-model yolo26seg_cpu --candidate-model yolo26seg_dali \
  --frames 'frames/*.jpg' --stride 8 --limit 50 \
  --report integration-tests/kserve-ensemble/baselines/dali-vs-cpu.json

# Interleaved latency benchmark, JSON transport
integration-tests/kserve-ensemble/benchmark_preprocessing.py \
  --models yolo26seg_cpu yolo26seg_dali \
  --labels cpu-preprocess dali-gpu-preprocess \
  --frames 'frames/*.jpg' --iterations 30

# Same, over the HTTP binary tensor extension
integration-tests/kserve-ensemble/benchmark_binary_transport.py \
  --models yolo26seg_cpu yolo26seg_dali yolo26seg_gpu \
  --labels cpu-pre+cpu-post gpu-pre+cpu-post gpu-pre+gpu-post \
  --frames 'frames/*.jpg' --iterations 30
```

Prefer the binary one for anything comparing pipeline placement. Sending a
98 KB JPEG as a JSON number array costs more per request than the work being
measured, and it inflates every configuration by a different amount.

The comparison reports **both** directions. Recall alone (how many reference
detections the candidate found) hides the opposite failure: a path that invents
detections scores just as well as one that reproduces them. `--min-match-rate`
turns the check into a gate once a target is agreed.

Recorded baselines live in `baselines/`, each carrying full model provenance
(variant, input shape, engine sha256 prefix, builder version, GPU) -- a latency
number without them is not comparable. Measurements below use YOLO26m-seg
(medium) at 640x640 as a TensorRT FP16 engine on an RTX 3060 Laptop.

As of 2026-08-05, DALI GPU
preprocessing reaches 91.4% recall but only 86.7% precision against the CPU
path, with high-confidence misses in both directions, so it is not yet a
validated drop-in.

### Where the time actually went

The first round of measurements attributed the neuriplo-vs-tritonic latency gap
to host round-trips between pipeline steps, on the reasoning that GPU
postprocess compute was identical (same CUDA plugin, 2.58 vs 2.59 ms) while
preprocessing cost 7.66 ms against 0.03 ms. That reading also made GPU
preprocessing look like a net loss on its own, which was blamed on PCIe traffic.

It was mostly wrong. `TRTInfer` had never overridden
`get_infer_results_raw()`, so every TensorRT inference fell back to the base
implementation, which builds one 16-byte `std::variant` per output scalar and
then flattens it back to bytes -- about 42 MB of variant vector per frame for a
YOLO26m-seg engine, constructed and walked twice. That cost scales with tensor
element count, so it fell hardest on exactly the configurations moving the
largest tensors, which is why it read as a transfer cost.

Copying device-to-host straight into the destination byte buffer
([neuriplo#21](https://github.com/olibartfast/neuriplo/pull/21)) took GPU
pre+post from 70.9 ms to 26.8 ms in a same-session A/B, against tritonic's
27.04 ms for the same model and GPU, and made GPU preprocessing alone a clear
win rather than a loss. Detections were bit-identical across the change.

The lesson worth keeping: a per-stage decomposition attributed the gap to the
one mechanism nobody had measured directly (PCIe), and the real cause was
uninstrumented host work inside a stage. `baselines/preprocessing-latency.json`
carries both the old and new numbers so the correction stays visible.

**Known bug, pre-existing:** the GPU-postprocess ensemble can abort the server
with heap corruption. Repro, backtrace, and what has been ruled out are under
`known_bug` in `baselines/preprocessing-latency.json`. It reproduces on builds
from before the TensorRT change, so it is not a regression from it.

