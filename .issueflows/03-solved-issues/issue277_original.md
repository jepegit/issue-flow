# Issue #277: doctor: report unmanaged editor skills

Source: https://github.com/jepegit/issue-flow/issues/277

## Original issue text

## Problem / context

Editor skill dirs can hold folders issue-flow did not scaffold. `update` leaves
unknown names alone, so they are invisible to `doctor` / `status`. Skillbook
`scan` is the analogue; we want a **read-only** report, not a library import.

See `.issueflows/04-designs-and-guides/skillbook-lessons.md` (issue #275).

## Spec

Extend `issue-flow doctor` (and/or `agent audit` / `status`) to list skill
directories under each selected `EditorProfile` skills path whose names are
**not** in `SKILL_DIRS` output names.

Report-only. No delete, prune, or import.

## Acceptance criteria

- A throwaway extra folder (e.g. `.cursor/skills/my-notes/`) appears in
  doctor/audit output (and `--json`).
- Packaged skills are not listed as unmanaged.
- No files deleted or rewritten by this feature.
- `skillbook-lessons.md` follow-up table links this issue.

## Out of scope

- Clobber protection on `update` (sibling issue).
- skillbook interop or `~/.skillbook`.
- Agent Skills lint (#268).

## Comments (curated summary)

- **Clarifications / constraints**: sibling clobber work stays on #276; Agent Skills lint stays on #268.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-09-17._
