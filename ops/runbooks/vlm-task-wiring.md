# VLM Task Wiring Runbook

Use this when adding a new vision-language or multimodal task across the local
inference stack.

## Stack Order

```text
neuriplo-tasks       task contract, preprocess, postprocess, result type
neuriplo          backend execution and multimodal adapter behavior
neuriplo-infer  CLI, AppConfig, routing, rendering, e2e coverage
```

For serving support, add:

```text
neuriplo-kserve-runtime  request contract, model lifecycle, scheduling behavior
```

## Procedure

1. Define the task contract in `neuriplo-tasks`.
   - Register the task type.
   - Define preprocessing tensor layout.
   - Define postprocessing and result semantics.
   - Add unit tests for input and output contract behavior.

2. Implement backend support in `neuriplo`.
   - Add capability detection where needed.
   - Keep backend-specific model loading behind the backend adapter.
   - Normalize backend errors.
   - Add backend-local tests or smoke coverage.

3. Wire local application flow in `neuriplo-infer`.
   - Add CLI flags only when the application owns the user-facing option.
   - Extend `AppConfig` and routing.
   - Keep model/task semantics delegated to `neuriplo-tasks`.
   - Add end-to-end CLI coverage.

4. Wire serving flow in `neuriplo-kserve-runtime`, if required.
   - Validate KServe request shape.
   - Map lifecycle and readiness behavior.
   - Preserve public error response semantics.
   - Add protocol and scheduling tests.

5. Update `neuriplo-platform`.
   - Add or update ADRs if boundaries change.
   - Update contracts if tensor/result/wire semantics changed.
   - Update `versions.yaml` after compatible releases or WIP pins exist.
   - Add integration-test notes or fixtures.

## Guardrails

- Do not duplicate preprocessing or postprocessing in application/runtime repos.
- Do not expose backend runtime handles outside `neuriplo`.
- Do not change tensor shape, dtype, or result semantics without an explicit contract update.
- Do not make serving scheduler behavior observable unless it is documented as a runtime contract.
