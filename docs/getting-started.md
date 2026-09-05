---
title: Getting started
---

# Getting started

This page is for the first hour: you have heard of issue-flow, you have an
editor with an AI agent in it (Cursor, VS Code with Copilot, Claude Code,
opencode, Codex), and you want to get to the point where you can say
"work on issue 12" and have something sensible happen.

You do not need to have used agentic coding before. Two of the four steps below
happen in a terminal; the rest happens in your editor's chat window.

## 1. Install uv, then issue-flow

issue-flow is a Python CLI. The easiest way to install it is with
[uv](https://docs.astral.sh/uv/), a Python package manager that also installs
Python for you.

=== "macOS / Linux"

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    uv tool install issue-flow
    ```

=== "Windows"

    ```powershell
    winget install --id=astral-sh.uv -e
    uv tool install issue-flow
    ```

Check it worked:

```bash
issue-flow --version
```

You also need [Git](https://git-scm.com/downloads) and the
[GitHub CLI](https://cli.github.com/) (`gh`), because issue-flow's whole
workflow is built around GitHub issues and pull requests. If you are not sure
whether you have them, skip ahead — step 3 will tell you exactly what is
missing.

## 2. Scaffold your project

Pick one of the two starting points.

### Starting a brand-new project

Make a folder and scaffold into it:

```bash
mkdir my-project
cd my-project
issue-flow init --mode novice
```

The folder does not need to be a Python project or a git repository yet —
step 3 handles that.

### Adding issue-flow to an existing project

```bash
cd my-existing-project
issue-flow init --mode novice
```

`init` is non-destructive: it adds a `.issueflows/` tracking tree and your
editor's skill files, appends a managed block to `AGENTS.md`, and never
overwrites your own content.

!!! tip "Why `--mode novice`?"

    `novice` installs the straight-line workflow plus the safety nets and
    leaves out the hands-off and batch automation, so you get about a dozen
    commands instead of twenty. It also writes settings that **stop at each
    step and ask you** rather than chaining one step into the next.

    Nothing is locked in. When the flow feels familiar, run
    `issue-flow init --mode standard` to get the full surface. See
    [Configuration](configuration.md#modes) for what each mode contains.

## 3. Let the agent finish the setup

Open the project in your editor and type this in the chat window:

```text
iflow setup
```

(or `/iflow-setup` from the slash menu — both work).

The agent checks what is still missing and walks you through it, one
confirmation at a time:

- no Python project yet → `uv init`
- not a git repository → `git init` and a first commit
- `gh` not signed in → it asks *you* to run `gh auth login`, because that opens
  a browser and has to be done by a human
- no GitHub repository → `gh repo create`

Nothing runs without you approving it first, and it never installs tools or
signs in on your behalf — for those it prints the command and stops.

You can get the same report without the conversation:

```bash
issue-flow agent setup-status
```

It only reads; it changes nothing.

## 4. Work on your first issue

Now the ordinary loop. In the chat window:

| Type this | What happens |
|---|---|
| `iflow pick` | Shows you the open GitHub issues, you choose one, it creates a branch |
| `iflow plan` | Writes a plan and **stops** for you to approve it |
| `iflow build` | Implements the approved plan |
| `iflow close` | Runs tests, updates the changelog, commits, pushes, opens a pull request |
| `iflow cleanup` | After the PR is merged: back to the main branch, tidy up local branches |

If you forget where you are, just type `iflow` — it works out which step is
next and runs it.

No issues on GitHub yet? Type `iflow issue` and the agent will help you write a
well-specified one first.

## Where to go next

- **[The workflow](issue-workflow.md)** — every command in detail.
- **[Configuration](configuration.md)** — the settings `--mode novice` chose
  for you, and how to change them.
- **[Editor support](editors.md)** — what gets scaffolded for each editor.
