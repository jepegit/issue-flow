---
title: Home
---

# issue-flow

Agents should behave. Let them follow the issue flow.

**issue-flow** gives your AI coding agent a fixed way of working: every change
starts from a GitHub issue, gets a written plan that **you approve before any
code is touched**, and lands as a pull request with a changelog entry. The
state of each issue is kept in plain markdown files in your repository, so the
work survives across chat sessions and the next agent can pick it up. It works
with **Cursor, Claude Code, opencode, and Codex**.

It may slow you down a little compared with letting an agent loose. Maybe that
is a good thing.

## How it works

In your editor's chat window:

| Type this | What happens |
|---|---|
| `iflow pick` | Shows you the open GitHub issues, you choose one, it creates a branch |
| `iflow plan` | Writes a plan and **stops** for you to approve it |
| `iflow build` | Implements the approved plan |
| `iflow close` | Runs tests, updates the changelog, commits, pushes, opens a pull request |
| `iflow cleanup` | After the PR is merged: back to the main branch, tidy up local branches |

Forgot where you are? Type `iflow` and it runs the next step. For small issues,
larger changes split into stages, and batch runs, see the
[How-to guides](how-to/index.md).

## Start here

<div class="grid cards" markdown>

-   **New to issue-flow**

    ---

    Install it, scaffold your project, and work your first issue. No
    experience with agentic coding needed.

    [:octicons-arrow-right-24: Getting started](getting-started.md)

-   **Want to do something specific**

    ---

    Short task guides: one issue end-to-end, a quick yolo fix, a batch of
    issues, a staged epic, a folder of repos.

    [:octicons-arrow-right-24: How-to guides](how-to/index.md)

-   **You are an AI agent**

    ---

    Upgrade vs `update`, global init, workspaces, and the short map in
    [llms.txt](llms.txt).

    [:octicons-arrow-right-24: For agents](how-to/for-agents.md)

</div>

The terms used throughout these docs (focus issue, off-path, yolo, epic …)
are explained in [Concepts](concepts.md).

## Install

```bash
uv tool install issue-flow
cd your-project
issue-flow init
```

issue-flow also needs [Git](https://git-scm.com/downloads) and the
[GitHub CLI](https://cli.github.com/) (`gh`). [Getting started](getting-started.md)
covers installing [uv](https://docs.astral.sh/uv/), the beginner-friendly
`--mode novice`, and letting the agent finish the setup with `iflow setup`.

## License

issue-flow is released under the
[MIT License](https://github.com/jepegit/issue-flow/blob/main/LICENSE).
