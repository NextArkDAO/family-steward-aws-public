# QMD Integration Boundary

QMD is Family Steward's optional local candidate-discovery layer. It improves recall when a
family asks for something using different words than the original memory.

It does not decide what is true, current, superseded, private, or authorized. Family Steward
retains those decisions and must verify every candidate against its own source record before
Aster may use it.

The accepted shape is:

```text
household question
  -> bounded QMD semantic search in family-steward-v0
  -> untrusted candidate paths and scores
  -> Family Steward source and authority verification
  -> bounded cited memory result
  -> Aster response
```

## Current state

- Adapter and product status surface: implemented.
- Accepted QMD version: `2.8.3`.
- Default mode: semantic candidate discovery with `vsearch`.
- Persistent service or listener: none.
- Private household indexing: not authorized.
- Windows QMD infrastructure: independently accepted on Windows and macOS.
- Family Steward projection: three fictional Carter events with pinned file and manifest digests.
- Browser output: one current Family Steward event; no QMD snippets, scores, paths, or IDs.
- Fallback: Family Steward continues with its deterministic micro-memory when QMD is absent.

## Activation gate

`scripts/setup-qmd.ps1` creates the dedicated named index. `scripts/run-local.ps1` attaches the
accepted runtime, config, and cache paths only for that local process. Removing those environment
variables detaches QMD immediately. The connector has no daemon, listener, startup item, global
command, or background schedule.

Every query follows the same sequence:

1. Verify exact QMD version and build.
2. Search only `family-steward-v0` in the `family-steward` named index.
3. Accept only paths bound by the pinned authority manifest.
4. Recreate the Markdown projection from the active append-only memory event.
5. Return one current event using Family Steward fields only.
6. Return a quiet unavailable or no-match result when any boundary fails.
