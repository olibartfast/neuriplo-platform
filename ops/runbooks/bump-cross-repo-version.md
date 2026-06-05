# Bump Cross-Repo Version Runbook

Use this when updating `versions.yaml` after a sibling repo publishes a compatible
release or needs a temporary WIP commit pin.

## Goal

Record a known-good ecosystem version without changing runtime behavior or
duplicating repo-local dependency policy.

## Preconditions

- The changed repo is declared in `ops/CLUSTER_MAP.yaml`.
- The repo-local validation for the candidate version has passed.
- Downstream impact is understood from `dependency_edges`.
- WIP pins are temporary and use a 40-character commit SHA.

## Procedure

1. Identify the owning repo and change class.
   - Use `dependency-sync` for version matrix alignment.
   - Use `ops/runbooks/cross-repo-api-migration.md` if public contracts changed.

2. Verify the candidate ref in the sibling repo.
   - Released repos must have a `vX.Y.Z` tag.
   - WIP repos must have a reachable commit SHA.

3. Update `versions.yaml`.
   - Set `version` to the release tag or `wip`.
   - Set `ref` to the immutable commit SHA.
   - Update each compatibility set entry to match the declared version policy.

4. Check platform metadata.
   - Run `scripts/check_platform.py`.
   - Confirm no unrelated repo was added to the version matrix.

5. Run impacted integration checks when local checkouts exist.
   - For local inference changes, run `integration-tests/local-inference-smoke/run.py`.
   - For serving changes, run the serving smoke test once it exists.

6. Record PR evidence.
   - Changed repo and old/new versions.
   - Validation output.
   - Downstream repos considered.
   - Any follow-up required for WIP pins.

## Exit Criteria

- `versions.yaml` points at immutable refs.
- Compatibility set values match repository declarations.
- Platform validation passes.
- Required downstream smoke evidence is recorded or explicitly marked unavailable.
