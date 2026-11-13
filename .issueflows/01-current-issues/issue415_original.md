# Issue #415: Add `/iflow-run direct` for capable models

Source: https://github.com/jepegit/issue-flow/issues/415

## Original issue text

### Problem / context

Capable models (Fable-class and similar) can implement a normal issue without a planning interview. The hands-off paths we have still spend that interview, or they only fit a smaller job:

- `/iflow-plan` writes `issue<N>_plan.md` and stops for Accept / Revise / Abort. Grill-me adds one question at a time.
- `/iflow-run yolo` auto-confirms a short plan, but only for a small, low-risk change, and it squash-merges.
- `[issueflow].hands_off` skips the up-front confirm on yolo / cycle / auto / drive. Interactive pick, plan Accept, build, and ordinary close still ask, and the plan step still runs.
- `/iflow-run auto` and `drive` are the epic path: stages, adversarial review, and a loop-budget ask.

What should stay is the bookkeeping and the tools that save tokens:

- Graphify routine: `graphify query` / `path` / `explain` when `graphify-out/graph.json` exists, and `graphify update .` (AST only) after code edits.
- CLI fast paths (`issue-flow agent state --json` and the other `agent` helpers) instead of re-deriving the same fact from the tree.
- Solved-issue tracking: `issue<N>_status.md`, an explicit `- [x] Done` or `- [ ] Done`, then move the group to `03-solved-issues/` or `02-partly-solved-issues/`.
- Essential tests, when `[issueflow].essential_tests` is on: `pytest -m essential` as the in-loop gate, and a registry row for tests this issue added or changed (`.issueflows/04-designs-and-guides/essential-tests.md`, `test-registry.md`).
- History trick: `Changelog` / `Changelog-Date` / `Changelog-Id` trailers on the close commit. Leave `HISTORY.md` untouched on the issue branch. `issue-flow changelog release` still writes it on the default branch.

### Spec

Add one `/iflow-run` mode, id `direct`:

```text
/iflow-run direct [<N>]
```

`direct` names the posture (do the job). Fable is an example of the model class, not the command name.

Invoking the mode is the authorization. No second confirm, no plan Accept, no grill-me, no open-question interview.

Chain for one issue:

1. Resolve `<N>` from the argument, otherwise the focus issue. Capture when `issue<N>_original.md` is missing. An archived group under `02-partly-solved-issues/` or `03-solved-issues/` is a stop (re-open only on purpose, via `/iflow-pick`).
2. Work on `<N>-<slug>` through the existing worktree-first path when home is the default branch and the tree is clean. A dirty unrelated tree, or home not on the default branch, is a stop.
3. Skip `issue<N>_plan.md` and the Accept gate. Record decisions in `issue<N>_status.md` as the work proceeds.
4. Implement the issue. Before a broad search, when `graphify-out/graph.json` exists, run `graphify query` / `path` / `explain`. After code edits, run `graphify update .` (AST only). A missing or failing graphify is one report; continue with grep. Prefer `issue-flow agent … --json` over re-deriving the same fact. Read the design note that matches the area.
5. Tests. When `essential_tests` is true, `pytest -m essential` (via the project's runner) is the in-loop gate, and this mode writes the registry row for tests this issue added or changed (mark vs unmarked) with no confirm. When the knob is false, run the project's documented test command. A failing suite stops the run.
6. Close bookkeeping, without the yolo merge: status checkbox, move the issue group, changelog trailers, commit, `issue-flow agent sync-branch`, push, open or update the PR (`Closes #N`). Stop with the PR URL.

Safety stops stay, and they are stops rather than menus: unfixable test failure, `sync-branch` exit 1, ambiguous repo, product-code conflict, destructive git. Several independent deliverables: stop and name `/iflow-issue epic` or `/iflow-issue split`. This mode does not create children.

Surface:

- New mode file `src/issue_flow/templates/skills/iflow_run/direct.md.j2` (plain markdown: no frontmatter, no model directive). One router row in `iflow_run/SKILL.md.j2`. One line in the workflow doc. A short section in `.issueflows/04-designs-and-guides/hands-off-runs.md` recording why this is not yolo, not `hands_off`, and not auto/drive.
- Stay inside the word budgets in `tests/test_command_surface.py` (`SKILL_BUDGET` 1600, `SIDE_BUDGET` 3000). New prohibition hits count toward the mode-file cap of 48; state the positive action.
- Tests cover the router row, that the rendered mode file has no frontmatter, and that the word budget still passes.

### Acceptance criteria

- [ ] `/iflow-run direct` is a mode of `iflow-run`, rendered from the template, and listed in the router and the workflow doc.
- [ ] The mode file tells the agent to skip plan Accept and user questions, and to use graphify query/update plus the agent CLI when those tools exist.
- [ ] The mode file keeps status movement, essential-tests behavior (only when the knob is on), and changelog trailers, and it leaves `HISTORY.md` unedited on the issue branch.
- [ ] The mode opens or updates a PR and does not merge it and does not run `/iflow-cleanup`.
- [ ] The design note records why this is not yolo, not `hands_off`, and not auto/drive.
- [ ] `uv run pytest` and `uv run ruff check src/ tests/` pass.

### Out of scope

- A new scaffolding mode id (`standard` / `novice` / `simple` stay as they are).
- Naming the command `fable`, or binding it to one model id.
- Auto-merge, `/iflow-cleanup` from this mode, or a label that routes `/iflow-pick`.
- Changing yolo, cycle, auto, drive, or the `hands_off` knob.
- Forcing caveman on.
- `graphify extract` (the LLM pass).
- Creating epic or split children from this mode.
