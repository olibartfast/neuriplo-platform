# Plan

Milestone: Heterogeneous hardware placement and executor-neutral scheduling

Status: Specified, not implemented

Each group is independently implementable, reviewable, and ends in an
observable result. All groups land in `neuriplo-platform`; no owning-repo
implementation branch is touched.

## Group 1: Decision record and packet registration (platform, this repo)

- Write ADR 0014 (generic profiles plus executor-neutral scheduling;
  Slurm first for batch, Kubernetes evaluated for serving, HTCondor/OpenPBS
  documented alternatives, no purchase, no always-on fleet, privacy rule);
  record D-1 to D-4 from requirements.
- Register the packet in `specs/roadmap.md` Now; list ADR 0014 in
  `docs/adr/README.md`.
- Observable: V-1 passes (`scripts/check_platform.py`).

## Group 2: Placement architecture and purchase assessment (platform)

- Write `docs/architecture/heterogeneous-placement.md`: generic profile
  table with backend mapping, Windows x64 CPU profile with native-runner
  route, SDK cache placement with the GGML/TVM placeholder warning and the
  CPU-recipe limit, scheduler comparison, on-demand policy, dual-boot
  caution, and the unchanged in-flight campaign scope.
- Observable: V-5 and V-6 pass on review.

## Group 3: Executor-neutral job/evidence contract (platform)

- Write `contracts/scheduler-job-contract.md` (Version 0.1.0, Draft):
  job identity fields, profile reference, backend/task/model/dataset,
  executor binding kept out of the identity, evidence envelope, scheduler
  mapping notes for Slurm and Kubernetes, compatibility rules, validation
  strategy, examples. Owner: `neuriplo-platform`.
- List it in `contracts/README.md`.
- Observable: V-2 and V-7 pass.

## Group 4: Scheduled-session runbook and privacy enforcement (platform)

- Write `ops/runbooks/scheduled-validation-session.md`: prepare, start,
  run, collect, stop. Offline workers enter planned/on-demand state, never
  failure state. Privacy reminders inline.
- Add the untracked operator-inventory directory to `.gitignore`.
- Observable: V-1 (runbook sections), V-3, V-4 pass.

## Group 5 (deferred, not this packet): first executor runs

- Bind the contract to one executor (Slurm first): profile-to-node map in
  untracked operator inventory, batch jobs per backend, evidence envelopes
  attached to compatibility sets.
- Pilot the Windows native runner for the OpenCV 5 plus ONNX Runtime
  profile from the owning-repo side.
- This group needs machines powered for scheduled sessions and
  owning-repo/operator work; it is explicitly out of this packet and
  becomes a roadmap candidate when an operator schedules it.
