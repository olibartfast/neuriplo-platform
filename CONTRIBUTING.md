# Contributing to neuriplo-platform

This is the architecture control plane for the neuriplo AI infrastructure and
GPU-first serving platform. It contains no runtime code -- it coordinates
contracts, decisions, version compatibility, integration tests, and examples
across 6 sibling implementation repositories.

## Quick Start

```bash
# 1. Clone the platform
git clone https://github.com/olibartfast/neuriplo-platform.git
cd neuriplo-platform

# 2. Bootstrap sibling repositories
python3 scripts/bootstrap.py

# 3. Validate the checkout cluster
python3 scripts/check_platform.py
```

The bootstrap script clones all 6 sibling repos into the parent directory and
checks out the exact commits pinned in [versions.yaml](versions.yaml). After
bootstrap your directory layout looks like this:

```text
workspace/
|- neuriplo-platform/          # architecture control plane (this repo)
|- neuriplo-tasks/             # domain/task layer
|- neuriplo/                   # GPU-first backend abstraction
|- neuriplo-infer/             # local application layer
|- neuriplo-kserve-client/     # KServe V2 protocol client
|- neuriplo-kserve-runtime/    # serving runtime
`- videocapture/               # video/image source layer
```

## Repository Map

| Repository | Role | Build entrypoint |
|---|---|---|
| neuriplo-tasks | Domain/task contracts, pre/post-processing | `cmake -S . -B build -DBUILD_TESTS=ON` |
| neuriplo | GPU-first backend abstraction (ONNX, TensorRT, etc.) | `cmake -S . -B build -DDEFAULT_BACKEND=OPENCV_DNN` |
| neuriplo-infer | CLI, config, E2E wiring (local + remote) | `cmake -S . -B build -DDEFAULT_BACKEND=OPENCV_DNN` |
| neuriplo-kserve-client | KServe V2 client (HTTP/gRPC, backend-agnostic) | `cmake -B build -DKSERVE_CLIENT_BUILD_TESTS=ON` |
| neuriplo-kserve-runtime | KServe V2 server, batching, scheduling | `cmake --preset debug` |
| videocapture | Video/image I/O sources | `cmake -S . -B build` |

## First Things to Read

If you're new, read these in order:

1. [Mission](specs/mission.md) -- why this repository exists, what it owns, and what it refuses to own
2. [Architecture overview](docs/architecture/overview.md) -- ecosystem map and repo responsibilities
3. [Dependency policy](docs/architecture/dependency-policy.md) -- cross-repo change rules
4. [ADR index](docs/adr/README.md) -- design decisions (scan the titles, read the latest)
5. [Contract index](contracts/README.md) -- cross-repo API contracts
6. [Roadmap](specs/roadmap.md) -- what is in flight and what comes next

The remaining docs ([ownership](docs/architecture/ownership.md),
[tech stack](specs/tech-stack.md),
[production roadmap](docs/architecture/production-roadmap.md),
[GPU considerations](docs/architecture/gpu-hardware-considerations.md)) are
reference material for specific topics.

## Making Changes

For every major platform change:

1. Write an ADR using [the template](docs/adr/0000-template.md).
2. Update or add architecture documentation.
3. Implement in the owning repository (not this one).
4. Add tests in the owning repository and integration coverage here.
5. Update contracts, examples, and the version matrix.

This repo follows a `main`-branch workflow. Sibling repos use Gitflow
(`develop` for normal work, `master` for releases).

## Validation

Run before every commit:

```bash
python3 scripts/check_platform.py
```

This validates YAML metadata, ASCII content, docs, examples, integration tests,
version matrix, policies, and cluster map consistency.

When integration-test metadata or smoke behavior changes, also run:

```bash
python3 integration-tests/local-inference-smoke/run.py
```

## Where to Go Next

- [Examples](examples/README.md) -- end-to-end scenarios
- [Runbooks](ops/runbooks/) -- operational procedures (API migration, version bumps, CI triage)
- [Cluster map](ops/CLUSTER_MAP.yaml) -- full dependency topology
- [Version matrix](versions.yaml) -- known-good version combinations
