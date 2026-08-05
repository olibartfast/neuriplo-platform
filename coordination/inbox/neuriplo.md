# Inbox: neuriplo

## [ ] from:human 2026-08-05 -- audit the remaining get_infer_results_raw() gaps
`TRTInfer` never overrode `get_infer_results_raw()`, so every TensorRT
inference fell back to the base implementation in `InferenceInterface.cpp`,
which runs `get_infer_results()` and builds one 16-byte `std::variant` per
output scalar before flattening it back to bytes. For a YOLO26m-seg engine
that was ~42MB of variant vector per frame, constructed and traversed twice.

Fixed in PR #21. Server-side, same engine and frames, same session: the full
GPU pre + GPU post ensemble went 70.9 -> 26.8 ms (2.65x), and detections were
bit-identical -- the 50-frame agreement run reproduced the recorded baseline
exactly. Details and the corrected attribution are in
`integration-tests/kserve-ensemble/baselines/preprocessing-latency.json`.

These backends still inherit the default and pay the same cost:

    libtensorflow  libtorch  litert  migraphx  tvm

(`cactus`, `ggml` and `llamacpp` too, but their outputs are small enough that
it likely does not matter.) Audit with:

    for d in backends/*/; do grep -rq get_infer_results_raw "$d/src" || echo "$d"; done

Two things worth knowing before picking this up. The cost scales with output
element count, so it is invisible on small models and severe on segmentation
or detection heads -- do not judge it on a classifier. And it is silent: the
default is *correct*, just slow, so nothing fails and no test catches it. The
verification that matters is an A/B on one machine in one session plus a
detection-agreement run, not a benchmark against a recorded baseline.

Each of these needs a real model on the matching runtime to verify, which is
why they were left rather than changed blind.
