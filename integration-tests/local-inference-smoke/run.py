#!/usr/bin/env python3
"""Local smoke check for the vision platform checkout cluster."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency check path
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc

ROOT = Path(__file__).resolve().parents[2]
REPOS_ROOT = ROOT.parent


def load_versions() -> dict[str, Any]:
    with (ROOT / "versions.yaml").open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def require_git_ref(repo: Path, ref: str) -> None:
    result = run(["git", "rev-parse", "--verify", ref], repo)
    if result.returncode != 0:
        raise RuntimeError(f"{repo.name}: missing git ref {ref}\n{result.stdout}")


def require_commit(repo: Path, commit: str) -> None:
    result = run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], repo)
    if result.returncode != 0:
        raise RuntimeError(f"{repo.name}: missing commit {commit}\n{result.stdout}")


def require_tag_points_at(repo: Path, tag: str, ref: str) -> None:
    result = run(["git", "rev-parse", "--verify", f"{tag}^{{commit}}"], repo)
    if result.returncode != 0:
        raise RuntimeError(f"{repo.name}: cannot resolve tag {tag}\n{result.stdout}")
    resolved = result.stdout.strip()
    if resolved != ref:
        raise RuntimeError(
            f"{repo.name}: tag {tag} resolves to {resolved}, but versions.yaml pins {ref}"
        )


def validate_repositories(versions: dict[str, Any]) -> None:
    for name, meta in versions["repositories"].items():
        repo = REPOS_ROOT / name
        if not repo.is_dir():
            raise RuntimeError(f"missing local repository: {repo}")
        version = str(meta["version"])
        ref = str(meta["ref"])
        if version == "wip":
            require_commit(repo, ref)
        else:
            require_git_ref(repo, version)
            require_commit(repo, ref)
            require_tag_points_at(repo, version, ref)


def validate_runner(preset: str) -> None:
    neuriplo_infer = REPOS_ROOT / "neuriplo-infer"
    runner = neuriplo_infer / "docker_run_inference_e2e_example.sh"
    if not runner.is_file():
        raise RuntimeError(f"missing app-owned E2E runner: {runner}")

    list_result = run(["bash", str(runner), "--list-presets"], neuriplo_infer)
    if list_result.returncode != 0:
        raise RuntimeError(f"failed to list presets\n{list_result.stdout}")
    if preset not in list_result.stdout.splitlines():
        raise RuntimeError(f"preset {preset!r} not listed by app-owned runner")

    dry_run = run(
        [
            "bash",
            str(runner),
            "--preset",
            preset,
            "--dry-run",
            "--neuriplo-tasks-dir",
            str(REPOS_ROOT / "neuriplo-tasks"),
            "--skip-export",
            "--skip-convert",
        ],
        neuriplo_infer,
    )
    if dry_run.returncode != 0:
        raise RuntimeError(f"dry-run failed for preset {preset}\n{dry_run.stdout}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", default="owlv2")
    args = parser.parse_args()

    try:
        versions = load_versions()
        validate_repositories(versions)
        validate_runner(args.preset)
    except Exception as exc:  # pragma: no cover - top-level CLI reporting
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("local inference smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
