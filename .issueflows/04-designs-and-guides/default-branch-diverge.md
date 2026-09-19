# Default-branch diverge (ff-only vs unpushed home commits)

**Issue:** [#303](https://github.com/jepegit/issue-flow/issues/303)
**Status:** decided 2026-09-19, implemented in the same issue.
**See also:** [`separate-workspaces.md`](separate-workspaces.md) (#255),
[`local-branch-cleanup.md`](local-branch-cleanup.md) (#243).
Changelog-only PR conflicts (#260 / #288) are a different class.

## Context

Worktree-first start keeps **home on the default branch** and used to
require `git pull --ff-only` before `worktree-add`. Cleanup A1 and
switchback do the same pull. That dead-ends when home is both ahead and
behind `origin/<default>` — typically an unpushed `.issueflows/` chore
(epic `Published: #N`, doctor, scaffold) plus a squash on origin, often
made worse by a local merge “to catch up”.

`worktree-add` already starts from fetched `origin/<default>`. The issue
branch is fine. The pain is **home default hygiene**.

## Decisions

1. **Starting work does not require a clean FF of home default.**
   Fetch, classify with `issue-flow agent default-sync`, FF only when
   `action` is `even` / `ff_only`, otherwise print and continue.
2. **`default-sync` is classify-only.** No mutate. Skills choose the
   recovery.
3. **Never** rebase default, `push --force` default, or push default to
   skip CI.

| `action` | Offer |
| --- | --- |
| `even` / `ff_only` | `git pull --ff-only` is safe |
| `report_ahead` | Print unique commits; do not silent-push |
| `tracking_pr` | Merge origin or cherry-pick onto a chore branch, then a tiny PR |
| `replay_tracking` | Replay tracking onto `origin/<default>` (chore + PR); no stacked merge |
| `stop_product` | Stop. User decides. Includes `HISTORY.md` / lock / source |

4. **Prevent:** epic `Published: #N`, doctor housekeeping, and scaffold
   updates do not sit unpushed on home default.
5. **`apply-changelog`** still writes `HISTORY.md` on default after merge
   (#260). A leftover HISTORY commit plus a moved origin classifies as
   `stop_product`.
