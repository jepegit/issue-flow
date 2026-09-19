# Issue #303: Default-branch diverge: ff-only fails after unpushed home commits + a squash merge

Source: https://github.com/jepegit/issue-flow/issues/303

## Original issue text

## Problem / context

Worktree-first start (`/iflow-pick`, `/iflow-issue`, #255) tells the agent to keep **home on the default branch** and `git pull --ff-only` before `worktree-add`. `/iflow-cleanup` A1 does the same pull after merge.

That recipe **dead-ends** when home default is both ahead and behind `origin/<default>`:

```
## master...origin/master [ahead 2, behind 1]
fatal: Not possible to fast-forward, aborting.
```

Seen on jepegit/cellpy after the CLI-plugin / connectors sequence (#1042 → #1055/#1058 → #1060 / PR #1061). The agent stopped, the human had to choose merge-vs-reset, then later **merge + push default directly** (bypassed “PR required” / essential checks). Skills never explained *why* or what the safe next command was.

## Why it happens

Three things stack:

1. **Unique commits land on home default and stay unpushed.** Epic publish / housekeeping wrote `Published: #1058` on `.issueflows/05-epics/epic1042_plan.md` as a commit on local `master` (not on an issue branch, not in a PR). Same class of miss: issue-flow scaffold commits on default.
2. **Origin moves by squash.** The issue PR squash-lands a *new* commit on `origin/<default>`. Home is now **behind**.
3. **A local merge to “catch up” makes it worse.** When ff-only already failed (behind #1059), the agent merged `origin/master` into home to keep the chore. That merge commit is also unique. After the next squash (#1061), home was **ahead 2 (chore + merge) / behind 1**.

`git pull --ff-only` is correct *when home has no unique commits*. It cannot reconcile “I have a line of epic tracking you don’t” + “you have a squash I don’t”. Cleanup then prints the refusal and stops. The human hears “we need to pull and push” with no skill text for: classify ahead commits, don’t rebase/force-push default, don’t push default to skip CI.

`worktree-add` in this incident created the issue branch from `origin/master` anyway, so the issue PR was fine. The pain is **home default hygiene**, not the issue branch.

Related but not the same: #255 (keep home on default), #270 (worktree struggle), #243 (cleanup `-d` vs squash). Changelog-only PR conflicts (#260 / #288) are a different conflict class.

## Spec / suggested solution

### Prevent

- **Do not leave unique commits on the default branch.** Epic `Published: #N`, doctor repairs, and scaffold updates should go on the issue/chore branch (or a tiny dedicated PR), never sit unpushed on home default.
- **`worktree-add` always starts from fetched `origin/<default>`**, not local default HEAD. Starting work must not require home to be ff-able.
- After `/iflow-close` / switchback: if home default is **ahead** of origin, **report the unique commits** (oneline + paths). Do not silently push default.

### Recover (pick / cleanup / switchback)

When `git pull --ff-only` fails, classify `origin/<default>..HEAD`:

| Ahead commits | Action |
| --- | --- |
| Only `.issueflows/` / tracking docs | Offer: merge `origin/<default>` then **open a tiny PR** (or cherry-pick onto a chore branch). Do **not** push default directly. |
| Product / lock / HISTORY | Stop. Do not merge onto default. User decides. |
| Ahead is only an obsolete local merge whose tree matches origin plus tracking | Prefer reset/replay of the tracking commit onto `origin/<default>` over stacking another merge. |

Never: rebase default, `push --force` default, or treat “pull and push” as ff-only.

### Skill / CLI text

- `/iflow-cleanup` A1: if ff-only fails, print ahead/behind SHAs and the table above; do not only dump `fatal: Not possible to fast-forward`.
- Optional CLI: `issue-flow agent default-sync --json` (classify + recommended action, no mutate) for pick/cleanup to call.

## Acceptance criteria

- Starting an issue via worktree does not require a clean ff of home default.
- An unpushed `Published: #N` line cannot produce a second “merge origin into master and push master” incident without the skill naming the recovery.
- Cleanup/switchback never imply force-push or CI-skipping push to default.

## Out of scope

- Changing GitHub squash-merge policy.
- Auto-push to default.
- HISTORY multi-PR conflicts (#260 / #288).
