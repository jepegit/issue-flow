---
title: Do ops work without a PR
---

# Do ops work without a PR

## Goal

Track work that should **not** produce a pull request — promoting staging to
production, flipping a feature flag, an external deploy checklist, tag-only
steps — through an issue, and close it cleanly.

## Steps

1. Put the configured `ops` label on the GitHub issue (default name: `ops`) and
   run `iflow pick`, **or** run `iflow ops <N>` directly. If an issue has both
   the `ops` and `yolo` labels, ops wins.
2. The agent captures the issue and checks the working tree. It refuses when
   product code has uncommitted changes; working on the default branch is
   fine here.
3. It walks the ops checklist step by step, **asking before each step**, and
   logs what was done in `issue<N>_status.md`.
4. It finishes with `iflow close ops` (aliases `nopr`, `no-pr`): a final
   checklist confirm, the local issue files moved to `03-solved-issues/`, an
   optional commit of those tracking files, and `gh issue close` on GitHub.
   **No branch push, no PR.**

## Related

- [Command reference](../issue-workflow.md) — `/iflow-ops`
- [Label-driven flows](../configuration.md#label-driven-flows) — `label_flows`, `ops_label`
- [Work one issue end-to-end](work-one-issue.md) — the normal PR path
