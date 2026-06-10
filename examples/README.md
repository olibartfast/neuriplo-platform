# Examples

End-to-end examples belong here when they describe integration across repository
boundaries. Repo-local command syntax and implementation-specific runner scripts
stay in the owning repository.

## Example Types

Platform examples should describe:

- repositories involved
- compatibility set or version requirements
- task/backend/runtime scenario
- input and model artifact assumptions
- expected contract-level output
- validation status

Repo-local examples should stay in implementation repos when they primarily show:

- CLI flag syntax
- local build commands
- local setup scripts
- backend-specific installation steps
- single-repo test fixtures

## Current Examples

- [Local inference E2E](e2e-local-inference/README.md): cross-repo local
  inference scenario using `neuriplo-infer`, `neuriplo-tasks`, `neuriplo`, and
  optional `videocapture`.
- [OpenAI-compatible generative serving E2E](openai-generative-serving/README.md):
  generative-track scenario (ADR 0006) serving a GGUF model via `llama-server`
  and consuming it with curl and `ghostgrid` (ADR 0007).
