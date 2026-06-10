# Architecture Decision Records

ADRs capture durable architecture decisions and their consequences. Use one ADR
per decision. Keep decisions small enough that they can be reviewed and revised
independently.

## Template

Use [0000-template.md](0000-template.md) for new records.

## Records

- [0001 Use neuriplo-platform as architecture control plane](0001-use-platform-as-architecture-control-plane.md)
- [0002 Centralize cross-repo control plane](0002-centralize-cross-repo-control-plane.md)
- [0003 Keep executable runners in owning repositories](0003-keep-runners-in-owning-repos.md)
- [0004 Rename vision-core and vision-inference to neuriplo-tasks and neuriplo-infer](0004-rename-vision-repos-to-neuriplo-tasks-infer.md)
- [0005 Create a dedicated neuriplo-ui repository for the Qt UI](0005-create-neuriplo-ui-repo.md)
- [0006 Serve generative tasks over OpenAI-compatible endpoints, keep predictive tasks on KServe V2](0006-generative-serving-over-openai-protocol.md)
- [0007 Register ghostgrid as a secondary agentic consumer](0007-register-ghostgrid-as-secondary-consumer.md)
