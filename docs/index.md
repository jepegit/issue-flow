---
title: Home
---

# issue-flow

Agents should behave. Let them follow the issue flow.

**issue-flow** scaffolds a lightweight issue-tracking workflow into your project
so that AI coding agents can pick up GitHub issues, plan work, and land PRs in a
consistent way. It supports **Cursor, Claude Code, opencode, and Codex** via
`--editor` (see [Editor support](editors.md)); the examples below use the
default, Cursor. 

## Why

I guess it is just a matter of taste. If you are familiar with coding using agents and harnesses, `issue-flow` could very well slow you down. But...

Maybe that is a good thing?

## What it does

Running `issue-flow init` in your project root creates:

```text
your-project/
  .issueflows/
    00-tools/                # Helper scripts for agents
    01-current-issues/       # Active issue markdown files
    02-partly-solved-issues/ # Parked / in-progress issues
    03-solved-issues/        # Completed issues archive
    04-designs-and-guides/   # Durable project context and decisions
      this-project.md        # Hand-editable project brief (created if missing)
    05-epics/               # Staged epic plans (epic<N>_plan.md)
  .cursor/
    skills/                  # Agent Skills (/iflow, /iflow-pick, /iflow-init,
                             # /iflow-plan, /iflow-build, /iflow-close, ...)
    rules/
      issueflow-rules.mdc    # Always-on Cursor rule for the workflow
  AGENTS.md                  # Workflow rules (managed block; shared by all editors)
  docs/
    issue-workflow.md        # Human-readable overview of the workflow
```

The exact layout depends on which editor(s) you scaffold for — see
[Editor support](editors.md). Generated files are written non-destructively:
`AGENTS.md` is a managed block inside your own file, and issue markdown under
`.issueflows/` is never touched by `init` or `update`.

## Installation

Requires Python and [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv tool install issue-flow
```

Or add it as a dev dependency to your project: `uv add --dev issue-flow`.

The scaffolded workflows shell out to
[Git](https://git-scm.com/downloads) and the
[GitHub CLI (`gh`)](https://cli.github.com/) (run `gh auth login` once after
installing). `issue-flow init` checks for both up front and prints install
hints before it does anything; bypass the prompt in automation with
`--skip-dep-check`.

## Quick start

```bash
cd your-project
issue-flow init
```

That's it. Open the project in your editor and start with `/iflow` (or type
`iflow` in chat when a slash is awkward on your keyboard) — or step through the
linear path explicitly:

1. `/iflow-init 42` — pulls GitHub issue #42 into
   `.issueflows/01-current-issues/` and archives older issues.
2. `/iflow-plan` — drafts `issue<N>_plan.md` (Goal / Constraints / Approach /
   Files to touch / Test strategy / Open questions) and stops for your
   confirmation.
3. `/iflow-build` — reads the confirmed plan and implements it.
4. `/iflow-close` — runs tests, optionally bumps the version, appends a
   `HISTORY.md` entry, updates status files, commits, pushes, and opens a PR.
5. `/iflow-cleanup` — after the PR merges, switches to the default branch,
   fast-forwards, prunes, and deletes the merged local branch.

Plus a few off-path commands (never auto-dispatched): `/iflow-pick` (choose the
next issue), `/iflow-pause` (park work), `/iflow-yolo` (hands-off chain for
small issues), `/iflow-fix` (iterative fixes session), `/iflow-status`
(read-only overview), `/iflow-epic` (staged epic plan + publish),
`/iflow-cycle` (batch yolo queue), `/iflow-review` (label open issues),
`/iflow-doctor` (scaffold health check), and `/iflow-archive` (condense the
solved archive). The full lifecycle is described in
[The workflow](issue-workflow.md).

## Recipes

Short paths for common multi-issue work. Fuller examples live in the
scaffolded [workflow doc](issue-workflow.md) after `issue-flow init`.

**One issue, linear path** — `/iflow-init` → `/iflow-plan` → `/iflow-build` →
`/iflow-close` → `/iflow-cleanup` (or just `/iflow` between steps).

**One small issue, hands-off** — `/iflow-yolo <N>` (or pick an issue that
already has the `yolo` label via `/iflow-pick`).

**Label and ship a batch**

```text
iflow review yolo    # propose yolo labels; confirm once; apply
iflow cycle yolo     # process every open yolo-labelled issue
```

**Plan a large change as an epic**

```text
iflow epic 42                 # draft .issueflows/05-epics/epic42_plan.md
iflow epic 42 publish         # or: publish stage 1
iflow cycle epic 42 stage 1   # optional: batch the published stage
```

**Front door when you have not chosen yet** — `/iflow-pick` (parked work first,
else ranked open GitHub issues).

## Where to go next

- **[The workflow](issue-workflow.md)** — the human-readable walkthrough of the
  full issue lifecycle (also scaffolded into your project).
- **[CLI reference](cli.md)** — every `issue-flow` command, including the
  deterministic `agent` helpers.
- **[Configuration](configuration.md)** — `.env` variables,
  `.issueflows/config.toml`, modes, skill levels, and the optional caveman /
  grill-me skills.
- **[Editor support](editors.md)** — what gets scaffolded per editor, and how
  multi-root workspaces resolve the right repo.
- **[Graphify integration](graphify.md)** — an optional knowledge graph of your
  codebase that agents read instead of grepping.
- **[Developing](developing.md)** — working on issue-flow itself.
- **[Changelog](changelog.md)** — release notes.
- **[Acknowledgements](acknowledgements.md)** — the open-source projects
  issue-flow builds on.

## License

issue-flow is released under the
[MIT License](https://github.com/jepegit/issue-flow/blob/main/LICENSE).
