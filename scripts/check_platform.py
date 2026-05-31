#!/usr/bin/env python3
"""Validate vision-platform control-plane metadata."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised only on missing dep
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc

ROOT = Path(__file__).resolve().parents[1]
TAG_RE = re.compile(r"^v\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_ascii(errors: list[str]) -> None:
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        try:
            path.read_text(encoding="ascii")
        except UnicodeDecodeError:
            fail(errors, f"non-ASCII content: {path.relative_to(ROOT)}")


def validate_versions(errors: list[str]) -> None:
    versions = load_yaml(ROOT / "versions.yaml")
    repos = versions.get("repositories", {})
    compat_sets = versions.get("compatibility_sets", [])

    required = {
        "vision-core",
        "neuriplo",
        "vision-inference",
        "neuriplo-kserve-runtime",
    }
    missing = sorted(required - set(repos))
    if missing:
        fail(errors, f"versions.yaml missing repositories: {', '.join(missing)}")

    for name, meta in repos.items():
        version = str(meta.get("version"))
        ref = str(meta.get("ref"))
        if version == "wip":
            if not SHA_RE.match(ref):
                fail(errors, f"{name}: WIP repository must be pinned by 40-char commit SHA")
        else:
            if not TAG_RE.match(version):
                fail(errors, f"{name}: released repository version must be a vX.Y.Z tag, got {version}")
            if not SHA_RE.match(ref):
                fail(errors, f"{name}: released repository ref must be a 40-char commit SHA")

    for compat in compat_sets:
        compat_repos = compat.get("repositories", {})
        for name, value in compat_repos.items():
            if name not in repos:
                fail(errors, f"compatibility set {compat.get('name')}: unknown repo {name}")
                continue
            declared = str(repos[name].get("version"))
            if declared == "wip":
                if not SHA_RE.match(str(value)):
                    fail(errors, f"compatibility set {compat.get('name')}: WIP {name} must use commit SHA")
            elif value != declared:
                fail(errors, f"compatibility set {compat.get('name')}: {name} uses {value}, expected {declared}")


def validate_policies(errors: list[str]) -> None:
    policies = load_yaml(ROOT / "ops" / "policies.yaml")
    branch_policy = policies.get("branch_policy", {})
    normal_targets = set(branch_policy.get("normal_work_targets", []))
    release_targets = set(branch_policy.get("release_work_targets", []))
    sibling_rules = branch_policy.get("sibling_rules", {})

    expected_normal = {"develop", "feat/*", "feature/*"}
    if normal_targets != expected_normal:
        fail(errors, f"normal_work_targets must be {sorted(expected_normal)}, got {sorted(normal_targets)}")
    if release_targets != {"master"}:
        fail(errors, f"release_work_targets must be ['master'], got {sorted(release_targets)}")
    if not sibling_rules.get("master_is_release_only"):
        fail(errors, "sibling_rules.master_is_release_only must be true")
    if sibling_rules.get("direct_master_changes_allowed"):
        fail(errors, "sibling_rules.direct_master_changes_allowed must be false")


def validate_required_docs(errors: list[str]) -> None:
    required_docs = [
        ROOT / "docs" / "architecture" / "dependency-policy.md",
        ROOT / "docs" / "architecture" / "doc-migration.md",
    ]
    for path in required_docs:
        if not path.exists():
            fail(errors, f"missing required platform doc: {path.relative_to(ROOT)}")


def validate_cluster_map(errors: list[str]) -> None:
    cluster = load_yaml(ROOT / "ops" / "CLUSTER_MAP.yaml")
    cluster_repos = set(cluster.get("repos", {}))

    for edge in cluster.get("dependency_edges", []):
        source = edge.get("from")
        target = edge.get("to")
        if source not in cluster_repos:
            fail(errors, f"CLUSTER_MAP dependency edge references unknown source repo: {source}")
        if target not in cluster_repos:
            fail(errors, f"CLUSTER_MAP dependency edge references unknown target repo: {target}")

    for repo, meta in cluster.get("repos", {}).items():
        for field in ("depends_on", "consumed_by"):
            for related in meta.get(field, []):
                if related not in cluster_repos:
                    fail(errors, f"CLUSTER_MAP {repo}.{field} references unknown repo: {related}")


def validate_repo_meta(errors: list[str]) -> None:
    cluster = load_yaml(ROOT / "ops" / "CLUSTER_MAP.yaml")
    policies = load_yaml(ROOT / "ops" / "policies.yaml")
    sibling_repos = set(policies["branch_policy"].get("sibling_repositories", []))
    cluster_repos = set(cluster.get("repos", {}))

    for repo in sorted(cluster_repos):
        meta_path = ROOT / "ops" / "repo-meta" / f"{repo}.yaml"
        if not meta_path.exists():
            fail(errors, f"missing repo metadata: {meta_path.relative_to(ROOT)}")
            continue
        meta = load_yaml(meta_path)
        if meta.get("name") != repo:
            fail(errors, f"{meta_path.relative_to(ROOT)} name must be {repo}")
        repo_root = meta.get("repo_root")
        if not repo_root:
            fail(errors, f"{repo}: repo_root is required")
        if repo in sibling_repos:
            branches = meta.get("default_branches", {})
            if branches.get("integration") != "develop":
                fail(errors, f"{repo}: integration branch must be develop")
            if branches.get("release") != "master":
                fail(errors, f"{repo}: release branch must be master")

    extra_meta = {
        path.stem for path in (ROOT / "ops" / "repo-meta").glob("*.yaml")
    } - cluster_repos
    if extra_meta:
        fail(errors, f"repo metadata not present in cluster map: {', '.join(sorted(extra_meta))}")


def validate_examples(errors: list[str]) -> None:
    examples_root = ROOT / "examples"
    for path in examples_root.iterdir():
        if not path.is_dir():
            continue
        readme = path / "README.md"
        if not readme.exists():
            fail(errors, f"example missing README.md: {path.relative_to(ROOT)}")
            continue
        text = readme.read_text(encoding="ascii")
        required_phrases = [
            "Validation status:",
            "Version set:",
            "Repositories Involved",
        ]
        for phrase in required_phrases:
            if phrase not in text:
                fail(errors, f"{readme.relative_to(ROOT)} missing required phrase: {phrase}")


def validate_integration_tests(errors: list[str]) -> None:
    tests_root = ROOT / "integration-tests"
    for path in tests_root.iterdir():
        if not path.is_dir():
            continue
        readme = path / "README.md"
        if not readme.exists():
            fail(errors, f"integration test missing README.md: {path.relative_to(ROOT)}")
            continue
        text = readme.read_text(encoding="ascii")
        required_phrases = [
            "Validation status:",
            "Version set:",
            "Owning repos:",
        ]
        for phrase in required_phrases:
            if phrase not in text:
                fail(errors, f"{readme.relative_to(ROOT)} missing required phrase: {phrase}")
        scripts = [candidate for candidate in path.iterdir() if candidate.is_file() and candidate.stat().st_mode & 0o111]
        if not scripts:
            fail(errors, f"integration test missing executable script: {path.relative_to(ROOT)}")


def main() -> int:
    errors: list[str] = []
    validate_ascii(errors)
    validate_versions(errors)
    validate_policies(errors)
    validate_cluster_map(errors)
    validate_repo_meta(errors)
    validate_required_docs(errors)
    validate_examples(errors)
    validate_integration_tests(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("platform metadata ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
