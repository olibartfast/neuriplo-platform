# Validation

Milestone: Heterogeneous hardware placement and executor-neutral scheduling

Status: Specified, not implemented

Written before implementation. Each check names the requirement it closes.

## Automated Checks

- V-1 (R-7): `scripts/check_platform.py` passes with the new packet, ADR,
  architecture doc, contract, and runbook present; all new files are ASCII.
- V-2 (R-4, R-7): The new contract follows the contract template (Owner,
  Consumers, Version, Status, Purpose, schema, compatibility rules,
  validation strategy, examples) and is listed in `contracts/README.md`.

## Negative Checks

- V-3 (R-6): No tracked file names a personal IP, hostname, machine name,
  account label, machine identifier, credential, or private local path.
  Check: `grep -rEi 'ts\.net|100\.(64|6[5-9]|[78][0-9]|9[0-9]|1[0-1][0-9]|12[0-7])\.'`
  over the new/edited files returns no hits, and a reviewer confirms no
  hostnames, account labels, or private paths. Version-like numbers
  (for example `11.2.1.2`) are allowlisted only when they are backend
  versions, never addresses.
- V-4 (R-8 and out of scope): The packet changes no owning-repo branch, no
  `versions.yaml` pin, no compatibility set, and no in-flight campaign
  scope; `git status` shows platform docs, one contract, one runbook, the
  packet, `.gitignore`, and roadmap/ADR-index edits only.
- V-5 (R-3): No build, packaging, or distribution step for GPU variants of
  placeholder-output backends (GGML, TVM) is introduced anywhere in the
  packet; the architecture doc states the placeholder limit explicitly.

## Manual / Attested Checks

- V-6 (R-1, R-2, R-5): A reader unfamiliar with the private fleet can tell
  from the architecture doc alone which generic profile validates which
  backend, why no purchase is recommended, and that offline means
  planned/on-demand rather than failed.
- V-7 (R-4): A reader can express the same validation job for Slurm and
  for Kubernetes using only the executor-neutral contract fields, without
  executor-specific flags leaking into the job identity or the evidence
  envelope.

## Definition Of Done

V-1 to V-7 pass with dated evidence, the contract is `Draft` at version
`0.1.0`, the ADR is `Accepted`, the roadmap `Now` entry for this packet is
marked complete, and no private operator detail appears in any tracked
file.
