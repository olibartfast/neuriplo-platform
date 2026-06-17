# Benchmarking Contract

Owner: `neuriplo-platform` (contract definition); each implementation repo owns
its benchmarks.

Consumers: CI automation, release process, compatibility matrix gate

Status: Draft

## Purpose

Define the expectations, metrics, reproducibility rules, and regression
thresholds for inference performance benchmarks across the neuriplo platform.
Benchmarks are the platform's primary throughput/latency quality signal.

## Benchmark Categories

### Single-Stream Latency

One request at a time, no concurrency. Measures end-to-end latency for a single
inference.

```text
metrics:  P50, P95, P99 latency (ms)
warmup:   >= 50 iterations discarded
samples:  >= 200 iterations measured
```

### Batched Throughput

Maximum sustained throughput at a given batch size. Concurrency may be tuned.

```text
metrics:  requests/sec, images/sec or tokens/sec, GPU utilization (%)
batch:    fixed batch size (1, 4, 8, 16, 32, max-supported)
warmup:   >= 20 iterations discarded
duration: >= 30 seconds steady state
```

### Max Throughput (Saturation)

Find maximum throughput by increasing concurrency until latency degrades beyond
the latency SLA.

```text
metrics:  max stable requests/sec, concurrency at max, P99 latency at max
SLA:      P99 latency <= 2x single-stream P99 latency (default; override per task)
```

## Metric Definitions

```text
latency_ms:
  end-to-end:   from request enqueue to response available (includes queue wait)
  inference:    from tensor submission to tensor output (excludes queue, pre/post)
  queue_wait:   from request enqueue to scheduling start

throughput:
  requests_per_second:  completed requests / wall-clock seconds
  tokens_per_second:    output tokens / wall-clock seconds (generative tasks)
  images_per_second:    completed inferences / wall-clock seconds (CV tasks)

gpu_utilization_pct:  SM occupancy or equivalent (sampled during benchmark)
gpu_memory_used_mib:  peak working set during benchmark
```

## Reproducibility Requirements

A benchmark is reproducible when:

```text
1. Model artifact is pinned by hash (SHA256).
2. Input data is fixed (seed, shape, content; synthetic or canonical dataset).
3. GPU device is documented by name, driver version, and memory.
4. Backend and version are documented.
5. Number of warmup and measurement iterations is stated.
6. No other workload shares the GPU during measurement.
7. Performance governor or equivalent is locked (no dynamic frequency scaling).
```

## Regression Threshold

```text
latency regression:  P99 > 1.15x baseline for the same compatibility set = flagged
throughput regression: requests/sec < 0.90x baseline = flagged
memory regression:   peak GPU memory > 1.10x baseline = flagged

Flagged regressions block a compatibility set promotion until the owning repo
documents the cause or reverts.
```

The baseline is the last promoted compatibility set. First-time benchmarks
establish the baseline.

## Reporting Format

Benchmarks produce a JSON artifact:

```json
{
  "benchmark_version": "1.0",
  "compatibility_set": "ecdset-kserve-litert-followup",
  "timestamp": "2026-06-18T12:00:00Z",
  "hardware": {
    "device_name": "NVIDIA L40S",
    "driver_version": "550.127.05",
    "memory_mib": 46068
  },
  "backend": {
    "name": "tensorrt",
    "version": "10.7.0"
  },
  "model": {
    "name": "ecdet-resnet18",
    "sha256": "abc123..."
  },
  "scenario": "batched_throughput",
  "batch_size": 8,
  "warmup_iterations": 20,
  "measurement_iterations": 200,
  "metrics": {
    "requests_per_second": 142.3,
    "latency_p50_ms": 54.2,
    "latency_p95_ms": 68.7,
    "latency_p99_ms": 82.1,
    "gpu_utilization_pct": 87.4,
    "gpu_memory_used_mib": 3421
  }
}
```

## Conformance Shape

A result file carries one or more measured runs in a `results` array (so a single
session can report several transport paths or batch sizes). Required top-level
fields: `benchmark_version`, `compatibility_set`, `timestamp`, `hardware`,
`backend`, `model`, `results`. Each entry in `results` requires `scenario`
(`single_stream` | `batched_throughput` | `max_throughput`), `batch_size`, and a
`metrics` object carrying the metric keys above.

Unmeasured fields must be present with a `null` value rather than omitted, so
consumers can rely on the shape. `scripts/check_benchmark.py` enforces this and
runs against every `integration-tests/**/results/*.json`.

No conforming baseline has been published yet. Latency evidence (HTTP JSON vs
binary vs gRPC) is recorded in
`integration-tests/kserve-runtime-edgecrafter-e2e/BENCHMARK.md`.

## Validation Strategy

- Structural validation: `scripts/check_benchmark.py` validates result files
  against the conformance shape above.
- Each implementation repo owns benchmark scripts and CI gating rules.
- Platform CI may optionally run benchmarks on pinned compatibility sets when GPU
  hardware is available.
- GPU-free CI environments skip benchmarks and report `skipped` status.
- The platform repo validates that every compatibility set has a benchmark
  artifact path declared (not that the artifact exists at all times).

## Relationship to Other Contracts

- `gpu-capability-contract.md`: benchmarks document GPU capabilities against the
  capability contract surface.
- `backend-contract.md`: benchmark scenarios exercise the backend execution path.
- `runtime-contract.md`: serving benchmarks exercise the KServe V2 path.
- `versions.yaml`: each compatibility set may link benchmark baseline artifacts.
