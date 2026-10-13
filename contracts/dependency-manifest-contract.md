# Dependency Manifest Contract

Name: dependency-manifest

Owner: standalone dependency-manager repo (coldpac, under
`olibartfast`; exact name decided at creation). Platform records the
interface; implementation lives in that repo.

Consumers:
[`videocapture`](https://github.com/olibartfast/videocapture) (first),
[`neuriplo`](https://github.com/olibartfast/neuriplo),
[`neuriplo-infer`](https://github.com/olibartfast/neuriplo-infer),
[`neuriplo-kserve-runtime`](https://github.com/olibartfast/neuriplo-kserve-runtime),
[`neuriplo-kserve-client`](https://github.com/olibartfast/neuriplo-kserve-client),
[`neuriplo-tasks`](https://github.com/olibartfast/neuriplo-tasks).

Version: 0.1.0

Status: Draft

## Purpose

One per-project declaration of third-party and sibling dependencies that
projects today across `versions.env` files, `setup_*.sh` curl tarballs,
apt baselines, and CMake `FetchContent` pins. The manager resolves intent
to a lockfile, projects a backwards-compatible `versions.env`, and reports
status (wanted vs installed vs update-available) uniformly across
providers.

## Schema

`deps.yaml` (intent, checked in per consumer repo):

```yaml
schema_version: 1
packages:
  - name: opencv
    kind: system-library
    wanted: ">=4.6.0"
    providers: [apt, conan, vcpkg, custom-url]
    preferred: apt
    components: [core, imgproc]
    linkage: shared
    platforms: [ubuntu-24.04]
  - name: onnxruntime-gpu
    kind: backend-binary
    wanted: "==1.19.2"
    providers: [custom-url]
    url: "https://github.com/microsoft/onnxruntime/releases/download/v1.19.2/onnxruntime-linux-x64-gpu-1.19.2.tgz"
    sha256: "<64-hex>"
  - name: neuriplo
    kind: sibling
    wanted: "v0.10.0"
    providers: [fetchcontent]
    repo: "olibartfast/neuriplo"
    ref: "<40-char-sha>"
```

`deps.lock` (resolved, checked in; the only thing installers execute):

```yaml
schema_version: 1
resolved:
  - name: opencv
    version: "4.6.0+dfsg-13.1ubuntu1"
    provider: apt
    package: "libopencv-dev"
  - name: onnxruntime-gpu
    version: "1.19.2"
    provider: custom-url
    sha256: "<64-hex>"
```

`versions.env` projection (generated, backwards compatible):

```sh
OPENCV_VERSION=4.6.0
ONNX_RUNTIME_VERSION=1.19.2
NEURIPLO_VERSION=v0.10.0
```

Precedence: `cmake -D` > environment > `versions.env` > lockfile default,
preserving current `neuriplo-infer` behavior.

## Provider Rules

Supported in v1: `apt`, `snap`, `conan`, `vcpkg`, `custom-url`,
`fetchcontent`. Each entry lists acceptable providers in priority order;
`preferred` selects among them. Rules:

- Pin downloaded coordinates to immutable refs (tag + sha, digest, or
  sha256); `latest` and bare branches are rejected by the validator.
- One provider wins per package per resolution; combining two providers
  for the same package in one build fails closed with the entry name,
  attempted providers, and remediation.
- Offline mode (`--offline`) performs zero network calls; missing local
  cache entries fail with the cache path expected.
- Sibling (`fetchcontent`) entries use immutable tags plus commit SHA,
  matching `versions.yaml` matrix rules.

## Compatibility Rules

- Additive manifest fields only within major `0.x` minors; renames go
  through deprecation (old + new accepted, warning emitted) for one minor.
- `1.0.0` freezes the schema; providers may be added without breaking it.
- Backend version policy stays owned by `neuriplo`; the manifest consumes
  it. Task semantics stay owned by `neuriplo-tasks`.

## Validation Strategy

- Schema validator in the manager repo runs on every consumer `deps.yaml` /
  `deps.lock` pair; platform CI checks the golden fixtures resolve and the
  four existing `versions.env` files import losslessly.
- `status` exit codes: `0` clean, `2` updates available, `1` error/drift.
- Evidence: lockfile + generated `versions.env` + `status` report attached
  to the consumer PR that bumps them.

## Examples

Minimal apt-only project (`videocapture` first integration):

```yaml
schema_version: 1
packages:
  - {name: opencv, kind: system-library, wanted: "==4.6.0",
     providers: [apt], package: "libopencv-dev"}
```

Backend binary plus sibling (abbreviated `neuriplo-infer` shape):

```yaml
schema_version: 1
packages:
  - {name: onnxruntime-gpu, kind: backend-binary, wanted: "==1.19.2",
     providers: [custom-url], url: "https://...", sha256: "<64-hex>"}
  - {name: neuriplo, kind: sibling, wanted: "v0.10.0",
     providers: [fetchcontent], repo: "olibartfast/neuriplo", ref: "<sha>"}
```
