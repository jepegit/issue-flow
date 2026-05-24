# Issue #57: /issue-plan: add explicit 'prior-art discovery' step (codebase grep + graph hubs)

Source: https://github.com/jepegit/issue-flow/issues/57

## Original issue text

## Summary

`/issue-plan` currently does enough exploration to write a plan, but the
exploration is *implicit* — it relies on the agent's discretion to grep
for related code before proposing an approach. In practice, on
multi-module changes, the agent can produce a clean plan that still
misses prior art already living elsewhere in the codebase. The plan then
silently risks duplicating an existing helper or diverging from its
naming / parameter conventions.

I'd like `/issue-plan` to make that exploration **explicit and
checklist-driven**, with the graph integration as a first-class input
when available.

## Concrete proposal

Add a numbered step to the `/issue-plan` command (between the current
*"Read the issue"* and *"Explore, then propose"* steps) that says
roughly:

> **Prior-art discovery.** Before drafting the plan:
> 1. If `graphify-out/GRAPH_REPORT.md` exists, skim it for **God Nodes**,
>    **Communities**, and **Suggested Questions** whose names touch the
>    affected area. Note the community numbers.
> 2. Grep the codebase for sibling helpers / functions that already do
>    something adjacent to the new work (e.g. existing
>    `filter_*`, `remove_*`, `yank_*`, `add_*` helpers in the same
>    domain).
> 3. Capture findings in a **Prior art** sub-section under
>    `## Constraints` in `issue<N>_plan.md`. For each item, record:
>    - what it is (function name + module),
>    - what convention it follows (param shape, column names, units),
>    - and how the new work will be *consistent* with it (mirror,
>      coexist, or migrate later).
> 4. If the new work overlaps strongly with prior art, raise this
>    explicitly as an **Open question** ("merge with X?" vs "coexist
>    with X?") rather than silently picking one.

`/issue-start` would then read that sub-section before implementing, so
the API of any new module is grounded in what's already there.

## Why this matters (concrete example)

On `cellpy` issue #363 (adding a filtering layer for `summary_plot`),
the plan I drafted introduced a new `cellpy.filters.filter_summary`
without acknowledging that the codebase already has:

- `yank_before()` / `yank_after()`
- `remove_first_cycles_from_summary()` / `remove_last_cycles_from_summary()`
- `remove_outliers_from_summary*` / `remove_outliers_from_summary_on_index()`
- `add_c_rate()` / `create_rate_column()`

All of these were sitting in graphify communities 76 / 125 / 238 / 239
and were discoverable in ~30 seconds *if* the graph step had been part
of the planning checklist. They didn't surface until a manual retro,
and at that point the plan needed a "Prior art" patch.

A built-in checklist step would have caught this on the first pass.

## Notes / scope

- The graphify part should remain **opt-in / graceful** — if
  `graphify-out/GRAPH_REPORT.md` is absent, the step degrades to "grep
  only", matching how the existing rules already handle graphify.
- This is purely a `/issue-plan` change. No changes needed to
  `/issue-start`, `/issue-init`, or `/issue-close`, although
  `/issue-start` could *optionally* be tweaked to remind the agent to
  read the **Prior art** sub-section before writing new modules.
- Could also be mirrored in the `issueflow-issue-plan` skill so the
  on-demand `/issueflow-issue-plan` invocation gets the same checklist.

## Related

- Existing graphify guidance lives in the project-level
  `.cursor/rules/graphify.mdc` and (in this project) an
  `issueflow-build` skill. Today these recommend skimming the report
  but don't tie it into a specific lifecycle step — that's the gap
  this issue closes.
