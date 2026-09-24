---
title: Use issue-flow in a folder of repos
---

# Use issue-flow in a folder of repos

## Goal

You have a **parent folder** that contains several git repositories (for
example `batbase-workspace/batbase` and `batbase-workspace/batbase-loader`).
You want each repo's issue-flow skills updated, and optionally an
`issueflow-workspace.toml` so commands run from the parent know which repo
is the default.

Each repo keeps its **own** `.issueflows/`. The parent folder does not get
a shared tracker.

## Which command?

Run these from the **parent folder** (`batbase-workspace`), not from inside
one repo.

| You want… | Command |
| --- | --- |
| First time: scaffold every git sibling **and** write the toml | `issue-flow workspace bootstrap --yes --default batbase` |
| Repos already have `.issueflows/`; only write the toml | `issue-flow workspace init --default batbase` |
| Toml exists; refresh skills/rules in every member | `issue-flow workspace update` |
| Status / doctor / dirty-tree for every member | `issue-flow workspace status` / `doctor` / `dirty` |
| Peek before writing (no `init`, no toml) | `issue-flow workspace bootstrap --json` |

`--default` is the member folder name lifecycle commands use when you are
standing in the parent (outside any one repo). Required when there is more
than one git member. Pick the “main” repo.

## Worked example

```text
batbase-workspace/
  batbase/           # git repo
  batbase-loader/    # git repo
```

### A. Neither repo has issue-flow yet

```bash
cd batbase-workspace
issue-flow workspace bootstrap --yes --default batbase
```

That runs `issue-flow init` in each **own-git** child, then writes
`issueflow-workspace.toml`. Non-git folders are skipped (use
`iflow setup` inside those first). Drop `--yes` to classify only.

In the editor, type `iflow init` from the parent folder — same path, with a
confirm before `--yes`.

### B. Both repos already have `.issueflows/`

```bash
cd batbase-workspace
issue-flow workspace init --default batbase
issue-flow workspace update
```

After an `uv tool upgrade issue-flow`, you only need the second line.

### C. Toml already exists

```bash
cd batbase-workspace
issue-flow workspace update
```

Works from a member repo too — the command walks up to find
`issueflow-workspace.toml`.

A **new clone** is not picked up by `update` alone. Re-run
`issue-flow workspace bootstrap --yes --default <name>` (or
`workspace init --default <name> --force`) so `members` matches the
current siblings. Classify-only lists names on disk that are missing
from the toml.

Optional: `workspace init --code-workspace` or
`workspace bootstrap --yes --code-workspace` also adds member folders to
a VS Code/Cursor `*.code-workspace` file (the sole file in the parent, or
`<folder>.code-workspace` if none). Extra folders are kept unless
`--force`. Off by default — `--yes` does not turn this on. Two such
files: pass `--code-workspace-path`.

## One repo only

Stay inside that repo:

```bash
cd batbase
issue-flow update
```

## After the toml exists

Open the parent (or a multi-root editor workspace). Lifecycle commands
resolve the target repo in this order: `root:` / `repo:` hints, then
`issue-flow agent resolve`, then “exactly one issue branch / one scaffold”,
then the **default** member. They never guess between siblings, and
never let `git` or `gh` infer the repository from the current directory
alone. Design notes:
[multi-repo-workspaces.md](https://github.com/jepegit/issue-flow/blob/main/.issueflows/04-designs-and-guides/multi-repo-workspaces.md).

Work **per repo**: `iflow pick` and close in `batbase` do not touch
`batbase-loader`. Repeat in the other repo when needed.

**Workspace-wide inspect** (from the parent, or with trailing `workspace`):

```bash
issue-flow workspace status --local
issue-flow workspace doctor
issue-flow workspace dirty          # after workspace update
iflow cleanup workspace             # opt-in sequential per-repo cleanup
```

`workspace doctor` is audit-only. Repair one member:
`issue-flow doctor --fix -C batbase`. After `workspace update`,
`workspace dirty` lists members whose tree changed; land those commits
per repo (chore branch if you are on default). There is no auto-push.

## Related

- [Upgrade, init, and workspace (for agents)](for-agents.md) — package vs scaffold; global init
- [CLI: `workspace` commands](../cli.md#issue-flow-workspace-init)
- [Editor support — multi-root](../editors.md#multi-root-workspaces)
- [Work in a sibling worktree](worktrees.md) — issue worktrees (`../repo-N`),
  not the same as this parent-folder registry
