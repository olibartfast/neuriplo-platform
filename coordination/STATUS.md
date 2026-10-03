# Ensemble status board

Last updated: 2026-10-03

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

Latency, YOLO26m-seg at 640x640, TensorRT FP16, HTTP binary tensor extension.
Same machine, same frames, one session, A/B against a binary built from the
parent commit:

| Configuration | server before | server after | client after | vs CPU |
|---|---|---|---|---|
| CPU pre + CPU post | 150.8 ms | 121.5 ms | 123.5 ms | 1.00x |
| DALI GPU pre + CPU post | 160.4 ms | 76.8 ms | 78.7 ms | 1.58x |
| DALI GPU pre + GPU post | 69.8 ms | 23.9 ms | 26.8 ms | 5.08x |

The "after" column is neuriplo PR #21. `TRTInfer` had never overridden
`get_infer_results_raw()`, so every TensorRT inference fell back to the base
implementation, which builds one 16-byte `std::variant` per output scalar and
flattens it back to bytes -- ~42 MB of variant vector per frame for this
engine, built and walked twice. Copying device-to-host straight into the
destination byte buffer removed it. Detections were bit-identical: the 50-frame
agreement run reproduced the recorded baseline exactly (701/739/641).

This also corrects the earlier reading. GPU preprocessing alone was reported as
a net loss and blamed on the preprocessed tensor round-tripping to host; it was
the variant cost, which scales with element count and so fell hardest on the
configurations moving the largest tensors. GPU preprocessing alone is now a
clear win.

Transport measured three ways, client median: JSON 303.8 / 276.7 / 244.6 ms,
HTTP binary 155.0 / 164.8 / 74.0, gRPC 153.5 / 163.4 / 72.5. JSON is the
outlier; binary and gRPC agree within ~1.5 ms, so transport is not the
bottleneck once the tensor is not spelled out as JSON numbers.

Per-stage against tritonic on the same model and GPU, before PR #21: DALI
preprocess 7.66 ms vs 0.03, TensorRT 29.48 vs 24.48, GPU postprocess 2.58 vs
2.59 -- postprocess compute identical (same CUDA plugin). That decomposition
was read as "the whole gap is host round-trips" and a device-side handoff was
designed on it. The attribution was wrong: the gap was host work inside the
TensorRT stage, and removing it put GPU pre+post at 23.9 ms server-side against
tritonic's 27.04 ms ensemble.

Device-side tensor handoff is kept as a design (in
`baselines/preprocessing-latency.json`) but deprioritized. It would still
remove ~24 MB/frame of PCIe traffic, and it now buys an increment against a
competitive baseline rather than closing a gap -- while carrying a real risk,
since a partially-correct device path corrupts tensors silently instead of
failing.

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

- **Release wave 2026-10-03**: neuriplo v0.10.0 (plugin-loader hardening:
  malformed plugin metadata and outputs are rejected, outputs are released on
  every path, descriptor lookup is thread-safe; adds the consumer C ABI
  `neuriplo_c.h` with install/packaging), videocapture v0.6.0 (writer encodes
  on its own thread behind a bounded queue; `release()` returns `bool`), and
  neuriplo-infer v0.10.0 -> v0.10.2 (capabilities schema v2 with the run-report
  `diagnostics` section, async `--output_video` via videocapture v0.6.0, pins
  neuriplo v0.10.0). neuriplo-infer stays on the C++ API rather than the C ABI.
  The `versions.yaml` matrix and the capabilities contract (now version 2) are
  updated. Open: `--input_mode=encoded-image` against a model with a dynamic
  input dimension is still rejected by neuriplo-kserve-runtime v0.3.2.
- **Release wave 2026-09-12**: neuriplo-tasks v0.8.2 (image inputs typed
  `UInt8` now receive raw 0-255 pixels; detector-normalization fixes carried
  from v0.8.1), neuriplo v0.9.1, videocapture v0.5.0. neuriplo-infer `develop`
  merges the KServe input-datatype propagation (#44, pins tasks v0.8.2) and the
  plug-and-play README/docs split (#38/#39), and now keys its CI build caches on
  `versions.env` so a sibling pin bump re-fetches instead of reusing a stale
  checkout. The `versions.yaml` matrix is refreshed to the current tags; the
  compatibility sets carry their historical evidence forward with re-attestation
  noted per set.
- **Release wave 2026-06-12**: neuriplo v0.6.0 (multi-backend builds, plugin
  C ABI, raw-output API), runtime v0.1.0 (first release), client v0.3.0,
  infer v0.6.0 (pins -> neuriplo v0.6.0 + client v0.3.0, validated). All
  release PRs merged, tags pushed, master back-merged into develop.

## Known issues / debt

- **neuriplo Windows CI is broken at configure time**, independent of any code
  change: `could not find any instance of Visual Studio` from the
  `Visual Studio 17 2022` generator. The workflow last ran successfully in
  April 2026 on `feature/windows-support`; the hosted runner image has moved
  since. It fails before compiling anything, so it blocks every PR's rollup
  without indicating a real defect. Note there is already uncommitted
  `windows-build.yml` WIP in the neuriplo tree, so whoever owns that branch
  should land it rather than a second fix landing on top.
- **Heap corruption in the GPU-postprocess ensemble.** The runtime aborts with
  `malloc(): corrupted top size` (or `double free or corruption`) on the first
  JSON-transport request to `yolo26seg_gpu` after a binary-transport benchmark
  run. Pre-existing: reproduces identically on a binary built before the
  TensorRT change. Already ruled out -- DALI overrunning its output buffer
  (64-byte redzone on every `daliOutputCopy`, never trips), a DALI external
  input whose declared shape outruns its buffer (checked, never trips), and
  `RealNeuriploAdapter::infer`, which is where gdb catches the abort but only
  because it is the next large allocation. Full repro and backtrace under
  `known_bug` in
  `integration-tests/kserve-ensemble/baselines/preprocessing-latency.json`.
  Next step is ASAN or `MALLOC_CHECK_=3` to catch the write rather than the
  detection.
- Five neuriplo backends still inherit the slow default
  `get_infer_results_raw()` -- libtensorflow, libtorch, litert, migraphx, tvm.
  Same per-scalar variant cost TensorRT was paying; see
  `coordination/inbox/neuriplo.md`.
- neuriplo TensorRT metadata test disabled due to crash
  (`backends/tensorrt/test/TensorRTInferTest.cpp:119`) -- top roadmap item.
- Uncommitted agent WIP in neuriplo tree (ROADMAP + CI docs paths-ignore)
  and runtime tree (feature/step-13-2-infer-data-plane). Owners should
  commit or drop.
- Runtime CI checks out neuriplo@develop; consider pinning the v0.6.0 tag
  on release branches.
