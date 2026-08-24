# Capability Discovery Contract

Owner: [`neuriplo-infer`](https://github.com/olibartfast/neuriplo-infer)

Consumers: [`neuriplo-ui`](https://github.com/olibartfast/neuriplo-ui), other
out-of-process configuration tools

Version: 1

Status: Draft

## Purpose

Expose the capabilities of the exact `neuriplo-infer` binary a consumer will
invoke. The payload prevents browsers and other tools from maintaining a second
registry of tasks, models, sources, parameters, local backends, or remote
protocols.

The owning JSON Schema is
[`docs/capabilities.schema.json`](https://github.com/olibartfast/neuriplo-infer/blob/6518e8439d512f6bd1c5dc5d3a5a647e95a27917/docs/capabilities.schema.json).
This contract defines ownership and compatibility expectations; it does not
copy that schema.

## Invocation

```text
neuriplo-infer --capabilities
```

The command requires no task, source, weights, or endpoint arguments. On
success it exits with code 0 and writes one JSON document to standard output.
Consumers must invoke the executable with an argument array rather than shell
string composition.

## Top-Level Surface

Schema version 1 contains:

```text
schema_version          integer contract discriminator
producer                executable name and version
execution.workflows     workflows compiled into this binary
source_types            supported source categories and input representation
parameters              reusable CLI parameter definitions
tasks                   task, model, source, and parameter selections
```

Task, model, workflow, protocol, transport, source, and parameter identifiers
are machine identifiers. Presentation labels are a consumer concern.

## Workflow Semantics

Execution workflow is selected before workflow-specific configuration.

`local`:

- appears only when local inference support is compiled;
- lists compiled local backend identifiers in `backends`;
- has no remote protocols; and
- requires local model weights.

`client_server`:

- appears only when remote client support is compiled;
- does not list local backends;
- advertises protocol and compiled transport combinations; and
- requires an endpoint instead of local model weights.

KServe V2 is currently advertised under `client_server`, with HTTP and/or gRPC
according to the binary build. KServe must never appear in the `local.backends`
array.

A combined binary advertises both workflows. A local-only or client-server-only
binary advertises only the workflow it can execute. Consumers must not infer a
missing workflow from the parameter catalog.

## Parameter References

Workflow, task, and model parameter selections contain `required` and
`optional` identifier arrays. Every identifier must resolve to a definition in
the top-level `parameters` object.

Consumers use workflow parameters together with task and model parameters to
construct a configuration surface. A parameter present in the catalog but not
referenced by the selected workflow/task/model combination is not evidence that
the combination supports it.

## Compatibility Rules

- Adding an optional top-level object member is backward compatible for
  consumers that ignore unknown fields.
- Adding a task, model, alias, source type, parameter, backend, protocol, or
  transport is backward compatible.
- Removing or renaming an advertised identifier is breaking.
- Moving a backend into a different workflow or treating a remote protocol as a
  local backend is breaking.
- Adding a required field or changing an existing field's type or semantics is
  breaking and requires a new `schema_version`.
- Consumers must reject unsupported schema versions with an explicit error.
- A build omitting an unavailable workflow or optional transport is normal
  build-specific behavior, not a schema break.

## Validation Strategy

- `neuriplo-infer` validates model aliases against its task router, parameter
  reference resolution, identifier uniqueness, enum defaults, and compiled
  workflow reporting in unit tests.
- Local-only, client-server-only, and combined binaries validate their emitted
  JSON against the owning schema.
- `neuriplo-ui` validates the schema version, required shape, and parameter
  references before returning capability data to the browser.
- Cross-repository smoke coverage must exercise a combined binary and observe
  both `local` and `client_server` through the local adapter.
