# Faster Compilation Runbook

Cross-repository guidance for reducing C++ compile time across the neuriplo
platform. Repo-local build commands stay in each repository's README and
`ops/repo-meta/*.yaml`.

## Scope

| Repository | Role | Primary compile cost |
|------------|------|----------------------|
| vision-core | Task contracts | Single large library + many test binaries |
| neuriplo | Backend abstraction | Backend SDK headers, per-backend CI matrix |
| vision-inference | Local application | FetchContent siblings, duplicated app sources |
| neuriplo-kserve-runtime | Serving runtime | Small runtime tree; optional real-neuriplo preset |
| videocapture | Video I/O | Small library; avoid building app/tests as subproject |

## Baseline Tooling (all repos)

Each implementation repository should support this local profile:

```bash
cmake -S . -B build-fast -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER_LAUNCHER=ccache
cmake --build build-fast --parallel
```

`cmake/CompileSpeed.cmake` enables ccache automatically when installed and
`-DCMAKE_CXX_COMPILER_LAUNCHER` is not already set.

CI should prefer:

- Ninja generator
- `ccache-action` (or sccache for cross-runner cache sharing)
- `cmake --build ... --parallel`

## Repository-Specific Rules

### vision-inference

- FetchContent siblings must not build subproject tests or sample apps:
  `BUILD_INFERENCE_ENGINE_TESTS=OFF` and `BUILD_TESTS=OFF` before
  `FetchContent_MakeAvailable`.
- App sources compile once via `vision-inference-app` static library; tests link
  the library instead of recompiling app `.cpp` files.
- See `vision-inference/docs/FasterCompilationPlan.md` for phased experiments
  (PCH, unity builds, faster linkers).

### videocapture

- `PROJECT_IS_TOP_LEVEL` guards sample app and test subdirectories.
- When fetched by vision-inference, only the `VideoCapture` shared library
  should build.

### neuriplo

- Release-only optimization: `-O3 -ffast-math` applies to `Release` builds
  only (`cmake/SetCompilerFlags.cmake`).
- Avoid `--clean-first` in CI when separate build directories are available.

### vision-core

- CI already uses ccache; prefer Ninja in configure steps.
- `result_types.hpp` is OpenCV-free: use `BoundingBox`, `ImageMatrix`, and
  `opencv_interop.hpp` at rendering or postprocess boundaries.
- Longer-term: consolidate test executables into fewer gtest binaries.

### neuriplo-kserve-runtime

- CMake presets use Ninja.
- `real-onnx` preset is the largest compile profile because it embeds neuriplo.

## Measurement Before Further Changes

Record for each repo before adopting PCH, unity builds, or include refactors:

1. Clean configure + build time
2. Single-file incremental rebuild time
3. Link time (if dominant, try mold or lld)
4. `ccache -s` hit rate after warmup

## Procedure

1. Measure the current clean and incremental build times for the target repo.
2. Apply baseline tooling first: Ninja, parallel builds, and ccache when available.
3. Remove unnecessary subproject targets when a repo is fetched as a dependency.
4. Eliminate duplicate source compilation across app and test targets.
5. Restrict aggressive optimization flags to release profiles only.
6. Re-run repo-local validation and record before/after timings in PR evidence.
7. If compile time is still high, follow repo-specific follow-up priorities below.

## PR Evidence

Compile-speed PRs must include:

- before/after timings
- configure, build, and test commands
- confirmation that inference semantics, output schema, CLI flags, and backend
  fallback behavior are unchanged

Use `ops/PR_EVIDENCE_TEMPLATE.md` for cross-repo maintenance work.

## Follow-Up Priorities

1. Consolidate vision-core test executables into fewer gtest binaries.
3. Prebuilt sibling packages instead of FetchContent clones in vision-inference.
4. Share ccache across neuriplo backend matrix jobs in CI.
