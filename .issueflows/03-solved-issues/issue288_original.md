# Issue #288: Prevent HISTORY conflicts: defer_changelog (write on default after merge)

Source: https://github.com/jepegit/issue-flow/issues/288

## Original issue text

## Problem / context

`/iflow-close` writes every changelog bullet into the same few lines under `## [Unreleased]` on `HISTORY.md` / `CHANGELOG.md`. Two PRs forked from the same default both insert there, so the second goes `DIRTY` / `CONFLICTING` after the first squash-lands — even when CI was green. Version promotion (rewriting `[Unreleased]` → `[0.x.y]`) is worse: keep-both cannot resolve heading conflicts (dual `0.4.13` on #255 vs #259).

Repair is already shipped:

- #240 — `issue-flow agent sync-branch` keep-both for additive `[Unreleased]` bullets on the *current* close branch
- #260 Part A — `/iflow-pr-sync` refreshes sibling dirty heads

Those rebase + re-run CI. They do not stop the collision. #260 Part B (`defer_changelog`) was deferred; this issue is that follow-up.

Layout changes (Unreleased at the bottom, a second shared `unreleased.md`) do **not** fix this. Git conflicts on the same insertion point, not on top-vs-bottom. A single sidecar file is the same single-writer problem, moved.

## Spec

Optional `[issueflow].defer_changelog` (default `false` so existing projects keep today's "bullet in the PR commit" behaviour from #171).

When `true`:

1. **Issue branches never edit** `HISTORY.md` / `CHANGELOG.md`.
2. `/iflow-close` records the bullet in `issue<N>_status.md` and the PR body (and still honours `nohistory` / `confirm_changelog_update` for *whether* a bullet exists).
3. After merge, `/iflow-cleanup` and yolo post-pull append that bullet on the default branch (newest last — same order as `history.py` / mode A). Version promote, if any, happens in that same default-branch write — one writer, no dual `0.x.y` headings.
4. Parallel-cycle workers already leave bullets in status and let the coordinator append; this knob makes that the default for serial close too.
5. Bake the key at `issue-flow update`; document it in `skill-behaviour-knobs.md`, `changelog-timing.md`, and `pr-queue-sync.md`. `confirm_changelog_update` still gates the *text* of the bullet; it does not write HISTORY on the issue branch when defer is on.

## Acceptance criteria

- [ ] `[issueflow].defer_changelog` exists (default `false`), typed in config, shown by `issue-flow config show`, baked into close / cleanup / yolo / cycle templates on `update`.
- [ ] With the knob on, close + tests never produce a HISTORY/CHANGELOG hunk on the issue branch; the bullet is in status and the PR body.
- [ ] After merge, cleanup / yolo post-pull appends the deferred bullet on default (and promotes `[Unreleased]` when a bump was planned). Idempotent if the bullet is already present.
- [ ] Two concurrent PRs with defer on do not go `DIRTY` because of HISTORY; version promote is not attempted on either issue branch.
- [ ] Knob off = today's behaviour (bullet in the PR commit, #240 / #260 repair still apply).
- [ ] Design docs record prevent vs repair: this issue implements prevent; fragments / towncrier stay out of scope.

## Out of scope

- Moving `[Unreleased]` to the bottom of HISTORY, or adding a shared sidecar unreleased file.
- Towncrier/scriv-style `changelog.d/<n>.md` fragments (possible later upgrade if we want a *file* in every PR *and* zero HISTORY edits).
- Git `merge=union` driver (GitHub squash ignores it; unsafe on promote).
- Changing squash-merge policy, or auto-merging the PR queue.
- Replacing #240 / #260 repair — those stay the default-off path.

## Links

#260 (Part B), #240, #171. Design: `pr-queue-sync.md`, `changelog-conflicts.md`, `changelog-timing.md`, `parallel-cycle.md`.
