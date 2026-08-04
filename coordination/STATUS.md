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
| Pipeline model kind | neuriplo-kserve-runtime | Merged to develop (284/281 tests, tasks on/off), incl. DALI chaining, GPU serving, scheduler/validation fixes |
| `decodeImage` from memory | neuriplo-tasks | Merged to develop; 28/28 tests |
| Conformance leg | neuriplo-kserve-client | Merged to develop; 48/48 tests. Live ensemble leg still to be run against a served ensemble |
| Encoded-image + envelope adapter | neuriplo-infer | Merged to develop with the v0.8.0 alignment; 52/52 tests |
| Cross-repo agreement test | neuriplo-platform | Metadata leg implemented and passing against a live ensemble; agreement leg still pending (needs machine-readable detections out of neuriplo-infer) |

DALI/TensorRT lane (2026-08-05): neuriplo gained a DALI backend
(`feat/dali-backend`) hosting serialized pipelines through the DALI C API, pure
C++ at inference time. The runtime serves it as a `dali` model chained ahead of
a TensorRT FP16 engine in an ensemble. Live parity vs the CPU-preprocess path
over the same engine, 50 frames: 91.4% of detections matched at IoU>=0.5, 96.2%
at confidence>=0.5, misses concentrated at the 0.30 threshold margin; ~8
high-confidence residual mismatches remain uninvestigated (suspected NMS
flips). Three runtime fixes landed en route: scheduler error propagation
(failures were redacted to "internal error"), dynamic-axis input validation in
NeuriploExecutor, and batch-dimension reconciliation between pipeline steps.

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
