# Rename `/iflow-start` → `/iflow-build`

**Issue:** [#183 — renaming from start to build](https://github.com/jepegit/issue-flow/issues/183)
**Status:** decided 2026-07-19, implemented in the same issue.

## Context

The post-plan implement step was named `/iflow-start`. "Build" better matches
"implement the plan", and frees `start` for a future small auto-loaded prep
skill (not part of this issue).

## Decisions

1. **Hard cut** — no lasting `iflow start` / `/iflow-start` alias.
2. **`agent state` stage** string becomes `"build"`; `next_command` is
   `/iflow-build`. `STAGE_START` remains a Python alias of `STAGE_BUILD` for
   importers.
3. **Retirement** — `iflow-start` added to `RETIRED_COMMANDS` and
   `RETIRED_SKILLS` so `issue-flow update` prunes old scaffold files.
4. **Behaviour unchanged** — rename + docs only.

## Consequences

- Chat invoke: `iflow build` / `/iflow-build`.
- Yolo / dispatcher chains use `build` instead of `start`.
- Dogfood projects need `issue-flow update` after upgrade.
