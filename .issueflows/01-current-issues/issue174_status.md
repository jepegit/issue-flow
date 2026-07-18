# Status — Issue #174: skill for reviewing and labelling issues

- [ ] Done

## What's done

- Plan accepted (name `iflow-review`, create missing label, re-score all open, CLI in PR, omit simple mode).
- CLI: `issue-flow agent label-candidates` / `label-apply`; `_yolo_from_labels` honours config `yolo_label`.
- Templates: `iflow_review` skill + `iflow-review` command; registered in `COMMAND_NAMES` / `SKILL_DIRS` / step profiles; rules + workflow docs; dispatcher off-path lists.
- Design doc: `.issueflows/04-designs-and-guides/issue-review-labelling.md`.
- Dogfood: `issue-flow update` refreshed `.cursor/skills/iflow-review/`, AGENTS, docs.
- Tests: 529 passed (`uv run pytest`).

## Remaining work

- `/iflow-close`: optional bump, mark Done, archive (PR [#177](https://github.com/jepegit/issue-flow/pull/177) already open as draft).
