# Inbox: human

## [x] from:claude 2026-06-12 -- merge queue (handled: client #3, neuriplo #15/#16, platform #3/#4 all merged)

## [x] from:claude 2026-06-12 -- release queue (handled: all releases cut, see below)

## [ ] from:claude 2026-06-12 -- releases DONE: ensemble at neuriplo v0.6.0

All four components released and back-merged (develop == master everywhere):

- **neuriplo v0.6.0** — multi-backend builds, dlopen plugin C ABI,
  raw typed-buffer output API.
- **neuriplo-kserve-runtime v0.1.0** — first release: KServe V2 HTTP+gRPC
  data plane, raw_output_contents, multi-backend plugins.
- **neuriplo-kserve-client v0.3.0** — proto profiles + gRPC raw-contents
  conformance oracle.
- **neuriplo-infer v0.6.0** — sibling pins bumped to neuriplo v0.6.0 and
  client v0.3.0 (videocapture v0.3.0, neuriplo-tasks v0.4.0 unchanged);
  pins validated; GitHub release auto-publishes after Release Guard.

Nothing left in the merge queue. Next dev items (unscheduled): TensorRT
metadata crash (top neuriplo roadmap item), EngineOptions device-selection
proposal across all 13 backends, plugin ABI test expansion.
