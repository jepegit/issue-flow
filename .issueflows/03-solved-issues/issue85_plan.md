# Plan: Issue #85 — Align issues with plan

## Goal

Audit the "Future plans" section in `README.md` against open GitHub issues, then create GitHub issues for any feature promises that lack tracking.

## Constraints

### Prior art

- `.cursor/skills/iflow-pick/SKILL.md` — shows `gh issue create` usage for creating a new general-fixes issue (with title/body confirmation).
- `iflow-pick` expects confirmation before creating any GitHub issue; follow the same pattern.

### Scope

- **Read-only for code** — this task creates GitHub issues only, no source changes.
- **Issue body quality** — each created issue should have a clear, actionable description with context and acceptance criteria.
- **Reference the README** — link back to the README section so the issue-requester connection is explicit.
- **Milestone assignment** — suggest a milestone (e.g. v.0.5.0 or later) when creating each issue, but accept user override.

## Approach

1. **Parse the README future plans** (lines 478-482) into a structured list.
2. **Cross-reference with open issues** — check which plans already have tracking issues:
   - "More editors (Windsurf)" → already tracked as #17
   - "`issue-flow status`" dashboard → already implemented (in README usage section, CLI commands, shipped in v.0.4.x)
   - "Custom templates" → NOT tracked
   - "Git hook integration" → NOT tracked
   - "GitHub Actions workflow" → NOT tracked
3. **Draft issue bodies** for the three untracked items, each with:
   - Title: terse feature summary
   - Body: what it is, why it matters, what "done" looks like
   - Link to README.md future plans section as context
4. **Confirm with user** — show the three proposed issues (title + body) and ask for approval before creating.
5. **Create issues** — use `gh issue create --title "..." --body "..."` (add `--milestone` if suggested/confirmed).
6. **Update status** — record the created issue numbers in `issue85_status.md`.

## Files to touch

- `.issueflows/01-current-issues/issue85_status.md` (create, track progress and created issue numbers)
- No source code changes

## Test strategy

- **Validation**: after creating issues, run `gh issue view <N>` for each to confirm title/body landed correctly.
- **Cross-check**: re-run `gh issue list --state open` and verify the new issues appear.

## Open questions

- Should the new issues be assigned a milestone (e.g. v.0.5.0), or left unassigned for triage?
