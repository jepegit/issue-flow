---
name: iflow-workspace-git
description: >-
  Git status (and optional fetch --prune) across every workspace member.
  Not the issue-flow lifecycle status command.
disable-model-invocation: true
issue-flow-version: 0.5.17
---

# issue-flow — workspace git (`/iflow-workspace-git`)

Follow this skill for a **git hygiene snapshot** of every scaffolded
workspace member (branch, dirty paths, ahead/behind). Do **not** confuse
this with `/iflow-status` / `issue-flow workspace status` (issue-flow
lifecycle + GitHub).

**Invoke:** type `iflow git` in chat, or `/iflow-workspace-git` from the
slash menu (`iflow-workspace-git` / `iflow workspace-git` also work).



### MODEL & EXECUTION DIRECTIVE


**Profile: economy** — Prioritize speed and token economy over deep reasoning.

In Cursor: use **Auto** or a fast model before invoking this step.



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
- **GitHub:** pass an explicit repo on every `gh` call — never rely on `gh`'s implicit cwd default. For most commands use `--repo <owner/repo>`; **exception:** `gh repo view` takes the repo as a **positional** arg (`gh repo view <owner/repo> …`) and rejects `--repo`.
- **Paths:** all `.issueflows/…` paths are under `<project_root>`.

When `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` exists, read it for layout and cross-repo guidance.


## Input

- **(nothing)** or **`status`** — `issue-flow workspace git status [--json]`.
  No fetch.
- **`fetch`** — `issue-flow workspace git fetch [--json]`, then status.

## Instructions

1. Resolve the workspace (toml walk-up). If there is no
   `issueflow-workspace.toml`, stop and point at `issue-flow workspace
   init` / `bootstrap`. Do **not** guess sibling folders.
2. If the user passed `fetch`, run `issue-flow workspace git fetch --json`
   first. Report per-member ok/fail. Continue after a single-member
   failure.
3. Run `issue-flow workspace git status --json`. Present each member:
   name, branch, ahead/behind vs `origin/<default>`, clean/dirty, dirty
   paths. Note locked skips.
4. Never pull, rebase, merge, push, stash, or reset. Those stay
   per-repo (`default-sync`, `/iflow-cleanup`).

## Constraints

- Off-path. Never auto-dispatch from `/iflow`, `/iflow-build`, or
  `/iflow-close`.
- Status is read-only. Fetch is `--prune` only.
- Locked members are skipped, same as other `workspace` commands.
