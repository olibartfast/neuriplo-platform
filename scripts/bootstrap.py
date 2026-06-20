#!/usr/bin/env python3
"""Bootstrap the neuriplo-platform development environment.

Clones all sibling repositories at the versions pinned in versions.yaml and
validates the checkout cluster with check_platform.py.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def run(cmd: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def git_clone(url: str, dest: Path) -> bool:
    print(f"  Cloning {url} -> {dest}")
    result = run(["git", "clone", url, str(dest)], ROOT.parent, check=False)
    if result.returncode != 0:
        print(f"    ERROR: {result.stdout.strip()}")
        return False
    return True


def git_fetch(repo: Path) -> bool:
    result = run(["git", "fetch", "--tags", "origin"], repo, check=False)
    if result.returncode != 0:
        print(f"    WARNING: fetch failed for {repo.name}: {result.stdout.strip()}")
        return False
    return True


def git_checkout(repo: Path, ref: str) -> bool:
    result = run(["git", "checkout", "--detach", ref], repo, check=False)
    if result.returncode != 0:
        print(f"    ERROR checking out {ref} in {repo.name}: {result.stdout.strip()}")
        return False
    return True


def git_current_sha(repo: Path) -> str:
    result = run(["git", "rev-parse", "HEAD"], repo)
    return result.stdout.strip()


def resolve_clone_url(name: str, org: str, use_ssh: bool) -> str:
    if use_ssh:
        return f"git@github.com:{org}/{name}.git"
    return f"https://github.com/{org}/{name}.git"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap the neuriplo development environment"
    )
    parser.add_argument(
        "--org",
        default="olibartfast",
        help="GitHub organization for sibling repos (default: olibartfast)",
    )
    parser.add_argument(
        "--ssh",
        action="store_true",
        dest="use_ssh",
        help="Use SSH instead of HTTPS for cloning",
    )
    parser.add_argument(
        "--skip-clone",
        action="store_true",
        help="Skip cloning; only checkout pinned versions in existing repos",
    )
    parser.add_argument(
        "--skip-validate",
        action="store_true",
        help="Skip platform validation after checkout",
    )
    args = parser.parse_args()

    versions = load_yaml(ROOT / "versions.yaml")
    pinned = versions.get("repositories", {})

    # Exclude neuriplo-platform itself (already cloned)
    sibling_repos = {
        name: meta
        for name, meta in pinned.items()
        if name != "neuriplo-platform"
    }

    errors: list[str] = []
    ok: list[str] = []
    cloned: list[str] = []
    already_ok: list[str] = []

    for name, meta in sibling_repos.items():
        dest = ROOT.parent / name
        ref = str(meta["ref"])
        version = str(meta.get("version", ""))

        print(f"\n[{name}] version={version} ref={ref[:8]}")

        if not dest.is_dir():
            if args.skip_clone:
                errors.append(f"{name}: missing and --skip-clone set")
                continue
            url = resolve_clone_url(name, args.org, args.use_ssh)
            if not git_clone(url, dest):
                errors.append(f"{name}: clone failed")
                continue
            cloned.append(name)
        else:
            if not args.skip_clone:
                git_fetch(dest)
            current = git_current_sha(dest)
            if current == ref:
                already_ok.append(name)
                print(f"  Already at {ref[:8]}")
                continue

        if not git_checkout(dest, ref):
            errors.append(f"{name}: checkout failed")
            continue

        final_sha = git_current_sha(dest)
        if final_sha != ref:
            errors.append(f"{name}: expected {ref[:8]}, got {final_sha[:8]}")
            continue

        ok.append(name)

    print("\n" + "=" * 50)
    if ok:
        print(f"Checked out {len(ok)} repos: {', '.join(ok)}")
    if already_ok:
        print(f"Already at target: {', '.join(already_ok)}")
    if cloned:
        print(f"Cloned {len(cloned)} repos: {', '.join(cloned)}")

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    if not args.skip_validate:
        print("\nValidating platform metadata...")
        validator = ROOT / "scripts" / "check_platform.py"
        result = run([sys.executable, str(validator)], ROOT, check=False)
        print(result.stdout)
        if result.returncode != 0:
            return 1

    print("\nPlatform checkout cluster is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
