# Status for issue #45: include issue comments

- [x] Done

## What was done

- `/issue-init` now fetches GitHub issue comments alongside body (`gh issue view --json title,body,url,number,comments`) and triages them into a curated section written to `issue<N>_original.md`.
- Added a new skill `issueflow-issue-comments` describing how to triage the comment thread into three buckets (Additional tasks, Clarifications / constraints, Superseded / retracted) with chronological precedence, noise filtering, and edge-case handling.
- Updated `issueflow-issue-init` skill to mirror the new fetch + triage step and to delegate to the new skill.
- Registered the new skill in `TEMPLATE_MANIFEST` so `issue-flow update` emits it into `{agent_dir}/skills/issueflow-issue-comments/SKILL.md`.

## Files changed

- [src/issue_flow/templates/commands/issue-init.md.j2](../../src/issue_flow/templates/commands/issue-init.md.j2) — fetch comments, add triage step (2a), extend file format with optional `## Comments (curated summary)` section, update output + constraints.
- [src/issue_flow/templates/skills/issueflow_issue_init/SKILL.md.j2](../../src/issue_flow/templates/skills/issueflow_issue_init/SKILL.md.j2) — mirror the command changes; delegate to the new skill.
- [src/issue_flow/templates/skills/issueflow_issue_comments/SKILL.md.j2](../../src/issue_flow/templates/skills/issueflow_issue_comments/SKILL.md.j2) — new skill with triage rules, three buckets, output contract, and edge cases.
- [src/issue_flow/templating.py](../../src/issue_flow/templating.py) — added the new skill entry to `TEMPLATE_MANIFEST`.
- [tests/test_templating.py](../../tests/test_templating.py) — bumped manifest count to 21, added `issueflow_issue_comments` to the expected-skills list, and added three focused tests (`test_issue_init_fetches_and_triages_comments`, `test_issue_init_skill_delegates_to_comments_skill`, `test_issue_comments_skill_documents_triage_rules`).

## Tests

- `uv run pytest -q` → 71 passed.
- No linter errors on changed files.

## Remaining work

None. Both tasks in the original issue are covered:

1. `/issue-init` goes through the comments and includes tasks from them (non 1-to-1 curated summary, honors chronological precedence so later comments can supersede earlier ones).
2. A new skill (`issueflow-issue-comments`) describes how to review the comments and extract relevant tasks.
