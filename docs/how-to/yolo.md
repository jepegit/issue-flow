---
title: Fast-track a small issue
---

# Fast-track a small issue

## Goal

Ship a **small, low-risk** change (docs tweak, tiny fix) under one confirm:
`capture → plan → build → close`, then auto-merge.

## Steps

**Option A — label**

1. Put the configured `yolo` label on the GitHub issue (default name: `yolo`).
2. Run `iflow pick`, confirm the issue. Pick folds the yolo chain into that
   confirm — no second prompt.

**Option B — explicit**

1. Already on an issue branch with a clean tree and green tests.
2. Run `iflow yolo <N>` (or `/iflow-yolo`). Confirm once.
3. Chain runs through close: changelog without a prompt, PR squash-merged
   (may watch checks, then retry; `--auto` only as last resort).

Use yolo only when scope is clearly small. Ambiguity, failed tests, or a dirty
unrelated tree **stops** the chain — fall back to the linear commands.

## Related

- [Label-driven flows](../configuration.md#label-driven-flows) — `label_flows` / `yolo_label`
- [The workflow](../issue-workflow.md) — `/iflow-yolo` section
- [Work one issue end-to-end](work-one-issue.md) — non-hands-off path
- Batch many yolo issues: `iflow cycle yolo`
