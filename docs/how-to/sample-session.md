---
title: A sample session
---

# A sample session

This page follows **one real issue** from `iflow pick` to `iflow cleanup`:
[#328 "location of worktrees"](https://github.com/jepegit/issue-flow/issues/328),
worked on in the issue-flow repository on 2026-09-24. It was recorded as it
happened and then trimmed. Output is shortened (long paths become `…` or
`<tmp>`), but nothing is made up.

Look for the **confirmation points**. They are the places where the agent
stopped and waited for the user; everything between them ran on its own.

!!! note "Two things to know"

    - The session ran in **Claude Code**. Cursor, opencode and Codex look a
      little different, but the steps and stops are the same.
    - #328 changed where worktrees are created. The worktree at the start of
      this session was made by the **old** code (next to the repo).

## 1. Pick the issue

**You type:**

```text
iflow pick
```

**The agent** checked the repository (`git fetch --prune`,
`issue-flow agent preflight`), looked for parked work and open epic issues
(none), and listed the open GitHub issues. Issues already tracked locally or
that depended on this session were left out. It printed:

> Preflight: on `main`, up to date with origin. The working tree has
> uncommitted **tracking files only** (status files from an earlier run). No
> parked work, no open epic candidates.
>
> | # | Issue | Labels / milestone | Why it ranks here |
> |---|---|---|---|
> | 1 | #328 location of worktrees | — | Close to recent work (worktree-first start, workspaces) |
> | 2 | #248 option for not stopping in a cycle | v.0.5.0 | Cycle behaviour; milestone |
> | 3 | #308 publish on success | — | Release flow |
> | 4 | #268 Improve skills | — | Broad; may need a split |
> | 5 | #100 Custom templates — let users override Jinja2 scaffolds | v.0.5.0 | Milestone |
>
> Which one? Reply with the issue number.
>
> Also: the tracking files on `main` must not end up on the new branch. Either
> **(a)** commit them on a small chore branch + PR first (recommended), or
> **(b)** leave them uncommitted on `main` for now.

!!! question "Confirmation point: which issue, and what about the dirty tree"

    `iflow pick` never chooses for you, even when one issue is the obvious
    candidate. It also refuses to start from a working tree with uncommitted
    changes until you decide what happens to them.

## 2. Branch, worktree and capture

**You type:**

```text
1, a
```

**The agent** committed the tracking files on a chore branch and opened a
small PR for them, then:

```text
$ issue-flow agent default-sync --json          → "action": "even"
$ issue-flow agent worktree-add 328 --slug worktree-location --json
{"path": "…/issue-flow-workspace/issue-flow-328",
 "branch": "328-worktree-location", "home_branch": "main",
 "created": true, "error": null}
$ issue-flow agent capture 328
wrote .issueflows/01-current-issues/issue328_original.md
```

Your own checkout stayed on `main`; the work happens in the sibling worktree
`../issue-flow-328` on branch `328-worktree-location`. Because `auto_plan` is
on (the default), pick went straight into planning.

## 3. Plan

**The agent** read the captured issue and the design notes, looked for
existing code to reuse, and wrote `issue328_plan.md`. No code was changed.
An excerpt of the real file:

```markdown
## Goal

Let users choose where issue worktrees go:

- **Repos inside a workspace folder** (a parent folder with `issueflow-workspace.toml`)
  keep today's behaviour: the worktree goes next to the repo, inside that folder.
- **Stand-alone repos** can use a **common worktrees folder** (e.g. `~/worktrees`)
  instead of cluttering the repo's parent folder.
- Anything unset or missing falls back to today's behaviour.

## Constraints

- **Default behaviour is unchanged.** Without the new settings, `worktree-add`
  still creates `../<repo>-<N>`.
  …

### Prior art

- `gitutils.worktree_path_for_issue(home, N)` → `home.parent / f"{home.name}-{N}"`.
  It is the single source of the path …
- `project.find_workspace_file(start)` walks up to `issueflow-workspace.toml`. …

## Approach

2. **One resolver,** `gitutils.resolve_worktree_location(…)`:

   | Situation | Worktree goes to | `reason` |
   | --- | --- | --- |
   | Repo inside a workspace and `worktrees_in_workspace = true` | `../<repo>-<N>` (in the workspace folder) | `workspace` |
   | `worktrees_dir` set, and the folder exists | `<worktrees_dir>/<repo>-<N>` | `worktrees_dir` |
   | `worktrees_dir` set but missing, or not absolute after expansion | `../<repo>-<N>` | `fallback: <why>` |
   | Nothing set | `../<repo>-<N>` | `sibling` |

   The resolver never creates the common folder …

## Open questions

1. **Names.** `worktrees_dir` + `worktrees_in_workspace`? … *Recommended: the two above.*
2. **Missing folder.** Fall back to the sibling path, or create the folder?
   *Recommended: fall back and print why.*
3. **Relative paths.** … *Recommended: treat it as invalid → fall back with a note.*
4. **Folder name inside the common folder.** Keep `<repo>-<N>` …? *Recommended: keep it.*
```

The agent summarised the plan in chat and ended with:

> Reply **Accept** to take my recommendations and start the build,
> **Revise** with your answers, or **Abort**.

!!! question "Confirmation point: approve the plan"

    This is the most important stop. The open questions are real design
    decisions (names, what happens when a folder is missing), and each comes
    with a recommendation. Nothing is built until you answer.

## 4. Build

**You type:**

```text
Accept
```

Because `auto_build` is on (the default), **the agent** went straight into the
build:

- started `issue328_status.md` with `- [ ] Done`;
- added the two settings, the resolver, and a `location` field in
  `worktree-add`'s output;
- ran the whole test suite, which caught something:

```text
FAILED tests/test_doc_configuration.py::test_all_settings_table_lists_every_config_key_once
AssertionError: missing: ['worktrees_dir', 'worktrees_in_workspace'], unknown: []
```

That test exists so that no setting ships undocumented. The agent added the
two settings to the configuration page and a "Where the worktree goes" section
to the worktrees how-to, updated three templates, and wrote 10 new tests.
Then it tried the feature for real in a throwaway home folder:

```text
$ issue-flow config set --global worktrees_dir '~/worktrees'
$ issue-flow agent worktree-add 6 --slug demo -C projects/demo
Created: <tmp>/home/worktrees/demo-6  (worktrees_dir)
Branch: 6-demo
Home: <tmp>/projects/demo (main)

# after deleting ~/worktrees:
$ issue-flow agent worktree-add 7 --slug demo -C projects/demo
Created: <tmp>/projects/demo-7  (fallback)
note  worktrees_dir '<tmp>/home/worktrees' does not exist; using the repo's parent folder
```

Full suite: 882 passed. `auto_close` is off (the default), so the build ended
with a hand-off instead of shipping:

> `auto_close` is off, so the build stops here. When you're ready, type
> `iflow close`.

## 5. Close

**You type:**

```text
iflow close
```

**The agent**, in order:

1. ran the essential tests (18 passed) and the full suite (882 passed) and
   checked lint;
2. left the version alone (no bump was asked for);
3. added a changelog entry under `## [Unreleased]` in `HISTORY.md`;
4. marked the status `- [x] Done` and moved the `issue328_*` files to
   `03-solved-issues/`;
5. committed, synced with `main` (`already up to date with origin/main`),
   pushed, and opened
   [PR #375](https://github.com/jepegit/issue-flow/pull/375) with
   `Closes #328`;
6. pulled `main` in your checkout and removed the worktree (clean tree), but
   kept the branch.

!!! note "Close does not merge"

    Without the `yolo` token, merging stays your decision. The agent waited
    for CI (all five checks passed) and told you to merge on GitHub, then run
    `iflow cleanup`.

## 6. Cleanup, first try: refused

**You type:**

```text
iflow cleanup
```

The PR had not been merged yet. **The agent** checked and stopped without
deleting anything:

> Cleanup stopped without deleting anything, because PR #375 hasn't been
> merged yet. Until it merges, its branch `328-worktree-location` counts as
> unmerged work, and cleanup never deletes that.

!!! question "Safety check: unmerged work is never deleted"

    Cleanup only removes branches whose work has landed on `main`. A branch
    with an open PR is left alone, however many times you ask.

## 7. Cleanup after the merge

**You type** (after merging on GitHub):

```text
merged 375 now
```

**The agent** confirmed the merge (`gh pr view 375` → merged as `097a7b2`),
classified the local branches, and asked **two separate questions**:

> **Phase A1 (safe):** `git pull --ff-only`, then `git fetch --prune`.
>
> **Phase A2 (force-delete, needs its own yes):** these branches need
> `git branch -D`. A squash merge leaves each branch's own commits off `main`,
> so `-d` always refuses them. Every commit on each branch has an equivalent
> on `origin/main`, and each PR is merged:
>
> | Branch | Tip | PR |
> |---|---|---|
> | `328-worktree-location` | `54da663` | #375 |
> | … 8 older branches … | | |
>
> To undo any deletion: `git branch <name> <tip>`.

!!! question "Confirmation point: two separate yeses"

    A yes to the safe step never implies a yes to `git branch -D`. The tip
    SHAs are printed so every deletion can be undone.

With both answered **yes**, `main` moved to the merged commit, and the
landed branches were deleted:

```text
097a7b2 feat: choose where issue worktrees go (worktrees_dir) (#375)
328-worktree-location 54da663 -D
…
```

A branch whose PR was still open was kept.

## Afterwards

The very next issue started (the one that produced this page) was the first
to use the new code. Its `worktree-add` reported `"location": "workspace"`,
because this repository lives in a workspace folder.

**In total you typed seven short messages:** `iflow pick`, `1, a`, `Accept`,
`iflow close`, `iflow cleanup`, `merged 375 now`, and one answer to the two
cleanup questions. You also merged the PR on GitHub yourself.

## Related

- [Work one issue end-to-end](work-one-issue.md): the same steps as a checklist
- [Concepts](../concepts.md): the lifecycle, the folders, where the agent stops
- [Work in a sibling worktree](worktrees.md): including the new `worktrees_dir`
- [After a squash merge](after-squash-merge.md): cleanup in detail
