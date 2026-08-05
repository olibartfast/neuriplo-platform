# Ensemble status board

Last updated: 2026-08-05

## Lanes

| Agent role | Repo(s) | Current work | State |
|---|---|---|---|
| neuriplo-agent | neuriplo | Post-release: TensorRT metadata crash (top item), EngineOptions device-selection | Idle |
| runtime-infer-agent | neuriplo-kserve-runtime, neuriplo-infer | Ensemble/pipeline + DALI/TensorRT lane merged to develop in both repos | Done |
| client-agent | neuriplo-kserve-client | Ensemble conformance merged to develop | Done |
| human | merges, releases, platform | ADR 0011 + ensemble contract written; review the infer alignment branch | WIP |

## Ensemble serving lane (2026-08-04)

Sequencing is runtime -> client -> infer adapter, per the wire-contract rule.

| Step | Repo | State |
|---|---|---|
| Spec: ADR 0011 + `contracts/ensemble-contract.md` | neuriplo-platform | Written, unreviewed |
| Pipeline model kind | neuriplo-kserve-runtime | Merged to develop (286/281 tests, tasks on/off), incl. DALI chaining, GPU serving, scheduler/validation fixes |
| `decodeImage` from memory | neuriplo-tasks | Merged to develop; 28/28 tests |
| Conformance leg | neuriplo-kserve-client | Merged to develop; 48/48 tests. Live ensemble leg still to be run against a served ensemble |
| Encoded-image + envelope adapter | neuriplo-infer | Merged to develop with the v0.8.0 alignment; 52/52 tests, -DWERROR=ON and cppcheck clean |
| Cross-repo agreement test | neuriplo-platform | Metadata leg passing live. Server-to-server preprocessing comparison implemented (compare_preprocessing.py, symmetric, JSON output). A client-path agreement gate still needs machine-readable detections out of neuriplo-infer |

DALI/TensorRT lane (2026-08-05): neuriplo gained a DALI backend hosting
serialized pipelines through the DALI C API, pure C++ at inference time, with
the full docs/ADDING_BACKEND.md checklist closed (registry entry, tests, setup
script, validation, Readme). The runtime serves it as a `dali` model chained
ahead of a TensorRT FP16 engine.

Preprocessing-placement measurements are reproducible artifacts, not prose:
`integration-tests/kserve-ensemble/compare_preprocessing.py` and
`benchmark_preprocessing.py`, with results under `baselines/`.

Parity, 50 frames of 1280x720 video, YOLO26m-seg (medium) at 640x640 served
as a TensorRT FP16 engine -- the same engine on both sides -- with symmetric
one-to-one matching at IoU>=0.5:

| Direction | Rate |
|---|---|
| CPU detections found by DALI (recall) | 641/701 = 91.4% |
| DALI detections present in CPU (precision) | 641/739 = 86.7% |

19 unmatched CPU detections and 13 unmatched DALI detections are above
confidence 0.5. An earlier one-directional measurement reported only the 91.4%
figure; it hid the precision side, where DALI produces 38 more detections than
the reference. DALI preprocessing is NOT yet a validated drop-in.

Latency, YOLO26m-seg at 640x640, TensorRT FP16, HTTP binary tensor extension,
server-side pipeline median over 20 requests:

| Configuration | server | client | vs CPU |
|---|---|---|---|
| CPU pre + CPU post | 150.8 ms | 155.0 ms | 1.00x |
| DALI GPU pre + CPU post | 160.4 ms | 164.8 ms | 0.94x |
| DALI GPU pre + GPU post | 69.8 ms | 74.0 ms | 2.16x |

GPU preprocessing alone is a net LOSS: the preprocessed tensor round-trips to
host, costing more than the GPU decode saves. It pays only when postprocessing
is also on GPU, which collapses a 3.3 MB prototype tensor into a small
envelope. The win is as much about transfer volume as compute.

Transport matters enormously and earlier figures overstated everything: with
JSON `data` arrays the same three configurations measured 303.8 / 276.7 /
244.6 ms client-side. gRPC has NOT been measured -- this build has
NEURIPLO_RUNTIME_ENABLE_GRPC=OFF.

Per-stage against tritonic on the same model and GPU: DALI preprocess 7.66 ms
vs 0.03, TensorRT 29.48 vs 24.48, GPU postprocess 2.58 vs 2.59 -- the
postprocess compute is identical (same CUDA plugin). The whole gap is host
round-trips, because the DALI backend copies outputs device->host and the next
step re-uploads them. Device-side tensor handoff is the outstanding
optimization.

Runtime fixes landed en route: scheduler error propagation centralized on
SchedulerResult::adopt (failures were redacted to "internal error"),
dynamic-axis input validation, batch-dimension reconciliation restricted to
leading unit dimensions, and GPU serving via --use-gpu.

Validated end to end on 2026-08-04: a 404-frame 1280x720 video through
neuriplo-infer -> neuriplo-kserve-client -> neuriplo-kserve-runtime, serving a
YOLO26-seg ONNX model behind an ensemble that preprocesses, infers, and
postprocesses server-side, returning the packed-mask envelope. GPU inference via
the ONNX Runtime CUDA provider: ~160 ms per request, against ~1650 ms on CPU.

All coding-repo work is merged to local develop (2026-08-05): neuriplo-tasks,
neuriplo (new DALI backend), neuriplo-kserve-client, neuriplo-kserve-runtime,
and neuriplo-infer. Releases, tags, and version-matrix pins remain human-owned;
versions.yaml compatibility sets get entries once the siblings tag.

## Recently landed

- **Release wave 2026-06-12**: neuriplo v0.6.0 (multi-backend builds, plugin
  C ABI, raw-output API), runtime v0.1.0 (first release), client v0.3.0,
  infer v0.6.0 (pins -> neuriplo v0.6.0 + client v0.3.0, validated). All
  release PRs merged, tags pushed, master back-merged into develop.

## Known issues / debt

- neuriplo TensorRT metadata test disabled due to crash
  (`backends/tensorrt/test/TensorRTInferTest.cpp:119`) -- top roadmap item.
- Uncommitted agent WIP in neuriplo tree (ROADMAP + CI docs paths-ignore)
  and runtime tree (feature/step-13-2-infer-data-plane). Owners should
  commit or drop.
- Runtime CI checks out neuriplo@develop; consider pinning the v0.6.0 tag
  on release branches.
