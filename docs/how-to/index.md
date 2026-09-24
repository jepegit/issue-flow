---
title: How-to guides
---

# How-to guides

Short, task-oriented paths. Each page is goal → steps → related links — not a
full command reference. Unfamiliar terms (focus issue, off-path, yolo, epic
stage …) are explained in [Concepts](../concepts.md). For every slash command in detail, see
[Command reference](../issue-workflow.md).

## Quick recipes

Label a batch of small issues and ship them hands-off
([Run a cycle of issues](cycle.md)):

```text
iflow review yolo    # propose yolo labels; confirm once; apply
iflow cycle yolo     # process every open yolo-labelled issue
```

Plan a large change as an epic ([Create and run epics](epics.md)):

```text
iflow epic 42                 # draft .issueflows/05-epics/epic42_plan.md
iflow epic 42 publish         # or: publish stage 1
iflow cycle epic 42 stage 1   # optional: batch the published stage
```

Not sure what to work on? `iflow pick` shows parked work first, then open
GitHub issues ranked for you.

## Everyday

| Guide | When to use it |
| --- | --- |
| [Work one issue end-to-end](work-one-issue.md) | The normal loop: pick → plan → build → close → cleanup |
| [Park and resume](park-and-resume.md) | Stop mid-issue without losing state |
| [After a squash merge](after-squash-merge.md) | PR landed; tidy local (and optionally remote) branches |
| [Work in a sibling worktree (or stay inplace)](worktrees.md) | Default `../repo-N` start; `worktree_first` knob; `inplace` / `worktree` tokens |

## Faster

| Guide | When to use it |
| --- | --- |
| [Fast-track a small issue](yolo.md) | Low-risk change: one confirm, then hands-off |
| [Run a cycle of issues](cycle.md) | Batch many yolo-fit issues under one confirm |

## Bigger changes

| Guide | When to use it |
| --- | --- |
| [Create and run epics](epics.md) | A change too big for one issue |
| [Use auto mode](auto-mode.md) | Unattended epic stage with adversarial review |

## Team and repos

| Guide | When to use it |
| --- | --- |
| [Use issue-flow in a folder of repos](workspaces.md) | Parent folder + sibling repos: bootstrap / init / update |
| [Refresh dirty open PRs](pr-sync.md) | Open PRs went dirty after another merge |

## Extras

| Guide | When to use it |
| --- | --- |
| [Use pstack skills](pstack-skills.md) | Opt-in unslop / tdd / blast-radius and friends |

## Elsewhere

- **Setting up:** [Choose a mode](choose-a-mode.md) (`novice` / `simple` /
  `standard`) now lives under **Getting started**.
- **AI agents:** [Upgrade, init, and workspace](for-agents.md) has its own
  **For agents** tab.
