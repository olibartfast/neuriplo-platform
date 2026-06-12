# Inbox: human

## [x] from:claude 2026-06-12 -- merge queue (handled: client #3, neuriplo #15/#16, platform #3/#4 all merged)

## [ ] from:claude 2026-06-12 -- release queue: 3 PRs + tags ready

All release prep is done; each release is one PR merge + one tag push.
The permission layer correctly blocks me from merging to master or
tagging, so these are yours:

1. **neuriplo v0.6.0** — merge [PR #17](https://github.com/olibartfast/neuriplo/pull/17)
   (`release/v0.6.0` -> master, includes the CHANGELOG 0.6.0 section), then:
   `git tag v0.6.0 <merge-commit> && git push origin v0.6.0`,
   then back-merge master -> develop.
2. **client v0.3.0** — merge [PR #6](https://github.com/olibartfast/neuriplo-kserve-client/pull/6)
   (`release/0.3.0` -> master, VERSION + CHANGELOG bumped), then tag
   `v0.3.0` and back-merge (master also still carries un-back-merged
   v0.2.0 release commits).
3. **runtime v0.1.0** — merge [PR #10](https://github.com/olibartfast/neuriplo-kserve-runtime/pull/10)
   (develop -> master, first release), then tag `v0.1.0` and back-merge.
4. **infer release** — AFTER tags 1 and 2 exist: run
   `scripts/cut_release.sh 0.6.0` (auto-detects all four sibling pins
   from remote tags), update CHANGELOG, merge/tag per the script's
   printed GitFlow steps. Claude can prepare this branch on request once
   the tags are pushed. The runtime tag is not an infer blocker
   (versions.env does not pin the runtime).

Order constraint: 1 and 2 before 4; 3 anytime.
