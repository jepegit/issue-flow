# Issue #276: update: warn or skip when a packaged skill path is not last render

Source: https://github.com/jepegit/issue-flow/issues/276

## Original issue text

## Problem / context

`issue-flow update` re-renders every packaged skill and silently overwrites
same-named folders under editor trees (e.g. `.cursor/skills/iflow-plan`).
Foreign-named folders are already left alone (`_prune_excluded_surfaces` only
touches `SKILL_DIRS`). User tools such as skillbook (copy or symlink) can
therefore lose edits if they reuse a packaged output name.

See `.issueflows/04-designs-and-guides/skillbook-lessons.md` (issue #275).
Part of epic/parent: none — follow-up from #275.

## Spec

On `update` (and `init` overwrite of an existing skill dir), detect that a
packaged output path is not “ours”:

- symlink / unexpected extra files, or
- content hash ≠ last rendered template (or a stored render stamp)

Then **warn** and either skip that path or require an explicit force
(choose one in `/iflow-plan`; default recommend: warn + skip, `--force` overwrites).

Do **not** depend on the skillbook CLI. Name-collision is enough.

## Acceptance criteria

- Packaged name with foreign/symlink/hash-mismatch content: `update` does not
  silently overwrite; warning names the path.
- Unchanged packaged skills still update as today.
- User folders whose names are not in `SKILL_DIRS` stay untouched.
- Tests cover skip/warn vs `--force` (or the chosen confirm).
- `skillbook-lessons.md` follow-up table links this issue.

## Out of scope

- Personal skill library / push-pull (#269).
- Agent Skills lint (#268).
- Scan of unmanaged skill dirs (sibling issue).

## Comments (curated summary)

- **Clarifications / constraints**: sibling unmanaged-skill scan is #277; Agent Skills lint stays on #268.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-09-17._
