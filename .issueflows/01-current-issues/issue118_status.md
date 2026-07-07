# Issue #118 status: slash-less iflow invocation

- [ ] Done

## What's done

- Added **Chat invocation (no slash)** section to `templates/rules/_body.md.j2` — primary form `iflow <step>`, aliases hyphen/slash; editor-neutral wording.
- Created `templates/skills/_invocation_forms.md.j2` and included in all 13 lifecycle skill templates.
- Updated `templates/docs/issue-workflow.md.j2` — keyboard callout, space-first invoke column.
- Added `.issueflows/04-designs-and-guides/slash-less-invocation.md`.
- README quick-start mentions `iflow plan` / `iflow init`.
- Tests: `test_rules_body_documents_slashless_chat_invocation`, skill + doc assertions.
- Re-rendered via `issue-flow update`.

## Testing

- `uv run ruff check src/ tests/` — clean
- `uv run pytest` — 348 passed
- `uv run .issueflows/00-tools/verify_scaffold.py` — all checks passed

## Remaining work

- `/iflow-close` — commit, push, PR
