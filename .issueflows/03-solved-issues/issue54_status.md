# Status for issue #54: Allow for more interactive sessions

- [x] Done

## Summary

Added a new off-path `/issue-fix` slash command (and mirrored
`issueflow-issue-fix` skill) for interactive iterative-fix sessions: set up one
GitHub issue + long-lived branch, loop over many small fixes (short plan each,
implemented only on confirmation, recorded in `issue<N>_status.md`), and finish
with `/issue-close`.

## Done so far

- **New command template** `src/issue_flow/templates/commands/issue-fix.md.j2`
  (3-phase: set up session → fix loop → finish via `/issue-close`).
- **New skill template** `src/issue_flow/templates/skills/issueflow_issue_fix/SKILL.md.j2`
  (frontmatter `name: issueflow-issue-fix`, `disable-model-invocation: true`).
- **Manifest** `src/issue_flow/templating.py`: added `issue-fix` to
  `COMMAND_NAMES` and `issueflow_issue_fix` to `SKILL_DIRS` (cursor 25→27,
  codex 14→15).
- **Off-path wiring**: `/issue-fix` listed as never-auto-dispatched in
  `commands/iflow.md.j2` + `skills/issueflow_iflow/SKILL.md.j2`, with a note to
  drive active sessions via `/issue-fix` + `/issue-close`.
- **Rules** `rules/_body.md.j2`: added an `/issue-fix` paragraph to the command
  lifecycle (propagates to `issueflow-rules.mdc`, `AGENTS.md`, `CLAUDE.md`).
- **Docs** `docs/issue-workflow.md.j2`: count ten→eleven, command + skill table
  rows, dispatcher "not auto-dispatched" line, new `## 9. /issue-fix` section,
  and Detours entry. `README.md`: tree listing, skills list, off-path prose.
- **Design doc** `.issueflows/04-designs-and-guides/issue-fix-interactive.md`
  recording the 6 decisions (off-path, always-GitHub, status-file log, coexist
  with `/issue-pick fix`, delegate to init/close, `/iflow` document-only).
- **Tests** `tests/test_templating.py`: updated counts (25→27 ×2, codex 14→15
  & skills 13→14), added `issue-fix` to expected command/skill lists, and added
  `test_issue_fix_describes_interactive_session`,
  `test_issue_fix_skill_mirrors_command`, `test_iflow_lists_issue_fix_as_off_path`.
- Regenerated the local scaffold (`uv run issue-flow update`) so
  `.cursor/commands/issue-fix.md` + `.cursor/skills/issueflow-issue-fix/` exist.

## Verification

- `uv run pytest` — **144 passed**.
- `uv run ruff check src/ tests/` — **All checks passed**.

## Design decisions (resolved 2026-06-16)

- Command name `/issue-fix`; always create a GitHub issue (no local-only mode);
  per-fix log in `issue<N>_status.md`; coexist with `/issue-pick fix`; `/iflow`
  interaction documented only (no status marker in v1). See the design doc.

## Remaining work

- None for this issue. Next step: `/issue-close` (tests, optional version bump,
  commit, push, PR).
