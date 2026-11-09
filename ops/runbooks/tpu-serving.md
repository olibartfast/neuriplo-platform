# TPU Serving Runbook

Use this runbook to stand up a Cloud TPU VM, run an operator-supplied KServe V2
service, validate the TensorFlow ResNet-50 classifier artifact on CPU and TPU,
invoke it from `neuriplo-infer`, and record reproducible evidence.

Remote TPU is serving, not an in-process backend. The client selects a service
by endpoint, model name, and version; the service owns the TPU device, compiler,
and runtime. The service boundary is defined in
[`contracts/tpu-serving-contract.md`](../../contracts/tpu-serving-contract.md)
and in
[`docs/architecture/inference-modes.md`](../../docs/architecture/inference-modes.md).
No `tpu` value is added to the client `device` configuration.

The first representative is the TensorFlow ResNet-50 classifier, exported by
[neuriplo-tasks](https://github.com/olibartfast/neuriplo-tasks). It keeps the
existing raw-BGR/logits task contract:

```text
input:  image, Float32, NHWC, [1, 224, 224, 3], BGR pixels in [0, 255]
output: logits, Float32, [1, 1000]
```

The TPU service implementation is out of scope for this repository. This
runbook treats the start command as operator-supplied and only fixes the KServe
V2 HTTP surface and the artifact contract the service must honor.

## Goal

Produce one attested TPU result for the TensorFlow classifier that a reviewer
can reproduce from the commands and values recorded in the evidence section.
Metadata-only inspection is not a TPU pass.

## Procedure

### 1. Confirm prerequisites and quota

Before creating a TPU VM, confirm all of the following:

- A Google Cloud project with billing enabled.
- The Cloud TPU API is enabled:
  ```bash
  gcloud services enable tpu.googleapis.com --project=<project>
  ```
- Cloud TPU quota for the target zone is greater than zero. Check the quota in
  the Google Cloud console under `IAM & Admin > Quotas` (filter for the Cloud
  TPU API), or attempt the create and read the quota error. This repository
  does not request or reserve quota.
- The exported SavedModel directory exists. From a `neuriplo-tasks` checkout with
  TensorFlow installed, export the representative to a concrete local path:

  ```bash
  python3 export/classification/tensorflow/export_tf_saved_model_classifier.py \
    --output /tmp/tf-regate-resnet50
  ```

  Set `LOCAL_MODEL_DIR=/tmp/tf-regate-resnet50` in the session variables below,
  or obtain the attested artifact from the owning packet and point
  `LOCAL_MODEL_DIR` at that directory.
- One validation image is available locally. `neuriplo-tasks` does not ship an
  image; the caller supplies it.
- The client binary is a [neuriplo-infer](https://github.com/olibartfast/neuriplo-infer)
  build with KServe client support. HTTP is required for this runbook; gRPC is
  optional.

Set names once for the session. Replace every `<...>` placeholder before
running a command:

```bash
export PROJECT=<project>
export ZONE=<zone>
export TPU_NAME=<tpu-name>
export ACCELERATOR_TYPE=<accelerator-type>
export TPU_RUNTIME=<tpu-runtime-version>
export REMOTE_MODEL_DIR=<remote-saved-model-dir>
export REMOTE_IMAGE=<remote-image>
export LOCAL_MODEL_DIR=<local-saved-model-dir>
export LOCAL_IMAGE=<local-image>
```

Use a current Cloud TPU VM accelerator type for the chosen zone and runtime, for
example `v5litepod-1` with `tpu-ubuntu2204-base`. Record the exact values in the
evidence table. Multi-host slices and TPU training are out of scope.

### 2. Create the Cloud TPU VM

Create the VM with `gcloud`. Keep the zone in every later command:

```bash
gcloud compute tpus tpu-vm create "${TPU_NAME}" \
  --project="${PROJECT}" \
  --zone="${ZONE}" \
  --accelerator-type="${ACCELERATOR_TYPE}" \
  --version="${TPU_RUNTIME}"
```

Confirm it exists before continuing:

```bash
gcloud compute tpus tpu-vm list \
  --project="${PROJECT}" \
  --zone="${ZONE}"
```

A create failure with a quota message means the prerequisite in step 1 is not
met. Do not retry in another zone without recording the change.

### 3. Copy the artifact, image, and helper

Copy the SavedModel directory and the validation image to the TPU VM:

```bash
gcloud compute tpus tpu-vm scp --recurse "${LOCAL_MODEL_DIR}" \
  "${TPU_NAME}:${REMOTE_MODEL_DIR}" \
  --project="${PROJECT}" \
  --zone="${ZONE}"

gcloud compute tpus tpu-vm scp "${LOCAL_IMAGE}" \
  "${TPU_NAME}:${REMOTE_IMAGE}" \
  --project="${PROJECT}" \
  --zone="${ZONE}"
```

The validation helper lives in `neuriplo-tasks`. Either clone the pinned tag on
the VM or copy the helper directory. Do not install its unpinned
`requirements.txt` over the TPU VM runtime:

```bash
gcloud compute tpus tpu-vm scp --recurse \
  <path-to-neuriplo-tasks>/export/classification/tensorflow \
  "${TPU_NAME}:<remote-tensorflow-export-dir>" \
  --project="${PROJECT}" \
  --zone="${ZONE}"
```

The helper is `export/classification/tensorflow/verify_tpu_saved_model.py` in
the `neuriplo-tasks` checkout. It has three modes: `metadata` (no device
execution), `cpu` (reference execution), and `tpu` (TPUStrategy execution that
fails explicitly instead of falling back to CPU).

### 4. SSH to the VM

```bash
gcloud compute tpus tpu-vm ssh "${TPU_NAME}" \
  --project="${PROJECT}" \
  --zone="${ZONE}"
```

Run the remaining artifact checks inside this SSH session. If the service is
bound to the VM loopback, open a second tunnel from the operator host:

```bash
gcloud compute tpus tpu-vm ssh "${TPU_NAME}" \
  --project="${PROJECT}" \
  --zone="${ZONE}" \
  --ssh-flag="-L 8080:localhost:8080"
```

### 5. Validate the artifact on CPU

Use the TensorFlow runtime already installed on the TPU VM. Cloud TPU VM images
ship a TensorFlow and `libtpu` pair that matches the VM runtime. Do not install
`export/classification/tensorflow/requirements.txt` on the VM: it is unpinned
and pulls TensorFlow and ONNX packages that can replace the TPU-compatible
stack. If you need a separate environment, create an isolated one with a pinned
TensorFlow and the matching `libtpu`, and use its interpreter for every helper
command below.

Run the CPU-side signature check first. Metadata mode needs only TensorFlow: it
does not execute a device, read an image, or require Pillow, so omit `--image`:

```bash
python3 <remote-tensorflow-export-dir>/verify_tpu_saved_model.py \
  --saved-model "${REMOTE_MODEL_DIR}" \
  --mode metadata
```

Expected result:

- Exactly one non-resource input and exactly one output in the
  `serving_default` TensorFlow signature.
- Input is `float32`, rank 4, with spatial/channel dimensions `224, 224, 3`.
  The SavedModel signature may report `None` for the batch axis; inference
  requests still use batch 1.
- Output is `float32`, rank 2, with a class dimension of `1000`. The signature
  may report `None` for the batch axis; the service returns batch 1.
- Exit code 0.

The helper prints the TensorFlow signature keys for the input and output (for
example `image` and `output_0`). These are TensorFlow signature/op names, not
necessarily the KServe wire tensor names. The input wire name is fixed as
`image`; the output wire name is model-specific and must be read from the
service's per-model metadata in step 8. For this representative, metadata must
advertise exactly one output tensor, but do not require a specific output wire
name and do not require the signature key to equal the wire name.

Then run the CPU reference on the same artifact and image. This mode decodes
the image, so Pillow is required. Use the preinstalled runtime when Pillow is
already present; otherwise install only a pinned Pillow into the isolated
environment described above, never the unpinned requirements file:

```bash
python3 <remote-tensorflow-export-dir>/verify_tpu_saved_model.py \
  --saved-model "${REMOTE_MODEL_DIR}" \
  --image "${REMOTE_IMAGE}" \
  --mode cpu
```

Expected result:

- `device: CPU`
- An `image:` line and a `sha256:` line for the validation image.
- Five `class=<index> score=<value>` lines under `top5:`.

Record the image SHA-256 and the top-5 classes and scores. This is the CPU
baseline for the comparison in step 10, not the TPU result.

### 6. Validate the artifact on TPU

On the Cloud TPU VM, run the helper in TPU mode with the same interpreter used
in step 5. Set `TPU_NAME` if the resolver cannot discover the local TPU
automatically:

```bash
export TPU_NAME="${TPU_NAME}"

python3 <remote-tensorflow-export-dir>/verify_tpu_saved_model.py \
  --saved-model "${REMOTE_MODEL_DIR}" \
  --image "${REMOTE_IMAGE}" \
  --mode tpu
```

Expected result:

- `device: TPU`
- The same image path and SHA-256 as the CPU run.
- Five `class=<index> score=<value>` lines under `top5:`.
- Exit code 0.

The helper refuses to fall back to CPU. A clear error about missing
`TPUClusterResolver`, a failed cluster connection, or failed TPU initialization
is a failed TPU run, not a pass. Record the TensorFlow version (`python3 -c
"import tensorflow as tf; print(tf.__version__)"`) and the `libtpu` version
reported by the runtime.

### 7. Start the service (operator-supplied)

The TPU-side service is supplied by the operator and is not pinned or shipped by
this repository. Start it so that it loads the validated SavedModel and exposes
KServe V2 HTTP with model name `tensorflow-resnet50` and version `1`.

Use the operator's documented command; the shape below is a placeholder, not a
required implementation:

```bash
<service-start-command> \
  --saved-model="${REMOTE_MODEL_DIR}" \
  --model-name=tensorflow-resnet50 \
  --model-version=1 \
  --http-port=8080
```

The contract's example model name is `resnet50_tf_tpu`. This runbook uses the
concrete value `tensorflow-resnet50` that the client command below sends; the
service metadata must advertise exactly that name and version.

Record the service image digest or commit. The service must:

- Accept a dense Float32 NHWC tensor named `image` shaped `[1, 224, 224, 3]`
  containing raw BGR pixels in `[0, 255]`.
- Return raw Float32 logits `[1, 1000]`. Do not apply softmax server-side.
- Advertise exactly one output tensor in per-model metadata. Its wire name is
  model-specific (the first Keras 3 export uses `output_0`); the client reads it
  from metadata and does not hardcode `logits`.
- Serve `/v2/health/live`, `/v2/health/ready`, and the model metadata routes
  described in the TPU serving contract.
- Keep device placement, compiler, and runtime inside the service.

If the service loads the SavedModel through a different input name or layout,
fix the service or the artifact before running the client. Client-side
reshaping is not part of the contract.

### 8. Check health and metadata

From a host that can reach the endpoint, set the endpoint and query health and
metadata. Use the tunnel from step 4 when the service listens on the VM
loopback:

```bash
export KSERVE_ENDPOINT=http://<endpoint-host>:<port>

curl -sS -o /dev/null -w 'server-live %{http_code}\n' \
  "${KSERVE_ENDPOINT}/v2/health/live"
curl -sS -o /dev/null -w 'server-ready %{http_code}\n' \
  "${KSERVE_ENDPOINT}/v2/health/ready"
curl -sS -o /dev/null -w 'model-ready %{http_code}\n' \
  "${KSERVE_ENDPOINT}/v2/models/tensorflow-resnet50/ready"
curl -sS -o /dev/null -w 'version-ready %{http_code}\n' \
  "${KSERVE_ENDPOINT}/v2/models/tensorflow-resnet50/versions/1/ready"
curl -fsS "${KSERVE_ENDPOINT}/v2/models/tensorflow-resnet50"
curl -fsS "${KSERVE_ENDPOINT}/v2/models/tensorflow-resnet50/versions/1"
```

Expected result:

- Server liveness, server readiness, model readiness, and version readiness all
  return HTTP 200.
- Per-model readiness is authoritative for routing: require HTTP 200 from both
  `/v2/models/tensorflow-resnet50/ready` and
  `/v2/models/tensorflow-resnet50/versions/1/ready` before invoking the client
  in step 9.
- Model metadata names `tensorflow-resnet50` and version `1`.
- Model metadata advertises exactly one output tensor.
- The input is Float32 with shape `[-1, 224, 224, 3]` or `[1, 224, 224, 3]`. A
  `-1` (or `None`) batch is a dynamic batch advertised by metadata; inference
  requests still use batch 1.
- The output is Float32 logits with shape `[-1, 1000]` or `[1, 1000]`, again
  with batch 1 per request. Its wire name is whatever metadata advertises; do
  not require `logits` or `output_0`.

If any readiness endpoint, including the per-model and per-version routes,
returns 503, the model is still loading or the service crashed. Wait for
readiness and inspect the service log. Do not send inference traffic to a
service that is not ready.

### 9. Run the neuriplo-infer client

Run the client only after both per-model readiness checks in step 8 returned
HTTP 200. The example below uses the exact model identity and HTTP transport
this runbook validates; replace only the source, endpoint, and output options:

```bash
neuriplo-infer \
  --source="${LOCAL_IMAGE}" \
  --type=tensorflowclassifier \
  --kserve_endpoint="${KSERVE_ENDPOINT}" \
  --kserve_model_name=tensorflow-resnet50 \
  --kserve_model_version=1 \
  --kserve_transport=http \
  --no_display
```

Do not pass `--weights`, `--use-gpu`, or a `device` value. Remote mode is
selected by `--kserve_endpoint`; the model artifact is loaded by the service.
Record the command, exit status, endpoint, output image path, and the run report
at `data/output/run_report.json`.

If HTTP is not available in the client build, stop. This runbook does not claim
a gRPC result.

### 10. Compare CPU and TPU top-k

Compare the same image across the CPU reference (step 5), the TPU helper (step
6), and the client run (step 9):

- Confirm all runs used the same image SHA-256.
- Compare top-1 class identity first.
- Compare the top-5 class indices and their order.
- Do not compare raw scores across scales. The helper prints raw logits, while
  the client returns probabilities after applying softmax once. If you compare
  scores, either apply one softmax to the helper logits first or record the
  raw-logit and client-probability scales separately and compare only class
  identity and ordering.

To convert the helper's raw top-5 logits to probabilities for a score
comparison, use the same softmax the client applies:

```bash
python3 - <<'PY'
import math

# Paste the helper's raw top-5 scores, in the order printed.
logits = [0.0, 0.0, 0.0, 0.0, 0.0]
shifted = [value - max(logits) for value in logits]
weights = [math.exp(value) for value in shifted]
total = sum(weights)
print([weight / total for weight in weights])
PY
```

Do not require bitwise or exact floating-point parity. TPU and CPU kernels may
use different reductions and fused operations, so small score differences are
expected even when the model and input are correct. State the tolerance and
which score scale (raw logits or client probabilities) the evidence record uses.
A practical first check is the same top-1 class and the same top-5 order; a
different top-1 needs the diagnosis in the next section, not a looser tolerance.

If only the client result differs from both helper runs, investigate the
client-side tensor construction before blaming the TPU. If the TPU helper and
the client agree but differ from CPU, record the difference and investigate
preprocessing and output decoding.

## Failure Diagnosis

| Symptom | Likely cause | Check |
|---|---|---|
| Connection refused or timeout | Wrong endpoint, scheme, port, or no tunnel | Re-check `--kserve_endpoint`, the scheme (`http` vs `https`), and the SSH tunnel from step 4. |
| HTTP 404 on `/v2/models/...` | Wrong model name or version | Compare with metadata in step 8. The expected values are `tensorflow-resnet50` and `1`. |
| HTTP 404 or 405 on `/v2/...` from the client | Endpoint includes the wrong path prefix or points at the wrong port | Point at the service root, not a UI or metrics port. A path prefix is allowed only when the service advertises it. |
| HTTP 400 with an invalid tensor shape error | Client and service disagree on rank, axes, or batch | Confirm NHWC `[1, 224, 224, 3]`. NCHW `[1, 3, 224, 224]`, a missing batch axis, or a dynamic shape mismatch is not the contract. |
| HTTP 400 with an unsupported dtype error | Service expects UINT8 or another dtype | The contract is Float32 pixels in `[0, 255]`. Do not quantize or rescale to `[0, 1]` at the client. |
| HTTP 503 or readiness never turns 200 | Model still loading, crashed, or failed to allocate the TPU | Read the service log. Retry only after `/v2/health/ready` is 200. |
| Model output has `[1, 1000]` but scores look like probabilities | A softmax was applied at the client, service, or helper | The task contract returns raw logits. Remove the extra softmax and compare logits. |
| Correct top-5 on CPU but wrong classes over the service | BGR and RGB swapped, or preprocessing applied twice | Both helper modes send raw BGR pixels and the SavedModel applies the ResNet mean subtraction. Do not feed RGB, and do not subtract the mean again. |
| Top-5 classes look plausible but scores are compressed | Softmax applied twice, or logits converted to probabilities twice | Decode once. Scores in the evidence table are logits unless the runbook step says otherwise. |
| TPU helper errors about `TPUClusterResolver` or initialization | Not on a TPU VM, wrong runtime, or missing `libtpu` | Confirm the VM type and runtime, set `TPU_NAME`, and record the failure. It is not a CPU pass. |
| Client build rejects `--kserve_transport=http` | Build without KServe client support | Use a build with KServe client support and record the rejection. This runbook does not cover local fallback. |

Escalate to the owning repository rather than editing platform contracts when
the defect is in task preprocessing, the client adapter, or the service:

- `neuriplo-tasks`: tensor names, shapes, dtypes, BGR/RGB, softmax, or top-k.
- `neuriplo-infer` or `neuriplo-kserve-client`: request construction, transport,
  endpoint parsing, or client-side decoding.
- The operator's TPU service: model loading, device placement, readiness, or
  server-side preprocessing.

## Cost and Teardown

A Cloud TPU VM is billed while it exists, including idle time. Delete it as soon
as the evidence is captured:

```bash
gcloud compute tpus tpu-vm delete "${TPU_NAME}" \
  --project="${PROJECT}" \
  --zone="${ZONE}"
```

Confirm the VM is gone:

```bash
gcloud compute tpus tpu-vm list \
  --project="${PROJECT}" \
  --zone="${ZONE}"
```

Close any SSH tunnel opened in step 4. Do not leave a running TPU VM or a
reserved accelerator for follow-up work unless a named owner and teardown date
are recorded. Copy only the evidence, logs, and top-5 output back to the
operator host before deleting the VM.

## Evidence Recording

Record one row per check in the packet `validation.md` results and attach the
same data to the PR using
[`ops/PR_EVIDENCE_TEMPLATE.md`](../PR_EVIDENCE_TEMPLATE.md). A TPU claim without
all of the following is not a TPU pass:

| Field | Example |
|---|---|
| Date and operator | `2026-11-09`, `<name>` |
| Project, zone, TPU name, accelerator type, runtime | `<project>`, `<zone>`, `<tpu-name>`, `<accelerator-type>`, `<runtime>` |
| TensorFlow and `libtpu` versions | exact versions printed on the VM |
| Service identity | image digest or commit, model name, version |
| Artifact identity | SavedModel path, export command or commit, artifact checksum |
| Input identity | validation image path and SHA-256 |
| Commands | the exact create, copy, helper, curl, and client commands used |
| CPU reference | metadata result and top-5 classes and scores |
| TPU result | TPU helper top-5 classes and scores, plus client top-5 when available |
| Comparison | top-1/top-5 agreement, score differences, tolerance, and verdict |
| Cost | start and delete times, or the billed duration |
| Unrun checks | explicit `not executed` entries with the reason |

Guardrails:

- Metadata-only output is a valid CPU-side artifact check, not a TPU pass.
- Do not add an active compatibility set to [`versions.yaml`](../../versions.yaml)
  from this runbook. The missing compatibility set is intentional until the
  owning repositories produce attested evidence; a draft set is also evidence
  gated and is not added by this runbook.
- Do not claim a GPU or TPU result from a different host, artifact, or image
  SHA-256.
- Keep console output and logs free of credentials and private image content
  before attaching them.

## Exit Criteria

- The TPU VM was created with recorded quota and configuration.
- CPU metadata and CPU reference checks passed on the same artifact.
- TPU mode passed and reported `device: TPU`.
- The service passed health and metadata checks for `tensorflow-resnet50`
  version `1`.
- The client ran with HTTP and recorded its output and run report.
- CPU and TPU top-5 results were compared with a stated tolerance, not bitwise
  parity.
- The TPU VM was deleted and the cost was recorded.
- Evidence is in the packet and the PR evidence block.
