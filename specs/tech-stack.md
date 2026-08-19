# Tech Stack

Living document. It records what this repository is built from and what the
governed ecosystem runs on, so a packet does not have to restate either.
Version pins live in [`versions.yaml`](../versions.yaml); this file records the
choices, not the numbers.

Last updated: 2026-08-19

## Control-Plane Stack (This Repository)

The control plane is documents plus small validators. There is no build step.

| Layer | Choice | Why |
|---|---|---|
| Documents | Markdown, ASCII only | Reviewable in a diff; ASCII is enforced across the tree by `scripts/check_platform.py` |
| Structured metadata | YAML | Compatibility sets, policies, cluster map, per-repo metadata |
| Measurements | JSON documents under `integration-tests/<scenario>/baselines/` | Machine-comparable, so a gate can read them instead of a human reading prose |
| Validators | Python 3.12, executable, dependency-light | Runs on a bare `ubuntu-latest` runner with no toolchain |
| Third-party Python | `pyyaml`, and only `pyyaml` | Every added dependency is a thing CI can break on |
| CI | GitHub Actions, `ubuntu-latest` | Hermetic: no GPU, no sibling checkouts, no serving endpoint |
| Branching | `main`, direct or short-lived branch to PR | Sibling Gitflow rules do not apply here, per [`.agents/rules/always-apply.md`](../.agents/rules/always-apply.md) |

Validators live in [`scripts/`](../scripts); the entry points are
`check_platform.py` (metadata, structure, ASCII, required docs),
`check_benchmark.py` and `check_benchmark_baseline.py` (benchmark documents and
their reachability from the version matrix), `generate_compat_report.py`, and
`bootstrap.py` (clones siblings at their pinned refs).

Constraints that follow from the above, and that every packet inherits:

- Scripts stay small, executable, and Python 3.12 compatible, with clear error
  messages and nonzero exits on failure.
- No model downloads, generated artifacts, or GPU-dependent checks enter the
  gate. Sibling-dependent and live-serving checks are opt-in.
- All files stay ASCII.

## Governed Ecosystem Stack

What the sibling repositories are built from. Authority for each row is the
owning repository; this table is the platform's view of it.

| Concern | Choice | Owner |
|---|---|---|
| Implementation language and build | C++ with CMake across all six repos | each owning repo |
| Backend execution | OpenCV DNN, ONNX Runtime, LibTorch, TensorRT, OpenVINO, LibTensorFlow, GGML, TVM | [`neuriplo`](https://github.com/olibartfast/neuriplo) |
| Task semantics | preprocess / execute / postprocess contract, computer vision as the first domain | [`neuriplo-tasks`](https://github.com/olibartfast/neuriplo-tasks) |
| Predictive serving protocol | KServe V2 / Open Inference Protocol, HTTP and gRPC, raw little-endian tensor payloads | [`neuriplo-kserve-client`](https://github.com/olibartfast/neuriplo-kserve-client) and [`neuriplo-kserve-runtime`](https://github.com/olibartfast/neuriplo-kserve-runtime) |
| Generative serving protocol | OpenAI-compatible endpoints (chat/completions, embeddings, SSE), served by llama-server or a vLLM-backed deployment | outside the ecosystem, per [ADR 0006](../docs/adr/0006-generative-serving-over-openai-protocol.md) |
| Ensembles | native runtime pipeline model kind, with GPU preprocessing available through a DALI-hosted pipeline | [`neuriplo-kserve-runtime`](https://github.com/olibartfast/neuriplo-kserve-runtime), per [ADR 0011](../docs/adr/0011-ensemble-pipeline-serving.md) |
| Application wiring | CLI, configuration, pipeline builder, visualization | [`neuriplo-infer`](https://github.com/olibartfast/neuriplo-infer) |
| Video and image sources | OpenCV with optional GStreamer and FFmpeg backends | [`videocapture`](https://github.com/olibartfast/videocapture) |
| Accelerators | CUDA is the primary target; ROCm (via the ONNX Runtime provider) and oneAPI (via the OpenVINO GPU plugin) are planned, not shipped | [`neuriplo`](https://github.com/olibartfast/neuriplo) |

The backend list above is the declared set in
[`ops/repo-meta/neuriplo.yaml`](../ops/repo-meta/neuriplo.yaml). Records added
since then name LiteRT, MIGraphX, ExecuTorch, and a DALI backend as also present
in `neuriplo`; the declared set has not been updated to match. Treat
`ops/repo-meta/neuriplo.yaml` as the thing to fix, not as the thing to work
around.

Interface detail for each row lives in [`contracts/`](../contracts/README.md);
GPU-specific expectations live in
[`docs/architecture/gpu-hardware-considerations.md`](../docs/architecture/gpu-hardware-considerations.md).

## Changing The Stack

- Adding a system, package, or runtime dependency anywhere in the ecosystem is a
  forbidden change class for automation
  ([`ops/policies.yaml`](../ops/policies.yaml)). It needs explicit human review.
- A stack change that alters a cross-repository interface needs an ADR, a
  contract update, and a new compatibility set with evidence, in that order.
- A stack change visible only inside one repository does not belong here. Record
  it there.
- Dependency alignment across repos follows
  [`docs/architecture/dependency-policy.md`](../docs/architecture/dependency-policy.md).
