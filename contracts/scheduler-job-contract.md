# Scheduler Job Contract

Owner: `neuriplo-platform`

Consumers: deployment automation, CI runners, operator session scripts

Version: 0.1.0

Status: Draft

## Purpose

Define one executor-neutral shape for a validation job and its evidence,
so the same job binds to Slurm today and to Kubernetes (or HTCondor /
OpenPBS) tomorrow without changing its identity or its evidence envelope.
Executor-specific flags live in a binding section that is never part of
the job identity. Hardware is referenced by generic profile ID from
`docs/architecture/heterogeneous-placement.md`, never by hostname or
address.

## Job Identity

| Field | Required | Meaning |
|---|---|---|
| `job_name` | yes | Human-readable name, unique within a session |
| `profile` | yes | Generic profile ID (`P-LNX-NVIDIA`, `P-LNX-CPU`, `P-LNX-EDGE-CPU`, `P-LNX-ARM-EDGE`, `P-WIN-CPU`, `P-CLD-AMD`, `P-CLD-BURST`) |
| `backend` | yes | `neuriplo` backend ID the profile must provide |
| `task` | yes | Task ID from `neuriplo-tasks` |
| `model` | yes | Model artifact reference (registry path plus pinned digest, never `latest`) |
| `dataset` | yes | Input/dataset reference with pinned revision |
| `compatibility_set` | no | `versions.yaml` set this job gives evidence for |
| `executor_binding` | yes | Executor-specific mapping (see below); excluded from identity |

Two jobs with equal identity fields are the same job even when their
bindings differ. A job whose identity fields change is a new job.

## Executor Binding

The binding translates identity to one executor and carries only
mechanical detail:

- Slurm: partition, constraint/feature matching the profile, GRES
  (for example `gpu:1`), time limit, container or module load commands.
- Kubernetes: node selector or affinity matching the profile, resource
  requests/limits, image reference, Job TTL.
- HTCondor/OpenPBS: requirement/classad or queue and resource strings
  matching the profile. For HTCondor, the profile maps to a ClassAd
  requirement and the backend to a job attribute; GPU profiles add the
  GPU discovery constraint. For OpenPBS, the profile maps to the queue
  plus resource string.

Bindings must not add semantics (no extra models, no different thresholds).

## Evidence Envelope

Every completed job produces one evidence record:

| Field | Required | Meaning |
|---|---|---|
| `job_name`, `profile`, `backend`, `task` | yes | Echo of the job identity |
| `executor` | yes | Which executor ran it (`slurm`, `kubernetes`, `htcondor`, `pbs`, `native-runner`) |
| `outcome` | yes | `pass`, `fail`, or `skipped` with reason |
| `log_ref` | yes | Path or URI of the full log |
| `metrics_ref` | no | Path of the benchmark JSON when the job is a benchmark |
| `session` | yes | Scheduled-session ID from the runbook |

`skipped` covers planned/on-demand states (profile offline for the
session, campaign scope exclusion). A skipped profile is not a failure.

## Compatibility Rules

- Adding an optional identity, binding, or evidence field is backward
  compatible.
- Adding a profile is backward compatible; removing one is breaking.
- Changing the meaning of `outcome` values is breaking.
- Executor bindings for a new executor are backward compatible when old
  bindings keep working unchanged.

## Validation Strategy

- Platform review checks that every scheduled session's jobs carry a
  profile from the placement doc and that evidence envelopes echo the job
  identity exactly.
- Owning-repo or operator harnesses validate executor translation (the
  binding reaches a node with the profile's backend) and record the
  evidence path; the platform records the path, it does not rerun the job.
- A contract fixture with one job per profile and one binding per
  supported executor is the executable shape check; it lives with the
  executor owner, not here.

## Examples

Slurm binding for a TensorRT job on the NVIDIA profile:

```text
identity: job_name=yolo-trt-smoke, profile=P-LNX-NVIDIA,
  backend=TENSORRT, task=yolo, model=<registry>/yolo11n.engine@<digest>,
  dataset=<registry>/smoke@<rev>
binding: partition=gpu, constraint=backend_tensorrt, gres=gpu:1
evidence: outcome=pass, executor=slurm, session=2026-10-29-smoke-1
```

Kubernetes binding for the same job identity on the same profile:

```text
identity: (unchanged from above)
binding: nodeSelector profile=P-LNX-NVIDIA, resources nvidia.com/gpu=1,
  image=<registry>/neuriplo-infer:tensorrt@<digest>, ttlSecondsAfterFinished=3600
evidence: outcome=pass, executor=kubernetes, session=2026-10-29-smoke-1
```

Native-runner binding for the Windows CPU profile:

```text
identity: job_name=ocv5-ort-smoke, profile=P-WIN-CPU,
  backend=OPENCV_DNN, task=yolo, model=<registry>/yolo11n.onnx@<digest>,
  dataset=<registry>/smoke@<rev>
binding: runner label P-WIN-CPU, OpenCV 5 plus ONNX Runtime toolchain
evidence: outcome=pass, executor=native-runner, session=2026-10-29-smoke-1
```
