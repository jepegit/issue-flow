# Ops / no-PR close

**Issue:** [#251 — Support no-PR / ops work](https://github.com/jepegit/issue-flow/issues/251)
**Status:** decided with the issue plan (2026-09-11).

## Context

The normal lifecycle assumes code → branch → PR. Some real work should not open a
PR: promote staging→production, flip a feature flag, run an external deploy
checklist, or a tag-only step with no product diff. `modes.md` had deferred a
“no-PR close variant”; this ships it as a token + skill, not a separate mode id.

## Decision

1. **Close token** `ops` (aliases `nopr` / `no-pr`) — dedicated **Ops close path**
   in `/iflow-close`: checklist confirm, refuse product-code dirty trees and
   unique product commits, skip HISTORY by default, skip push/PR, archive
   tracking, optional `.issueflows/` commit (default branch allowed with
   confirm), `gh issue close`. Mutually exclusive with `yolo` / `draft`.
2. **Config** `ops_label` (default `"ops"`), gated by existing `label_flows`,
   same bake pattern as `yolo_label`.
3. **`/iflow-ops`** off-path skill — entry for “do ops now”, then `close ops`.
4. **Pick routing** — `ops_label` → `/iflow-ops`; when both yolo and ops labels
   present, **ops wins**.
5. **HISTORY** — skip by default on ops; honour explicit `log "..."`.
6. **Defer** — `/iflow-review ops`, `/iflow-cycle ops`, body auto-detect.

## Alternatives considered

- Separate scaffolding **mode** that rewrites all close copy — rejected; mode
  mechanism stays surface selection; ops is a close variant.
- Auto-detect ops from issue text — rejected; too easy to skip review silently.
- Always require an issue branch for ops — rejected; default-branch tracking
  commits are fine when there is no product diff.

## Examples

- Promote staging → production via project deploy CLI / console.
- Flip a remote feature flag; record result in status.
- Run a one-off ops checklist documented in the GitHub issue body.
