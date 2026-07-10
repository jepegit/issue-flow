---
name: iflow-epic
description: >-
  Plan a larger change as a staged epic: draft epic<N>_plan.md with stages of
  manageable issue specs. Draft-only — publishing to GitHub is a separate step.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — epic planning (`/iflow-epic`)

Follow this skill to plan a change that is **too large for one issue**: divide it into sequential **stages**, each stage into **manageable issues** that flow through the normal lifecycle (`/iflow-init` → `/iflow-plan` → `/iflow-start` → `/iflow-close`).

**This skill is draft-only.** Its deliverable is `.issueflows/05-epics/epic<N>_plan.md`. It never creates GitHub issues, labels, or milestones — publishing a confirmed plan is a separate, explicitly confirmed step of the epic workflow.

## Input

- **`<N>`** — the GitHub issue number of the **epic anchor** (an umbrella issue describing the large change). Required: an epic without an anchor has nowhere to track progress. If no anchor issue exists yet, stop and ask the user to create one (title prefixed `Epic:`, label `epic` when available) — creating it is the user's call, not this skill's.
- Optional free text — extra context, constraints, or a proposed stage split to seed the draft.


**Invoke:** type `iflow epic` in chat, or `/iflow-epic` from the slash menu (`iflow-epic` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: reasoning** — Prioritize deep thinking and careful trade-offs over speed or token economy.

In Cursor: switch to a thinking-capable model before invoking this step (not Auto-only).



Keep scope tight to what this step requires.




### Resolve project root (multi-root workspaces)

Before any `git`, `gh`, or `.issueflows/` path operation in this workflow:

**Resolution order** (stop when unambiguous):

1. **Explicit hints** in slash input — `root:<path>`, `repo:<folder-basename>` (directory name, e.g. `cellpy-core`), or `repo:owner/name`.
2. **CLI fast path** — `issue-flow agent resolve [-C <start>] [--from-file <active-file>] [--json]`. Use the returned `project_root` and `repo`; pass `-C <project_root>` to other `issue-flow agent …` subcommands. When the answer came from the workspace registry, the payload sets `resolved_via_workspace_default: true`.
3. **Branch context** — exactly one workspace repo whose branch matches `^\d+-` → that root.
4. **Single scaffold** — exactly one `.issueflows/` tree visible in the workspace → that root.
5. **Workspace default** — an `issueflow-workspace.toml` at the workspace root (created with `issue-flow workspace init`) may name a `default` member repo; use it when no scaffold matched above. Tell the user the default was used.
6. **Ambiguous** → **stop and ask**; never guess between sibling repos.

After resolution, treat the result as `<project_root>` and `<owner/repo>`:

- **Git:** `git -C <project_root> …` (or `issue-flow agent … -C <project_root>` for supported ops).
- **GitHub:** always `gh … --repo <owner/repo>` — never rely on `gh`'s implicit cwd default.
- **Paths:** all `.issueflows/…` paths are under `<project_root>`.

When `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` exists, read it for layout and cross-repo guidance.

## Instructions

1. **Gather context (read-only).** Read the epic anchor (`gh issue view <N> --repo <owner/repo>`), skim `.issueflows/04-designs-and-guides/` for relevant design docs (cite them in the plan when they shape the approach), and — when `graphify-out/GRAPH_REPORT.md` exists — skim it before grepping.

2. **Draft the staged plan** at `.issueflows/05-epics/epic<N>_plan.md` using exactly this structure (the publish step parses it):

   ```markdown
   # Epic #<N>: <title>

   Anchor: <GitHub issue URL>
   Status: draft

   ## Goal

   <what the whole epic achieves, and how we know it is done>

   ## Constraints

   <hard boundaries, non-goals, ordering requirements>

   ## Stage 1 — <stage title>

   <one paragraph: what this stage proves or delivers>

   ### Issue: <title as it will appear on GitHub>

   - Spec: <self-contained paragraph: context, scope, acceptance criteria>
   - Depends on: none | #<M> | stage <j> issue <k>
   - yolo: yes | no — <one-line judgment against the yolo-fitness criteria>

   ### Issue: <next issue title>
   ...

   ## Stage 2 — <stage title>
   ...
   ```

3. **Sizing rules for issue specs** — every issue must be *manageable*:
   - one issue = one branch = one PR, implementable in roughly a day or less;
   - a **crisp acceptance criterion** someone else could verify;
   - dependencies stated explicitly: `#<M>` for already-published issues, `stage <j> issue <k>` placeholders for unpublished ones (the publish step resolves placeholders to real numbers);
   - a **yolo-fitness judgment** per issue: `yes` only when it is well-specified, mechanical or pattern-following, low blast radius, and guarded by existing tests — umbrella work, design decisions, and flag-day changes are `no`.

4. **Stage discipline** — stages are sequential milestones, each small enough that finishing it can change the plan for the next. Front-load the stage that retires the most risk. Do not plan more than 2–3 stages in detail; sketch later stages as bullets under a `## Later (unstaged)` heading instead of fake-precise issue specs.

5. **Review with the user.** Present the draft (stage titles, issue titles, dependency graph, yolo flags) and iterate until they confirm. Record the confirmation by changing `Status: draft` to `Status: confirmed` in the plan file.

6. **Stop.** Publishing the confirmed plan (creating the GitHub issues stage by stage and maintaining the task list on the anchor issue) is the epic workflow's separate publish step — never do it from this skill, even if asked to "just create them": switch surfaces explicitly so the confirm gates stay distinct.

## Constraints

- **Draft-only**: no `gh issue create`, no label or milestone writes, no task-list edits on the anchor issue. Reading with `gh issue view` / `gh issue list` is fine.
- **Off-path**: `/iflow` never auto-dispatches to `/iflow-epic`; the user opts in explicitly.
- Epics decompose **into** the normal single-issue lifecycle, never around it — no issue spec may assume work happens outside a normal issue branch + PR.
- The plan file is user-owned working state under `.issueflows/`: `issue-flow update` never touches it.
