---
title: Upgrade, init, and workspace (for agents)
---

# Upgrade, init, and workspace (for agents)

## Goal

A human asked you (an AI coding agent) to **upgrade issue-flow**, **install
it globally**, or **set up a workspace**. Use this page. Do not invent a
different command order.

Machine index: [llms.txt](../llms.txt). Folder-of-repos detail:
[Use issue-flow in a folder of repos](workspaces.md).

## Do not confuse these

| The human said | That means | Not this |
| --- | --- | --- |
| Upgrade / latest version / update the tool | Upgrade the **package**, then refresh scaffolds | `issue-flow update` alone (that only rewrites skill files from the *already installed* CLI) |
| Init globally / install for all projects | Plant the **user-global** `iflow-init` skill, then `iflow init` from a folder | `issue-flow init` on a parent folder of repos |
| Set up this workspace / folder of repos | `workspace bootstrap` / `init` / `update` from the **parent** | `issue-flow init` at the parent (no shared `.issueflows/` there) |
| Refresh skills after an upgrade | `issue-flow update` (one repo) or `workspace update` (all members) | `uv tool upgrade` again |

`issue-flow update` never upgrades the PyPI package. `uv tool upgrade
issue-flow` never refreshes a project's `.cursor/skills/` by itself.

## Upgrade to the latest version

The CLI must be on `PATH` (`uv tool install issue-flow` once). Then:

```bash
uv tool upgrade issue-flow
issue-flow --version
```

Then refresh scaffolds so skills match the new CLI:

```bash
# one repo
issue-flow update

# parent folder that already has issueflow-workspace.toml
issue-flow workspace update
```

If the install is an **editable** local checkout (`uv tool install --force
--editable .`) and `pyproject.toml` dependencies changed, re-run
`uv tool install --force --editable .` — `uv tool upgrade` does not
re-resolve that venv.

Confirm before running upgrade/update unless the human already said to do it.

## Initialize issue-flow globally

User-global `iflow-init` is written on the first successful `issue-flow init`
or `issue-flow update` (or `uvx issue-flow workspace bootstrap --yes …`) on
that machine. After that, chat `iflow init` works in a folder with no
project scaffold.

First machine (CLI not installed yet):

```bash
uv tool install issue-flow
cd some-project          # or a parent folder of git repos
issue-flow init .        # one repo
# or:
issue-flow workspace bootstrap --yes --default <main-repo>
```

Then, from any later folder, type **`iflow init`** (or `/iflow-init`). That
skill classifies: single project vs parent folder. Follow it. Do not
`issue-flow init` a parent that only holds sibling repos.

## Set up a workspace

From the **parent folder** (example: `batbase-workspace`):

```bash
# first time — scaffold git siblings + write issueflow-workspace.toml
issue-flow workspace bootstrap --yes --default <main-repo>

# members already have .issueflows/ — toml only, then refresh
issue-flow workspace init --default <main-repo>
issue-flow workspace update

# toml already exists — refresh only
issue-flow workspace update
```

Peek first: `issue-flow workspace bootstrap --json` (no writes).

Never write `.issueflows/` on the parent. Never `git init` children from
this path — point those folders at `iflow setup`.

Full recipe: [Use issue-flow in a folder of repos](workspaces.md).

## After any of the above

- One repo: `iflow pick` (or `iflow capture <N>`).
- Workspace: repeat lifecycle **per repo**. The toml `default` is only a
  fallback when a command runs from the parent.
- After a non-yolo close: `issue-flow agent pr-ready [N] [--watch]` answers
  “can this PR merge yet?” — classify only, never merges.

## Related

- [Getting started](../getting-started.md) — human first hour
- [CLI reference](../cli.md) — flags
- [Editor support](../editors.md) — multi-root resolve
