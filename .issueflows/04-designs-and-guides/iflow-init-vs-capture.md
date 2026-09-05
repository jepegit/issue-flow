# `iflow-init` vs `iflow-capture` (#241)

**Status:** decided 2026-09-05.
**See also:** #183 (`iflow-start` → `iflow-build`) for the retire/rename pattern.

## Context

`/iflow-init` used to mean "capture this GitHub issue into `.issueflows/`"
(often inferred from the branch name). That overloaded the word *init*, which
users and the CLI already use for **scaffolding the harness** (`issue-flow
init`).

## Decisions

1. **Issue capture** is **`/iflow-capture`** (`iflow capture`, skill
   `iflow-capture`). Matches `issue-flow agent capture`.
2. **`/iflow-init`** is **harness cold-start / check** (off-path): guide
   `issue-flow init` when the scaffold is missing; otherwise point at
   `update` / doctor / `/iflow-capture`. Never captures issues; never
   auto-dispatched by `/iflow`.
3. **No dual-meaning alias** for one release (same as #183). Loud docs +
   HISTORY note instead.
4. Lifecycle stage id is **`capture`** (`STAGE_CAPTURE`); `STAGE_INIT` remains
   a back-compat alias equal to `STAGE_CAPTURE`. Suggested next command is
   `/iflow-capture`.
5. Scaffold marker skill stays `skills/iflow-init/SKILL.md` (always emitted).

## Link

Issue #241, `issue241_plan.md`.
