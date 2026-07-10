# OpenCV Boundary v0.6.0 Compatibility Evidence

Validation status: Active compatibility set, evidence-tracked

Version set: `opencv-boundary-v060` from `versions.yaml`

Owning repos: [neuriplo-tasks](https://github.com/olibartfast/neuriplo-tasks), [neuriplo-infer](https://github.com/olibartfast/neuriplo-infer), [tritonic](https://github.com/olibartfast/tritonic), and [neuriplo-track](https://github.com/olibartfast/neuriplo-track)

This scenario records the migration to `neuriplo-tasks v0.6.0`, where public
task contracts use native vision types and OpenCV interoperability is optional.

## Evidence

- [`evidence.yaml`](evidence.yaml) records attested clean FetchContent builds,
  consumer unit tests, the neuriplo-track CLI smoke, and KServe HTTP plus gRPC CI.
- `scripts/generate_compat_report.py` writes deterministic report artifacts under
  `reports/`; CI runs the same generator with `--check`.

## Regeneration

```bash
scripts/generate_compat_report.py --compat-set opencv-boundary-v060
scripts/generate_compat_report.py --check
```
