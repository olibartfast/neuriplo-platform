# CI Triage Runbook

Use this when CI fails in any repo in the platform cluster.

## Goal

Classify the failure, contain the scope, and produce the smallest safe PR that
restores expected build or test behavior.

## Inputs

- Failing workflow name and job name.
- Failing commit or PR.
- Relevant log excerpt.
- Target repo metadata from `ops/repo-meta/*.yaml`.

## Procedure

1. Identify the owning repo and failure class.
   - build configuration
   - compile or link failure
   - unit or integration test failure
   - dependency or version drift
   - flaky or environment-sensitive test

2. Check whether the failure is local or downstream.
   - If a source repo changed a contract, treat the consumer fix as a downstream API migration.
   - If the failure is isolated to one repo, keep the PR in that repo only.

3. Validate against `ops/policies.yaml`.
   - If the needed change is forbidden, stop and escalate to a human.

4. Reproduce with the repo-local commands from the relevant `repo-meta` file.

5. Implement the smallest repair.
   - Prefer test repair, docs sync, or mechanical wiring updates.
   - Do not widen scope into unrelated cleanup.

6. Run repo-local validation.

7. If a public contract or dependency edge is implicated, run downstream validation.

8. Open a PR using `ops/PR_EVIDENCE_TEMPLATE.md`.

## Exit Criteria

- Failure reproduced or clearly classified as non-reproducible.
- Change class allowed.
- Smallest fix implemented.
- Evidence collected.
- PR target follows branch policy.
