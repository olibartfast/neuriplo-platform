#!/usr/bin/env python3
"""Generate the Neuriplo compatibility report for a compatibility set.

The report is the platform's evidence that a pinned set of independently
versioned repositories works together. It distinguishes two classes of checks:

  metadata CI  - executed here, on any runner, with no GPU or C++ tooling:
                   * pinned ref integrity (the version tag resolves to the
                     40-char commit SHA recorded in versions.yaml)
                   * version consistency between the matrix and the set
                   * benchmark baseline files conform to the benchmarking
                     contract conformance shape (delegated to check_benchmark)
                   * result contract presence and baseline drift checks
  attested     - require GPU/C++ tooling (configure, build, unit tests,
                   inference smoke). Platform CI does NOT run these. They are
                   attested in a structured evidence file, which this script
                   validates and renders.

Output is deterministic (no wall-clock timestamp) so CI can regenerate the
report and fail when the committed copy is stale.

Usage:
  scripts/generate_compat_report.py                  # write latest.md + .json
  scripts/generate_compat_report.py --check          # CI: fail if stale or FAIL
  scripts/generate_compat_report.py --offline        # skip ref reachability
  scripts/generate_compat_report.py --compat-set NAME
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
# Importing the sibling validator must not leave __pycache__ artifacts behind,
# which would fail the platform's ASCII-only content scan.
sys.dont_write_bytecode = True

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised only on missing dep
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc

from check_benchmark import validate_document as validate_benchmark_doc  # noqa: E402

ROOT = SCRIPTS_DIR.parent
SHA_SHORT = 8
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EVIDENCE_STATUSES = {"pass", "fail", "skipped", "not_attested"}
ATTESTED_CHECK_KEYS = [
    "configure",
    "build",
    "unit_tests",
    "local_embedded_smoke",
    "kserve_grpc_smoke",
]
CHECK_LABELS = {
    "configure": "Configure",
    "build": "Build",
    "unit_tests": "Unit tests",
    "local_embedded_smoke": "Local embedded inference smoke test",
    "kserve_grpc_smoke": "KServe gRPC inference smoke test",
}


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="ascii") as handle:
        return yaml.safe_load(handle)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="ascii"))


class ReachabilityError(Exception):
    """Raised when git ls-remote cannot resolve a repository/tag."""


def resolve_tag_commit(url: str, tag: str) -> str | None:
    """Return the commit SHA a version tag points at, or None if the tag is absent.

    Uses `git ls-remote --tags`, which prints a dereferenced commit line
    (`refs/tags/<tag>^{}`) for annotated tags and a plain line for lightweight
    tags. No checkout or object download is performed.
    """
    try:
        completed = subprocess.run(
            ["git", "ls-remote", "--tags", url],
            check=True,
            capture_output=True,
            text=True,
            timeout=90,
        )
    except FileNotFoundError as exc:
        raise ReachabilityError("git is not installed") from exc
    except subprocess.CalledProcessError as exc:
        raise ReachabilityError((exc.stderr or exc.stdout or "").strip() or "git error") from exc
    except subprocess.TimeoutExpired as exc:
        raise ReachabilityError("git ls-remote timed out") from exc

    plain = f"refs/tags/{tag}"
    deref = f"refs/tags/{tag}^{{}}"
    plain_sha: str | None = None
    for line in completed.stdout.splitlines():
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        sha, ref = parts
        if ref == deref:
            return sha
        if ref == plain:
            plain_sha = sha
    return plain_sha


def choose_target_set(versions: dict[str, Any], requested: str | None) -> dict[str, Any]:
    sets = versions.get("compatibility_sets", [])
    if not sets:
        raise SystemExit("versions.yaml defines no compatibility_sets")
    if requested:
        for item in sets:
            if item.get("name") == requested:
                return item
        raise SystemExit(f"compatibility set not found: {requested}")
    for item in sets:
        if item.get("status") == "active":
            return item
    return sets[0]


def validate_evidence(
    errors: list[str], path: Path, set_name: str
) -> dict[str, Any] | None:
    if not path.is_file():
        errors.append(f"{set_name}: evidence file not found: {path.relative_to(ROOT)}")
        return None
    evidence = load_yaml(path)
    if not isinstance(evidence, dict):
        errors.append(f"{path.relative_to(ROOT)}: top level must be a mapping")
        return None
    if evidence.get("compatibility_set") != set_name:
        errors.append(
            f"{path.relative_to(ROOT)}: compatibility_set must be {set_name!r}, "
            f"got {evidence.get('compatibility_set')!r}"
        )
    last = str(evidence.get("last_attested", ""))
    if not DATE_RE.match(last):
        errors.append(f"{path.relative_to(ROOT)}: last_attested must be YYYY-MM-DD, got {last!r}")
    checks = evidence.get("checks", {})
    if not isinstance(checks, dict):
        errors.append(f"{path.relative_to(ROOT)}: checks must be a mapping")
        return evidence
    for key in ATTESTED_CHECK_KEYS:
        entry = checks.get(key)
        if entry is None:
            errors.append(f"{path.relative_to(ROOT)}: missing attested check {key}")
            continue
        status = entry.get("status") if isinstance(entry, dict) else None
        if status not in EVIDENCE_STATUSES:
            errors.append(
                f"{path.relative_to(ROOT)}: checks.{key}.status must be one of "
                f"{sorted(EVIDENCE_STATUSES)}, got {status!r}"
            )
    return evidence


def attested_row(evidence: dict[str, Any] | None, key: str) -> dict[str, Any]:
    if evidence is None:
        return {"status": "not_attested", "detail": "no evidence file", "last": ""}
    checks = evidence.get("checks", {}) if isinstance(evidence, dict) else {}
    entry = checks.get(key) or {}
    return {
        "status": entry.get("status", "not_attested"),
        "detail": (entry.get("detail") or "").strip().replace("\n", " "),
        "last": str(evidence.get("last_attested") or ""),
    }


def render_attested_result(row: dict[str, Any]) -> str:
    status = row["status"]
    last = f" ({row['last']})" if row["last"] and status in {"pass", "fail"} else ""
    if status == "pass":
        return f"pass{last}"
    if status == "fail":
        return f"fail{last}"
    if status == "skipped":
        return "skipped"
    return "not attested"


def metric_cell(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


def build_report(
    versions: dict[str, Any],
    target: dict[str, Any],
    evidence: dict[str, Any] | None,
    evidence_errors: list[str],
    offline: bool,
) -> dict[str, Any]:
    org = versions.get("platform", {}).get("github_org")
    if not org:
        raise SystemExit("versions.yaml: platform.github_org is required")
    repos = versions.get("repositories", {})
    set_name = target["name"]
    url_base = f"https://github.com/{org}"

    # --- repository ref integrity -------------------------------------------
    repo_rows: list[dict[str, Any]] = []
    repo_failures: list[str] = []
    for name, set_version in target.get("repositories", {}).items():
        meta = repos.get(name, {})
        version = str(meta.get("version", ""))
        ref = str(meta.get("ref", ""))
        url = f"{url_base}/{name}"
        row = {
            "name": name,
            "url": url,
            "version": version,
            "set_version": str(set_version),
            "ref": ref,
            "ref_short": ref[:SHA_SHORT],
            "tag_ref": "skipped",
            "status": "skipped (offline)",
        }
        if version != str(set_version):
            row.update(tag_ref="FAIL", status=f"FAIL: set pins {set_version}, matrix pins {version}")
            repo_failures.append(f"{name}: set pins {set_version}, matrix pins {version}")
        if not offline:
            try:
                commit = resolve_tag_commit(url, version)
            except ReachabilityError as exc:
                row.update(tag_ref="FAIL", status=f"FAIL: unreachable ({exc})")
                repo_failures.append(f"{name}: unreachable ({exc})")
            else:
                if commit is None:
                    row.update(tag_ref="missing", status=f"FAIL: tag {version} not found")
                    repo_failures.append(f"{name}: tag {version} not found")
                elif commit != ref:
                    row.update(
                        tag_ref="mismatch",
                        status=f"FAIL: tag resolves to {commit[:SHA_SHORT]}, matrix pins {ref[:SHA_SHORT]}",
                    )
                    repo_failures.append(f"{name}: tag {version} resolves to {commit}, matrix pins {ref}")
                else:
                    row.update(tag_ref="yes", status="verified")
        repo_rows.append(row)

    clone_status = "verified"
    if offline:
        clone_status = "skipped (offline)"
    elif repo_failures:
        clone_status = "FAIL"

    # --- benchmark baseline schema + result contract drift ------------------
    schema_errors: list[str] = []
    result_errors: list[str] = []
    result_contract = ROOT / "contracts" / "result-contract.md"
    if not result_contract.is_file():
        result_errors.append("contracts/result-contract.md missing")

    summary_rows: list[dict[str, Any]] = []
    for baseline in target.get("benchmark_baselines", []) or []:
        rel = baseline.get("file")
        scenario = baseline.get("scenario", "?")
        if not rel:
            schema_errors.append(f"{set_name}: baseline missing file: {scenario}")
            continue
        path = (ROOT / str(rel)).resolve()
        try:
            path.relative_to(ROOT)
        except ValueError:
            schema_errors.append(f"{set_name}: baseline escapes repo: {rel}")
            continue
        if not path.is_file():
            schema_errors.append(f"{set_name}: baseline file not found: {rel}")
            continue
        try:
            doc = load_json(path)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            schema_errors.append(f"{rel}: invalid JSON: {exc}")
            continue
        validate_benchmark_doc(schema_errors, rel, doc)
        if not isinstance(doc, dict):
            continue
        declared_set = doc.get("compatibility_set")
        if declared_set != set_name:
            result_errors.append(f"{rel}: compatibility_set {declared_set!r} != set {set_name!r}")
        backend = doc.get("backend", {})
        for index, result in enumerate(doc.get("results", []) or []):
            metrics = result.get("metrics", {}) if isinstance(result, dict) else {}
            summary_rows.append(
                {
                    "scenario": result.get("scenario", scenario),
                    "backend": backend.get("name", "-"),
                    "transport": result.get("transport", "-") if isinstance(result, dict) else "-",
                    "batch_size": result.get("batch_size") if isinstance(result, dict) else "-",
                    "p50": metrics.get("latency_p50_ms"),
                    "p95": metrics.get("latency_p95_ms"),
                    "p99": metrics.get("latency_p99_ms"),
                    "throughput": metrics.get("requests_per_second"),
                }
            )

    benchmark_schema_status = "verified" if not schema_errors else "FAIL"
    result_contract_status = "verified" if not result_errors else "FAIL"

    attested = {key: attested_row(evidence, key) for key in ATTESTED_CHECK_KEYS}
    last_attested = str((evidence or {}).get("last_attested", "")) if isinstance(evidence, dict) else ""

    return {
        "set_name": set_name,
        "status": target.get("status", ""),
        "org": org,
        "evidence_rel": target.get("evidence", ""),
        "last_attested": last_attested,
        "repo_rows": repo_rows,
        "clone_status": clone_status,
        "repo_failures": repo_failures,
        "benchmark_schema_status": benchmark_schema_status,
        "benchmark_schema_errors": schema_errors,
        "result_contract_status": result_contract_status,
        "result_contract_errors": result_errors,
        "attested": attested,
        "evidence_errors": evidence_errors,
        "summary_rows": summary_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# Neuriplo Compatibility Report")
    lines.append("")
    lines.append(f"Compatibility set: `{report['set_name']}`")
    lines.append(f"Status: `{report['status']}`")
    if report["evidence_rel"]:
        lines.append(
            f"Attested evidence: `{report['evidence_rel']}`"
            + (f" (last attested {report['last_attested']})" if report["last_attested"] else "")
        )
    lines.append("")
    lines.append(
        "Generated by `scripts/generate_compat_report.py`. Deterministic: this "
        "file is regenerated by CI and must match the committed copy exactly."
    )
    lines.append("")
    lines.append(
        "`metadata CI` checks run here on every change (ref integrity, version "
        "consistency, contract and baseline schema). `attested` checks require "
        "GPU/C++ tooling and are recorded in the evidence file above; platform "
        "CI validates the attestation, it does not re-run the checks."
    )
    lines.append("")

    lines.append("## Repositories")
    lines.append("")
    lines.append("| Repository | Version | Pinned ref | Tag resolves to ref | Status |")
    lines.append("|---|---:|---|---|---|")
    for row in report["repo_rows"]:
        lines.append(
            f"| [{row['name']}]({row['url']}) | `{row['version']}` | "
            f"`{row['ref_short']}` | {row['tag_ref']} | {row['status']} |"
        )
    lines.append("")

    lines.append("## Checks")
    lines.append("")
    lines.append("| Check | Source | Result |")
    lines.append("|---|---|---|")
    lines.append(f"| Clone pinned refs | metadata CI | {report['clone_status']} |")
    for key in ATTESTED_CHECK_KEYS:
        rendered = render_attested_result(report["attested"][key])
        lines.append(f"| {CHECK_LABELS[key]} | attested | {rendered} |")
    lines.append(
        f"| Result contract validation | metadata CI | {report['result_contract_status']} |"
    )
    lines.append(
        f"| Benchmark schema validation | metadata CI | {report['benchmark_schema_status']} |"
    )
    lines.append("")

    if report["repo_failures"] or report["benchmark_schema_errors"] or report["result_contract_errors"]:
        lines.append("## Failures")
        lines.append("")
        for failure in report["repo_failures"] + report["benchmark_schema_errors"] + report["result_contract_errors"]:
            lines.append(f"- {failure}")
        lines.append("")

    lines.append("## Benchmark Summary")
    lines.append("")
    lines.append(
        "Source: declared baseline files. Metric cells are `-` until a measured "
        "run is published under `results/` for this compatibility set."
    )
    lines.append("")
    lines.append("| Scenario | Backend / Transport | Batch | P50 | P95 | P99 | Throughput (req/s) |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for row in report["summary_rows"]:
        backend = f"{row['backend']} / {row['transport']}" if row["transport"] != "-" else row["backend"]
        lines.append(
            f"| `{row['scenario']}` | {backend} | {row['batch_size']} | "
            f"{metric_cell(row['p50'])} | {metric_cell(row['p95'])} | "
            f"{metric_cell(row['p99'])} | {metric_cell(row['throughput'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_json(report: dict[str, Any]) -> str:
    payload = {
        "compatibility_set": report["set_name"],
        "status": report["status"],
        "last_attested": report["last_attested"],
        "evidence": report["evidence_rel"],
        "checks": [
            {"check": "Clone pinned refs", "source": "metadata CI", "result": report["clone_status"]},
            *[
                {
                    "check": CHECK_LABELS[key],
                    "source": "attested",
                    "result": render_attested_result(report["attested"][key]),
                    "detail": report["attested"][key]["detail"],
                }
                for key in ATTESTED_CHECK_KEYS
            ],
            {
                "check": "Result contract validation",
                "source": "metadata CI",
                "result": report["result_contract_status"],
            },
            {
                "check": "Benchmark schema validation",
                "source": "metadata CI",
                "result": report["benchmark_schema_status"],
            },
        ],
        "repositories": [
            {
                "name": row["name"],
                "version": row["version"],
                "ref": row["ref"],
                "url": row["url"],
                "tag_resolves_to_ref": row["tag_ref"],
            }
            for row in report["repo_rows"]
        ],
        "failures": {
            "clone": report["repo_failures"],
            "benchmark_schema": report["benchmark_schema_errors"],
            "result_contract": report["result_contract_errors"],
            "evidence": report["evidence_errors"],
        },
        "benchmark_summary": report["summary_rows"],
    }
    return json.dumps(payload, indent=2) + "\n"


def has_blocking_failure(report: dict[str, Any]) -> list[str]:
    """Return the list of blocking failures (empty == ok to promote)."""
    blockers: list[str] = []
    if report["clone_status"] == "FAIL":
        blockers.append("Clone pinned refs failed")
    if report["benchmark_schema_status"] == "FAIL":
        blockers.append("Benchmark schema validation failed")
    if report["result_contract_status"] == "FAIL":
        blockers.append("Result contract validation failed")
    for key in ATTESTED_CHECK_KEYS:
        if report["attested"][key]["status"] == "fail":
            blockers.append(f"{CHECK_LABELS[key]} attested as fail")
    return blockers


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compat-set", help="compatibility set name (default: first active)")
    parser.add_argument("--offline", action="store_true", help="skip pinned-ref reachability")
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write; fail if the committed report is stale or any check FAILs",
    )
    args = parser.parse_args(argv)

    versions = load_yaml(ROOT / "versions.yaml")
    target = choose_target_set(versions, args.compat_set)
    set_name = target["name"]

    evidence_errors: list[str] = []
    evidence: dict[str, Any] | None = None
    evidence_rel = target.get("evidence")
    if evidence_rel:
        evidence = validate_evidence(evidence_errors, (ROOT / str(evidence_rel)).resolve(), set_name)

    report = build_report(versions, target, evidence, evidence_errors, args.offline)
    markdown = render_markdown(report)
    blob = render_json(report)

    report_dir = None
    if evidence_rel:
        report_dir = (ROOT / str(evidence_rel)).resolve().parent / "reports"
    elif target.get("benchmark_baselines"):
        first = (ROOT / str(target["benchmark_baselines"][0]["file"])).resolve().parent
        report_dir = first.parent / "reports"
    if report_dir is None:
        raise SystemExit(f"compatibility set {set_name}: no evidence or baseline path to locate reports/")

    md_path = report_dir / "latest.md"
    json_path = report_dir / "latest.json"

    blockers = has_blocking_failure(report) + evidence_errors

    if args.check:
        stale_files: list[str] = []
        for path, content in ((md_path, markdown), (json_path, blob)):
            if path.is_file():
                if path.read_text(encoding="ascii") != content:
                    stale_files.append(path.relative_to(ROOT).as_posix())
            else:
                stale_files.append(path.relative_to(ROOT).as_posix())
        if stale_files:
            for rel in stale_files:
                print(
                    f"ERROR: {rel} is stale or missing; "
                    f"run: scripts/generate_compat_report.py",
                    file=sys.stderr,
                )
            blockers.append("report is stale")
        if blockers:
            for item in blockers:
                print(f"ERROR: {item}", file=sys.stderr)
            return 1
        print(f"compatibility report up to date: {md_path.relative_to(ROOT)}")
        return 0

    report_dir.mkdir(parents=True, exist_ok=True)
    md_path.write_text(markdown, encoding="ascii")
    json_path.write_text(blob, encoding="ascii")
    print(f"wrote {md_path.relative_to(ROOT)}")
    print(f"wrote {json_path.relative_to(ROOT)}")
    if blockers:
        for item in blockers:
            print(f"ERROR: {item}", file=sys.stderr)
        return 1
    verified = sum(1 for r in report["repo_rows"] if r["status"] == "verified")
    print(f"ref integrity: {verified}/{len(report['repo_rows'])} repos verified")
    print("compatibility report ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
