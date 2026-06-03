# Modern C++ Pattern Reviews

Reviewed on: 2026-06-03

These reviews compare each vision-platform related repository against the
modern C++ and architecture patterns described in:

`/home/oli/Downloads/modern_cpp_design_patterns_beyond_gof.md`

Remote metadata was checked with `gh`. Source files were inspected on the
integration branch where available:

- `vision-core`: `develop`
- `neuriplo`: `develop`
- `vision-inference`: `develop`
- `videocapture`: `develop`
- `tritonic`: `develop`
- `neuriplo-kserve-runtime`: `master` because no `develop` or `dev` branch was
  visible
- `vision-platform`: `main` because no `develop` branch was visible

## Repository Reviews

- [vision-core](vision-core.md)
- [neuriplo](neuriplo.md)
- [vision-inference](vision-inference.md)
- [videocapture](videocapture.md)
- [neuriplo-kserve-runtime](neuriplo-kserve-runtime.md)
- [tritonic](tritonic.md)
- [vision-platform](vision-platform.md)

## Cross-Repository Priorities

1. Fix RAII and lifetime issues in `tritonic`.
2. Fix timeout and registry concurrency issues in `neuriplo-kserve-runtime`.
3. Reconcile platform metadata with actual remote branches and tracked
   consumers.
4. Update platform architecture docs to include modern non-GoF patterns used by
   inference and serving systems.
