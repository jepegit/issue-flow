# Issue #240: Changelog conflicts

Source: https://github.com/jepegit/issue-flow/issues/240

## Original issue text

When working on several issues at the same time we often end up with merge conflict for PRs on GitHub. And the PR can not be auto merged after CI.

## Comments (curated summary)

- **Additional tasks**:
  - **Rebase before merge in `/iflow-close`**: after push and before `gh pr merge`, fetch `origin/<default>` and rebase the issue branch (or `merge --ff-only` when possible); if clean, `git push --force-with-lease` and then merge. Today close only runs `git pull --ff-only` on the issue branch, which cannot pick up default-branch commits.
  - **Auto-resolve changelog-only conflicts**: when the conflict is confined to `HISTORY.md` / `CHANGELOG.md` (or `ISSUEFLOW_HISTORY_FILE`) and both sides only *add* bullets under `## [Unreleased]` (or the current release section), keep **all** bullets in a documented, fixed order (in-flight issue's bullet first or last — pick one and document it) and do not ask.
  - **Update the `/iflow-cycle` skill text**: sequential mode currently claims HISTORY stays single-writer; add that *external* merges to the default branch during one issue still collide, and that close's changelog resolver is the fix. Parallel mode's "coordinator owns HISTORY" path should use the same resolver so squash-merging worker PRs does not go DIRTY on `[Unreleased]`.
  - **Provide a shared resolver helper**: e.g. `issue-flow agent history-resolve`, or a documented recipe in `iflow-history-update`, so agents don't invent different keep-both orders.
- **Clarifications / constraints**:
  - This is **not only a parallel-dispatch problem**. Field report from a *sequential* `/iflow-cycle yolo` on `jepegit/cellpy` (queue `#961 → #962 → #963`): an unrelated PR (cellpy#954, squash of #952) landed on `master` during the ~8 min test/implement/test window of #961; PR cellpy#964 came back `mergeable: CONFLICTING`, `mergeStateStatus: DIRTY`, and the **only** conflict was `HISTORY.md` under `## [Unreleased]` (our #961 bullet vs the just-landed #952 bullet). Cycle step 6b treated the refused merge as a stop, `onfail:stop` halted the batch, and #962 / #963 were never reached.
  - **Stop only when the conflict is not changelog-shaped.** Any conflict outside the changelog — or a changelog hunk that isn't "two additive bullets" (edited existing bullet, heading rename, promoted version section) — must remain a step-6b stop / `onfail` trip.
  - **Never use `gh pr merge --admin` or skip CI** to paper over `DIRTY`. After a changelog rebase the PR needs a fresh check run; watch-then-merge / `--auto` is the correct behaviour.
  - Force-push only ever touches the **issue branch**, never the default branch (`--force-with-lease`).
  - Without the rebase-before-merge + changelog auto-resolve pair, `/iflow-cycle yolo` will keep dying on its first issue whenever anything else merges to the default branch during that issue's test/CI window.
  - Manual precedent from the reported run: rebase onto `origin/master`, keep both `[Unreleased]` bullets (ours first, then the already-landed one), `push --force-with-lease`; PR flipped to `MERGEABLE` with only pending required CI left. Full report: https://github.com/jepegit/issue-flow/issues/240#issuecomment-5412183611

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-08-25._
