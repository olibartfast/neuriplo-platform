# OpenAI-Compatible Generative Serving E2E

Validation status: Draft

Version set: `initial-architecture-baseline` from `versions.yaml`

Cross-repo scenario for the generative track defined in ADR 0006: a GGUF
model from the neuriplo ecosystem is served through an OpenAI-compatible
endpoint and consumed by external clients, with no custom protocol code.

## Repositories Involved

- `neuriplo-tasks`: owns the `image_understanding` task and the model
  export/setup notes (`export/image_understanding/ImageUnderstanding.md`).
- `neuriplo-infer`: embedded local mode for the same GGUF artifacts
  (unchanged by this example; shown only as the local-mode counterpart).
- `llama.cpp` (`llama-server`): third-party OpenAI-compatible server,
  a deployment dependency per ADR 0006, not a version-matrix member.

## Scenario

```text
GGUF model artifact (same artifact embedded local mode uses)
        |
        v
llama-server --model <model.gguf> [--mmproj <mmproj.gguf>] --port 8080
        |
        v
OpenAI-compatible endpoint: http://localhost:8080/v1/chat/completions
        |
        v
        curl / any OpenAI SDK
```

The KServe V2 protocol is not involved. The float-cast-bytes text encoding
used by the embedded llama.cpp backend boundary stays internal (ADR 0006).

## Model Artifact Assumptions

- A chat-capable GGUF model file readable by llama.cpp.
- For VLM use, the matching mmproj (vision projector) GGUF.
- Artifact selection and download steps live in `neuriplo-tasks`
  (`export/image_understanding/ImageUnderstanding.md`), not here.

## Serve

```bash
llama-server --model models/<model>.gguf --port 8080
# VLM variant:
llama-server --model models/<model>.gguf --mmproj models/<mmproj>.gguf --port 8080
```

## Consume: curl

```bash
curl -s http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
        "model": "local",
        "messages": [{"role": "user", "content": "Reply with the word ok."}],
        "max_tokens": 8
      }'
```

## Expected Contract-Level Output

- The endpoint returns an OpenAI chat-completions JSON body with
  `choices[0].message.content` holding the generated text.
- Streaming (`"stream": true`) returns SSE chunks with
  `choices[0].delta.content`.
- No V2 tensor shapes, datatypes, or float-cast text bytes appear anywhere
  on this path.

## Validation Status

Not yet validated end to end. Validation evidence to attach when run:
server startup log, one non-streaming curl response.
