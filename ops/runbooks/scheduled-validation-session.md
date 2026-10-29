# Scheduled Validation Session Runbook

Use this when running a validation or benchmarking session on the
heterogeneous fleet described in
`docs/architecture/heterogeneous-placement.md`. Jobs follow
`contracts/scheduler-job-contract.md`; hardware is referenced by generic
profile ID only.

## Goal

Run one scheduled session on the profiles the session needs, collect one
evidence envelope per job, then stop everything that was started. Offline
profiles stay in planned/on-demand state; they are never failures.

## Inputs

- Session ID (date plus purpose, for example `2026-10-29-smoke-1`).
- Job list: identity fields per the scheduler job contract.
- Executor for this session (one at a time: Slurm, Kubernetes,
  native runner).
- Compatibility set from `versions.yaml` when the session gives evidence
  for one.

## Procedure

1. Prepare jobs. Write each job identity (profile, backend, task, model
   digest, dataset revision) before touching any machine. Confirm every
   profile exists in the placement doc and every backend is one the
   profile claims. Do not invent profile IDs.

2. Start only what the session needs. Bring up the executor control plane
   (for example the Slurm controller) and the worker profiles scheduled
   for this session. Leave all other machines and services off. Record
   which profiles are online, which are planned/on-demand (offline), and
   which are out of campaign scope (skipped by decision, for example
   Jetson-class or AMD in the current UI campaign).

3. Bind and submit. Translate each job identity into the session
   executor's binding (Slurm partition/constraint/GRES, Kubernetes node
   selector/resources, or native-runner label). The local helper
   `ops/slurm/render_bindings.py` renders Slurm node lines from the
   untracked inventory; its stdout stays local. Never change identity
   fields during binding. Submit one executor only.

4. Collect evidence. For every job, produce the evidence envelope from
   the contract: identity echo, executor, outcome (`pass`, `fail`, or
   `skipped` with reason), log reference, metrics reference when the job
   is a benchmark, session ID. A profile that stayed offline is
   `skipped`, not failed.

5. Stop and verify. Shut down the control-plane services and workers
   started in step 2 unless an always-available queue is actually needed
   (record the exception and its owner). Verify nothing session-scoped is
   still running.

6. Record. Attach log and metrics references to the compatibility set
   evidence or the packet PR. Never paste personal IPs, hostnames,
   account labels, machine identifiers, credentials, or private local
   paths into tracked files; profile IDs plus digests are sufficient.

## Privacy Reminders

- Tracked files: generic profile IDs only.
- The profile-to-host inventory lives in the untracked local directory
  (see `.gitignore`); it is operator-owned and never committed.
- Logs attached as evidence must be scrubbed of hostnames and addresses
  before they enter the repo or a public artifact.
