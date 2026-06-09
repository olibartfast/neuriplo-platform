#!/usr/bin/env python3
"""Report compile-speed and baseline tooling progress across sibling repos."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency check path
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class CheckResult:
    repo: str
    check_id: str
    status: str
    detail: str


@dataclass(frozen=True)
class Check:
    check_id: str
    description: str
    fn: Callable[[Path], tuple[bool, str]]


def load_cluster() -> dict:
    with (ROOT / "ops" / "CLUSTER_MAP.yaml").open("r", encoding="ascii") as handle:
        return yaml.safe_load(handle)["cluster"]


def repo_checkouts(cluster: dict) -> dict[str, Path]:
    hints = cluster.get("local_checkout_hints", {})
    checkouts: dict[str, Path] = {}
    for name, hint in hints.items():
        if name == "neuriplo-platform":
            checkouts[name] = ROOT
            continue
        checkouts[name] = (ROOT / hint).resolve()
    return checkouts


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_glob(repo: Path, pattern: str) -> str:
    chunks: list[str] = []
    for path in sorted(repo.glob(pattern)):
        if path.is_file():
            chunks.append(read_text(path))
    return "\n".join(chunks)


def file_exists(repo: Path, relative: str) -> tuple[bool, str]:
    path = repo / relative
    if path.is_file():
        return True, relative
    return False, f"missing {relative}"


def file_contains(repo: Path, relative: str, needle: str, label: str | None = None) -> tuple[bool, str]:
    path = repo / relative
    if not path.is_file():
        return False, f"missing {relative}"
    text = read_text(path)
    if needle in text:
        return True, label or f"{relative} contains {needle!r}"
    return False, f"{relative} missing {needle!r}"


def file_lacks(repo: Path, relative: str, needle: str) -> tuple[bool, str]:
    path = repo / relative
    if not path.is_file():
        return False, f"missing {relative}"
    text = read_text(path)
    if needle in text:
        return False, f"{relative} still contains {needle!r}"
    return True, f"{relative} does not include {needle!r}"


def glob_contains(repo: Path, pattern: str, needle: str) -> tuple[bool, str]:
    text = read_glob(repo, pattern)
    if not text:
        return False, f"no files matched {pattern}"
    if needle in text:
        return True, f"{pattern} contains {needle!r}"
    return False, f"{pattern} missing {needle!r}"


def check_compile_speed(repo: Path) -> tuple[bool, str]:
    ok_cmake, detail_cmake = file_exists(repo, "cmake/CompileSpeed.cmake")
    ok_wired, detail_wired = file_contains(repo, "CMakeLists.txt", "CompileSpeed.cmake")
    if ok_cmake and ok_wired:
        return True, "CompileSpeed.cmake present and wired"
    return False, f"{detail_cmake}; {detail_wired}"


def check_fetchcontent_guard(repo: Path) -> tuple[bool, str]:
    path = repo / "CMakeLists.txt"
    if not path.is_file():
        return False, "missing CMakeLists.txt"
    text = read_text(path)
    required = ["BUILD_INFERENCE_ENGINE_TESTS OFF", "BUILD_TESTS OFF", "FetchContent_MakeAvailable"]
    missing = [item for item in required if item not in text]
    if missing:
        return False, f"CMakeLists.txt missing {', '.join(missing)}"
    make_idx = text.index("FetchContent_MakeAvailable")
    tests_idx = text.index("BUILD_TESTS OFF")
    engine_idx = text.index("BUILD_INFERENCE_ENGINE_TESTS OFF")
    if make_idx < tests_idx or make_idx < engine_idx:
        return False, "FetchContent guard flags appear after FetchContent_MakeAvailable"
    return True, "FetchContent subproject tests/apps disabled before MakeAvailable"


def check_app_static_library(repo: Path) -> tuple[bool, str]:
    ok_sources, _ = file_contains(repo, "app/CMakeLists.txt", "APP_LIB_SOURCES")
    ok_static, _ = file_contains(repo, "app/CMakeLists.txt", "STATIC")
    ok_library, detail = file_contains(repo, "app/CMakeLists.txt", "add_library(", "app static library target present")
    if ok_sources and ok_static and ok_library:
        return True, "app sources compile once via static library"
    return False, detail


def check_project_is_top_level_guard(repo: Path) -> tuple[bool, str]:
    return file_contains(repo, "CMakeLists.txt", "PROJECT_IS_TOP_LEVEL")


def check_release_only_optimization(repo: Path) -> tuple[bool, str]:
    path = repo / "cmake" / "SetCompilerFlags.cmake"
    if not path.is_file():
        return False, "missing cmake/SetCompilerFlags.cmake"
    text = read_text(path)
    if "CMAKE_CXX_FLAGS_RELEASE" in text and "-O3" in text:
        return True, "Release-only optimization flags"
    if 'CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -ffast-math"' in text:
        return False, "global -O3 -ffast-math still applied to all build types"
    return False, "expected Release-only -O3 flags in SetCompilerFlags.cmake"


def check_opencv_free_result_types(repo: Path) -> tuple[bool, str]:
    candidates = sorted(repo.glob("include/**/result_types.hpp"))
    if not candidates:
        return False, "missing result_types.hpp"
    path = candidates[0]
    text = read_text(path)
    if "opencv2/" in text or "#include <opencv" in text:
        return False, f"{path.relative_to(repo)} still includes OpenCV"
    if "BoundingBox" not in text or "ImageMatrix" not in text:
        return False, f"{path.relative_to(repo)} missing BoundingBox/ImageMatrix"
    return True, f"{path.relative_to(repo)} is OpenCV-free"


def check_ninja_presets(repo: Path) -> tuple[bool, str]:
    return file_contains(repo, "CMakePresets.json", '"generator": "Ninja"')


IMPLEMENTATION_REPOS = [
    "neuriplo-tasks",
    "neuriplo",
    "neuriplo-infer",
    "neuriplo-kserve-client",
    "neuriplo-kserve-runtime",
    "videocapture",
]

CHECKS: dict[str, list[Check]] = {
    "neuriplo-tasks": [
        Check("baseline_tooling", "CompileSpeed.cmake wired", check_compile_speed),
        Check("opencv_free_results", "OpenCV-free result_types.hpp", check_opencv_free_result_types),
        Check("ci_ninja", "CI uses Ninja", lambda repo: glob_contains(repo, ".github/workflows/*.yml", "Ninja")),
        Check("ci_ccache", "CI uses ccache", lambda repo: glob_contains(repo, ".github/workflows/*.yml", "ccache")),
    ],
    "neuriplo": [
        Check("baseline_tooling", "CompileSpeed.cmake wired", check_compile_speed),
        Check("release_only_optimization", "Release-only optimization flags", check_release_only_optimization),
        Check("ci_parallel_build", "CI uses parallel builds", lambda repo: glob_contains(repo, ".github/workflows/*.yml", "--parallel")),
    ],
    "neuriplo-infer": [
        Check("baseline_tooling", "CompileSpeed.cmake wired", check_compile_speed),
        Check("fetchcontent_guard", "FetchContent guard flags", check_fetchcontent_guard),
        Check("app_static_library", "App static library target", check_app_static_library),
        Check("ci_ninja", "CI uses Ninja", lambda repo: glob_contains(repo, ".github/workflows/*.yml", "Ninja")),
        Check("ci_ccache", "CI uses ccache", lambda repo: glob_contains(repo, ".github/workflows/*.yml", "ccache")),
    ],
    "neuriplo-kserve-client": [
        Check("baseline_tooling", "CompileSpeed.cmake wired", check_compile_speed),
        Check("ci_ninja", "CI uses Ninja", lambda repo: glob_contains(repo, ".github/workflows/*.yml", "Ninja")),
        Check("ci_ccache", "CI uses ccache", lambda repo: glob_contains(repo, ".github/workflows/*.yml", "ccache")),
    ],
    "neuriplo-kserve-runtime": [
        Check("baseline_tooling", "CompileSpeed.cmake wired", check_compile_speed),
        Check("ninja_presets", "CMake presets use Ninja", check_ninja_presets),
        Check("ci_ccache", "CI uses ccache", lambda repo: glob_contains(repo, ".github/workflows/*.yml", "ccache")),
    ],
    "videocapture": [
        Check("baseline_tooling", "CompileSpeed.cmake wired", check_compile_speed),
        Check("top_level_guard", "PROJECT_IS_TOP_LEVEL guard", check_project_is_top_level_guard),
        Check("ci_parallel_build", "CI uses parallel builds", lambda repo: glob_contains(repo, ".github/workflows/*.yml", "--parallel")),
    ],
}


def evaluate_repo(repo_name: str, repo_path: Path) -> list[CheckResult]:
    results: list[CheckResult] = []
    if not repo_path.is_dir():
        for check in CHECKS[repo_name]:
            results.append(CheckResult(repo_name, check.check_id, "missing", f"checkout not found: {repo_path}"))
        return results

    for check in CHECKS[repo_name]:
        ok, detail = check.fn(repo_path)
        results.append(CheckResult(repo_name, check.check_id, "pass" if ok else "fail", detail))
    return results


def print_report(results: list[CheckResult]) -> None:
    grouped: dict[str, list[CheckResult]] = {}
    for result in results:
        grouped.setdefault(result.repo, []).append(result)

    print("component progress")
    print("")
    for repo_name in IMPLEMENTATION_REPOS:
        repo_results = grouped.get(repo_name, [])
        if not repo_results:
            continue
        if any(item.status == "missing" for item in repo_results):
            print(f"{repo_name}: missing checkout")
            continue

        passed = sum(1 for item in repo_results if item.status == "pass")
        total = len(repo_results)
        print(f"{repo_name}: {passed}/{total} checks passed")
        for item in repo_results:
            marker = "ok" if item.status == "pass" else "FAIL"
            print(f"  [{marker}] {item.check_id}: {item.detail}")
        print("")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-local",
        action="store_true",
        help="fail when any implementation checkout is missing",
    )
    args = parser.parse_args()

    cluster = load_cluster()
    checkouts = repo_checkouts(cluster)
    results: list[CheckResult] = []
    for repo_name in IMPLEMENTATION_REPOS:
        results.extend(evaluate_repo(repo_name, checkouts[repo_name]))

    print_report(results)

    missing = sorted({item.repo for item in results if item.status == "missing"})
    failed = [item for item in results if item.status == "fail"]

    if args.require_local and missing:
        print(f"component progress: missing local checkouts: {', '.join(missing)}")
        return 1

    if failed:
        print(f"component progress: {len(failed)} check(s) failed")
        return 1

    if missing:
        print(f"note: skipped missing checkouts: {', '.join(missing)}")
    else:
        print("component progress ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
