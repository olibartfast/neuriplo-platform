# videocapture Modern C++ Pattern Review

Reviewed on: 2026-06-03

Remote: https://github.com/olibartfast/videocapture

Reviewed ref: `develop` at `240c7761063616bf83243165a6b812df3409d6ed`

## Scope

This review considers the video I/O layer against the modern pattern guidance,
especially Adapter, Strategy, Factory, backend selection, and vendor boundary
isolation.

Key files inspected remotely with `gh`:

- `CMakeLists.txt`
- `Readme.md`
- `include/VideoCaptureFactory.hpp`
- `src/VideoCaptureFactory.cpp`

## Pattern Alignment

- Video backends are isolated behind `VideoCaptureInterface`.
- `VideoCaptureFactory` selects between OpenCV, GStreamer, and FFmpeg adapters.
- The documented backend priority is explicit: FFmpeg, then GStreamer, then
  OpenCV.

## Findings

### Medium: Backend selection is compile-time only

`VideoCaptureFactory.cpp` chooses the backend with preprocessor conditionals. The
approach is simple, but it prevents runtime backend selection when multiple
backends are compiled in.

Recommendation: keep compile-time inclusion flags, but choose the active backend
through an explicit runtime factory option when both FFmpeg and GStreamer are
available.

### Low: CMake has a typo in module path construction

`CMakeLists.txt` appends `${CMAKE_CURRENT_LIST_DIR}/cmake}` with an extra `}`.
If this path is relied on, module discovery can fail or become confusing.

Recommendation: fix the path to `${CMAKE_CURRENT_LIST_DIR}/cmake`.

## Recommended Next Actions

1. Preserve the current backend priority as the default behavior.
2. Add runtime backend selection only if consumers need it; otherwise document
   that backend choice is a build-time policy.
3. Keep FFmpeg and GStreamer APIs behind adapters so application code never
   depends on vendor-specific types.
