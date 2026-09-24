---
title: Troubleshooting
---

# Troubleshooting

Common problems in the first hours with issue-flow, each as
**symptom → cause → fix**. If yours is not here, `issue-flow agent
setup-status` and `issue-flow doctor` are good first checks: both only read,
and they report what is missing or out of place.

## `gh` is not signed in

**Symptom:** capture, pick or close stops with an authentication error, or
`gh` asks you to run `gh auth login`.

**Cause:** the GitHub CLI has no token for this machine. issue-flow reads and
writes issues and pull requests through `gh`.

**Fix:** run this yourself in a terminal (it opens a browser, so the agent
cannot do it for you):

```bash
gh auth login
gh auth status      # check
```

## `issue-flow: command not found`

**Symptom:** `uv tool install issue-flow` succeeded, but the shell cannot find
`issue-flow`.

**Cause:** uv's tool directory is not on your `PATH` yet.

**Fix:**

```bash
uv tool update-shell    # adds the tool directory to your shell profile
```

Then open a new terminal. `issue-flow --version` should work.

## The commands don't show up in the editor

**Symptom:** `/iflow-plan` is not in the slash menu, or typing `iflow plan`
does nothing special.

**Cause:** usually one of these:

- the project was scaffolded for a different editor (the default is Cursor,
  so a Claude Code user needs `--editor claude`);
- the editor has not reloaded since the files were written.

**Fix:** check which folder exists (`.cursor/`, `.claude/`, `.opencode/`,
`.codex/`). If yours is missing, scaffold it:

```bash
issue-flow update --editor claude     # or opencode / codex / all
```

Then reload the editor window. See [Editor support](../editors.md).

## The commands behave like an older version

**Symptom:** a command does not know an option the docs describe, or behaves
the way it did before an upgrade.

**Cause:** upgrading the package does not rewrite the files in your project.
Every generated `SKILL.md` records the version that wrote it
(`issue-flow-version:` at the top).

**Fix:** refresh the project after every upgrade. These are two different
commands:

```bash
uv tool upgrade issue-flow    # the package
issue-flow update             # the files in this project
```

For a folder of several repos, run `issue-flow workspace update` from the
parent instead. See [Upgrade, init, and workspace](for-agents.md).

## A merged branch is "several commits ahead of main"

**Symptom:** after your PR was merged, `git status` on the old issue branch
says it is ahead of `main`, and `git branch -d` refuses to delete it.

**Cause:** PRs are squash-merged. GitHub puts one *new* commit on `main`, so
your branch's own commits never appear there, even though the work did land.

**Fix:** run `iflow cleanup`. It recognises these "squash-landed" branches and
offers to delete them with `git branch -D`, behind a second confirmation that
lists each branch's tip SHA. See [After a squash merge](after-squash-merge.md).

## `iflow` works on the wrong issue, or several issues are "current"

**Symptom:** the dispatcher picks an issue you did not expect, or
`.issueflows/01-current-issues/` holds files for more than one issue.

**Cause:** the focus issue comes from the branch name first (`42-fix-login`
means issue 42), then from the single group in `01-current-issues/`.
Leftovers from earlier work make the second rule ambiguous.

**Fix:** switch to the right issue branch, or tidy the folder:

```bash
issue-flow doctor              # report only
issue-flow doctor --fix        # safe repairs: create missing folders, sweep leftovers
```

Or type `iflow doctor` in chat. Finished groups (status says `- [x] Done`)
move to `03-solved-issues/`, unfinished ones to `02-partly-solved-issues/`.
Nothing is deleted.

## `git pull --ff-only` is refused on the default branch

**Symptom:** cleanup or close reports `Not possible to fast-forward` on
`main`.

**Cause:** your local `main` has commits that are not on `origin/main`,
often a tracking-file commit made directly on `main`.

**Fix:** let issue-flow classify the situation. It only reads:

```bash
issue-flow agent default-sync --json
```

Follow its recommended `action`. Usually that means moving the stray commit
to a small chore branch and PR. Never force-push, rebase, or push `main`
directly to get past this.

## An open PR became `CONFLICTING` after another merge

**Symptom:** a PR that was fine now shows a conflict, usually in `HISTORY.md`.

**Cause:** another PR merged first and added its own changelog entry in the
same place.

**Fix:** run `iflow pr-sync`. It rebases the affected PR branches, keeps
both changelog entries, and pushes with `--force-with-lease` after one
confirmation. See [Refresh dirty open PRs](pr-sync.md).

## Settings seem to be ignored on WSL or Windows

**Symptom:** a user-wide setting you set does not apply.

**Cause:** WSL and native Windows are separate machines for issue-flow. WSL
reads `~/.config/issue-flow/config.toml`; native Windows reads
`%APPDATA%\issue-flow\config.toml`. A project's own `.issueflows/config.toml`
also beats the user-wide file.

**Fix:** check which file and which values are in effect:

```bash
issue-flow config show --global     # the user-wide file for this environment
issue-flow config show              # what this project actually uses
```

See [How settings are resolved](../configuration.md#how-settings-are-resolved).

## Related

- [Getting started](../getting-started.md)
- [Concepts](../concepts.md)
- [Command reference](../issue-workflow.md)
