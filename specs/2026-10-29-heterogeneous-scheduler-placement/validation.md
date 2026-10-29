# Validation

Milestone: Heterogeneous hardware placement and executor-neutral scheduling

Status: Complete (2026-10-29)

## Results

### Review pass, 2026-10-29

Groups 1 to 4 verified against V-1 to V-7; Group 5 stays deferred per
the plan (needs operator-scheduled sessions and powered machines).

- V-1: `scripts/check_platform.py` passes with the packet, ADR 0014,
  placement doc, scheduler-job contract, runbook, `ops/slurm/` helper,
  and roadmap registration present; all files ASCII.
- V-2: the contract carries Owner, Consumers, Version 0.1.0, Status
  Draft, Purpose, identity/binding/evidence schema, compatibility
  rules, validation strategy, and Slurm/Kubernetes/native-runner
  examples; it is listed in `contracts/README.md`.
- V-3: privacy grep over all new files returns no hits (no tailnet,
  carrier-grade NAT, dotted-quad, hostname, or account-label patterns);
  the example inventory carries empty values only.
- V-4: packet commits (`7c81ad3`, `2b403ff`) touch platform docs, one
  contract, one runbook, `ops/slurm/`, the packet, `.gitignore`, and
  roadmap/ADR-index edits only; no `versions.yaml` pin, no
  compatibility set, no owning-repo branch.
- V-5: the placement doc states the GGML/TVM placeholder limit and the
  CPU-recipe limit explicitly; no GPU-variant build, packaging, or
  distribution step is introduced anywhere.
- V-6: reader check passes -- the profile table maps each backend to
  its profiles, the on-demand policy states no purchase is recommended
  and offline means planned/on-demand rather than failed.
- V-7: reader check passes -- the Slurm and Kubernetes examples share
  one job identity with different bindings and an unchanged evidence
  envelope; the native-runner example covers `P-WIN-CPU`.
- Tool check: `ops/slurm/render_bindings.py` runs exit 0 against the
  example inventory (all profiles unassigned/planned, partitions with
  no online nodes); one canonical-ID comment fix (`P-WIN-CPU`).

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
