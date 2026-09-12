# Issue #262: Add task-oriented how-to guides to the docs site

Source: https://github.com/jepegit/issue-flow/issues/262

## Original issue text

### Problem / context

Public docs cover install/first hour (`getting-started.md`) and long reference (`issue-workflow.md`, CLI, config). Common jobs still hard to find. Agent design notes in `.issueflows/04-designs-and-guides/` are not user how-tos.

### Spec

1. Add a **How-to** nav section on the Zensical docs site (`docs/how-to/` or similar).
2. Ship a **first set** of short, task-oriented pages (goal → steps → related commands/links):
   - Work one issue end-to-end (`pick` → `plan` → `build` → `close` → `cleanup`)
   - Fast-track a small issue (`yolo` / `yolo` label)
   - Park and resume (`pause` / pick parked)
   - After a squash merge (`cleanup`)
   - Refresh dirty open PRs (`pr-sync`, when shipped)
   - Choose a mode (`novice` / `simple` / `standard`)
   - **Create and run epics** (`/iflow-epic` plan → publish stage → pick children through normal lifecycle)
   - **Use auto mode** (`/iflow-auto` over a confirmed epic stage; cycle + review loop; when to stop/ask)
3. Link each how-to from Getting started / Home where useful; keep pages short.
4. Prefer linking existing design docs (e.g. `advanced-auto-mode.md`, epic guides) over copying them.

### Acceptance criteria

- [ ] How-to section in `zensical.toml` nav and builds on RTD / `uv run zensical build`
- [ ] At least **6** published how-to pages, including **epics** and **auto**
- [ ] Getting started (or Home) points readers at the how-to index
- [ ] No duplicate of full `issue-workflow.md`; how-tos stay procedural

### Out of scope

- Rewriting the whole workflow reference
- Translating every `04-designs-and-guides/` file into a how-to
- Video / interactive tutorials
- Non-English docs
