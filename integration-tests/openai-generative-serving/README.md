# OpenAI-Compatible Generative Serving Smoke

Validation status: Metadata smoke scaffold, live `llama-server` run not yet
attested

Version set: `rfdetr-keypoint-pose-followup`

Owning repos: `neuriplo-platform`, `neuriplo-tasks`, `neuriplo-infer`

## Purpose

Track the generative serving path from ADR 0006. Predictive tasks stay on
KServe V2, while remote generative tasks use OpenAI-compatible endpoints such as
`llama-server` or a vLLM-backed KServe deployment.

## What It Checks

- the platform example exists
- the scenario uses `/v1/chat/completions`
- the serving dependency is declared as third-party, not a version-matrix member
- the path is not routed through KServe V2 tensors
- required non-streaming and streaming response fields are documented

## Usage

From `neuriplo-platform`:

```bash
integration-tests/openai-generative-serving/run.py
```

This check is GPU-free and server-free. Live evidence should attach a
`llama-server` startup command, one non-streaming chat-completions response, and
one streaming SSE response.
