# Issue #282: Skill split — which packaged stems are global vs project-local

Source: https://github.com/jepegit/issue-flow/issues/282

## Original issue text

### Problem / context

Epic #269 comment asks which packaged skills install globally vs stay project-local, and whether Cursor reads `~/.claude/skills/`. Classify stems before any global materialize.

### Spec

Survey `SKILL_DIRS` (lifecycle vs behaviour vs pstack). Write a table in the design doc (or a sibling `global-vs-local-skills.md`): stem → `global` | `local` | `both` (global install + project override). Check whether Cursor user skills live under `~/.cursor/skills/` and whether Cursor also reads `~/.claude/skills/` (comment hypothesis — verify, do not assume). Record editor-profile implications. No `src/` install in this issue.

### Acceptance criteria

- Table reviewed.
- Every default stem classified.
- Cursor/Claude global paths verified or marked unknown with a follow-up under Later.

### Goal

Agreed stem list + verified (or explicitly unknown) global skill paths for Cursor and Claude.

### Model

deep

### Depends on

#281

Part of epic #269.
