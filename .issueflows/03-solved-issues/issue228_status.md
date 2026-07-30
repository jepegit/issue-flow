# Status — Issue #228: Allow picking based on label

- [x] Done

## What's done

- Pick skill + command templates: first-class `label:<L>` hard filter
  (GitHub `--label`, parked/epic filtered; empty → stop; never auto-pick).
- Soft hints remain bias-only when `label:` absent; cross-link to
  `/iflow-cycle label:<L>` / `yolo`.
- `issue-workflow.md.j2` + rendered `docs/issue-workflow.md` updated.
- Design note in `label-driven-flows.md` (pick filter vs cycle queue).
- Tests: `test_issue_pick_documents_label_hard_filter`,
  `test_init_pick_skill_documents_label_hard_filter`.
- `issue-flow update` refreshed local scaffold; full pytest green (586).

## Remaining work

- None.
