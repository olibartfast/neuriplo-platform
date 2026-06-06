# Maintenance Control Plane

This directory defines cross-repository maintenance assets for the vision
platform repo cluster.

These files are consumed by humans, agents, and CI automation when a change spans
repository boundaries. They do not replace review authority in the owning
repositories.

## Cluster Scope

Core inference repos:

- `neuriplo-tasks`: task contracts, preprocessing, postprocessing, result types.
- `neuriplo`: backend abstraction, backend execution, runtime compatibility.
- `neuriplo-infer`: CLI, configuration, runtime wiring, visualization, local
  end-to-end application flow.
- `neuriplo-kserve-runtime`: KServe protocol, admission, scheduling, model
  lifecycle, operational endpoints.

Supporting repos:

- `videocapture`: image/video source handling consumed by `neuriplo-infer`.

Control-plane repo:

- `neuriplo-platform`: architecture docs, ADRs, contracts, version matrix,
  integration plans, cross-repo runbooks.

## Contents

- `CLUSTER_MAP.yaml`: cluster topology, ownership, dependency edges, validation
  order.
- `policies.yaml`: allowed and forbidden automated change classes.
- `repo-meta/*.yaml`: repo-specific entrypoints, public surfaces, constraints.
- `runbooks/`: execution guides for high-value maintenance flows.
- `PR_EVIDENCE_TEMPLATE.md`: standard evidence block for cross-repo PRs.

## Migration Note

This material originated in `neuriplo-infer/ops` when that repository acted as
the practical integration point for the stack. `neuriplo-platform` is now the
canonical home for cross-repository control-plane assets. `neuriplo-infer`
should eventually link here and retain only application-local docs.
