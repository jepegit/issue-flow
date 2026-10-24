# Plan: issue #404 — changelog trailers, release-time HISTORY

## Goal

Feature closes stop editing `HISTORY.md`. The bullet lives in commit-message trailers. `HISTORY.md` gains a version section only when `issue-flow changelog release` runs on the default branch, so parallel PRs no longer conflict on `## [Unreleased]`.

## Constraints

- One PR, per the pick confirm. Repair paths stay: `sync-branch` keep-both and `/iflow-pr-sync` (#240, #260). This issue removes the shared heading; it does not delete the resolver.
- Do not change squash-merge policy, auto-merge, or non-`HISTORY.md` conflict handling. No cellpy reader.
- `nohistory` still means no bullet.
- `confirm_changelog_update` still gates the bullet text. It does not choose the file.
- Close may still bump `pyproject.toml`. It must not promote `HISTORY.md`.
- `changelog add` (a trailer with no close) is out of scope. Hand-typed bullets in `HISTORY.md` stay invisible to `changelog list`, as the issue says.
- Id is 12 lowercase hex from `secrets.token_hex(6)`. No new dependency. ULID was the other option in the issue.
- This PR must not diff `HISTORY.md`. The empty `## [Unreleased]` in this repo is folded by the first later `changelog release`, not by this change.

### Prior art

- `append_unreleased_bullet`, `promote_unreleased`, `parse_deferred_changelog`, `resolve_changelog_conflict` in `src/issue_flow/history.py` — coexist. New list/release helpers sit beside them. Do not remove the resolver.
- `issue-flow agent apply-changelog` (`src/issue_flow/agent.py`) — coexist as a manual reader of an existing `### Deferred changelog` block. Templates stop calling it.
- `defer_changelog` (#288, `changelog-timing.md`) — superseded for writes. See Open questions.
- `iflow-history-update` — migrate: compose the bullet and the three trailers; do not write the changelog file.
- `sync-branch` keep-both — keep, for repos that still have `[Unreleased]` and for design-guide / status-file conflicts.
- Graph: `graphify-out/graph.json` is absent. `GRAPH_REPORT.md` communities around `history.py`, apply-changelog tests, and the history-update skill match the grep hits above.
- Toolbox (`.issueflows/00-tools/README.md`): none of these helpers parse trailers or rewrite `HISTORY.md`.

## Approach

### Trailers

Close generates one block per bullet, in the commit message body (a file via `git commit -F`, not a heredoc):

```text
Changelog: <bullet> (#N)
Changelog-Date: YYYY-MM-DD
Changelog-Id: <12 hex>
```

The bullet keeps today's shape (`- <summary>. (#N)` stored as the `Changelog` value without the leading `- `). A person does not invent the id. `nohistory` emits no block.

Parse the **full** commit message, not only the final `git interpret-trailers` block. A squash body contains several trailer blocks. Group by `Changelog-Id`. Last occurrence in one message wins. Across commits, the later commit wins. A new id is a new bullet.

### List

`issue-flow changelog list` prints bullets and writes nothing.

Scan window: commits after the commit that introduced the current top `## [version] - date` heading (`git log -S` on that heading line, first parent walk). Exclude any `Changelog-Id` named in a `<!-- changelog-ids: ... -->` comment anywhere in `HISTORY.md`. Sort surviving notes by `Changelog-Date`, then commit order. Same id: newest text, and that commit's date.

If `## [Unreleased]` is still present, list does not print those old bullets (they are folded at release). Missing changelog file: print nothing, exit 0.

### Release

`issue-flow changelog release <version>` on the **default branch** only:

1. Refuse if the tree is dirty (`git status --porcelain`), the branch is not the default, `HEAD` changes between the read and the write, the version heading already exists, or the combined list is empty.
2. Build the new section from `changelog list` plus, on the first adoption release only, the existing `## [Unreleased]` bullets (in their current order, above trailer bullets). Then delete that heading. Do not recreate it.
3. Prepend `## [<version>] - <YYYY-MM-DD>` and an HTML comment of the shipped ids. Do not rewrite older sections. Do not commit, tag, bump `pyproject.toml`, or push.
4. The follow-up commit on the default branch should be only that file and should include `Changelog-Release: <version>` so CI can tell a release from a feature edit.

Empty `[Unreleased]` and no trailers is an empty list: refuse, leave the heading in place.

### Close, cleanup, cycle

Templates (`iflow-close`, `iflow-history-update`, `iflow-cleanup`, `iflow-yolo`, `iflow-cycle`, the close command, the managed rules body) tell the agent to put the trailer block in the close commit and to leave `HISTORY.md` unstaged. Version bump does not promote a heading. Cleanup and yolo post-pull do not run `apply-changelog`. Cycle workers do not append changelog bullets; the trailers ride the squash commit. Keep-both sync text stays for leftover `[Unreleased]` repos and for design docs.

### CI

`issue-flow changelog check` (used from `.github/workflows/ci.yml` on pull requests) exits 1 when `HISTORY.md` differs from the base and the commits that touch it lack `Changelog-Release:`. A release commit is the exception the issue allows. Push-to-default is not failed by this check.

## Files to touch

- `src/issue_flow/history.py` — pure parse, group, render, fold-`[Unreleased]`, refuse reasons. No git.
- `src/issue_flow/changelog.py` — new. Scan window, dirty / branch / `HEAD` checks, write `HISTORY.md`.
- `src/issue_flow/cli.py` — `changelog` Typer group: `list`, `release`, `check`.
- `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2`
- `src/issue_flow/templates/skills/iflow_history_update/SKILL.md.j2`
- `src/issue_flow/templates/skills/iflow_cleanup/SKILL.md.j2`
- `src/issue_flow/templates/skills/iflow_yolo/SKILL.md.j2`
- `src/issue_flow/templates/skills/iflow_cycle/SKILL.md.j2`
- `src/issue_flow/templates/commands/iflow-close.md.j2`
- `src/issue_flow/templates/rules/_body.md.j2`
- `tests/test_history.py` or `tests/test_changelog.py` — replace/collapse, fold, refuse reasons.
- `tests/test_changelog_cli.py` — temp git repo: scan window, dirty tree, non-default branch, empty list, no write on `list`.
- `tests/test_templating.py` — rendered close skill talks about trailers, not appending `[Unreleased]`.
- `.github/workflows/ci.yml` — run `changelog check` on pull requests.
- `docs/cli.md`, `docs/developing.md`, `docs/configuration.md`, `docs/concepts.md`, `docs/getting-started.md`, `docs/how-to/troubleshooting.md`, `docs/how-to/pr-sync.md`, `docs/how-to/sample-session.md`
- `.issueflows/04-designs-and-guides/changelog-timing.md` and `changelog-conflicts.md` — record the decision and the migration note for a repo that still has `[Unreleased]`.

## Test strategy

`uv run pytest` and `uv run ruff check src/ tests/`. New tests cover the acceptance list: list does not write, release prepends one section and records ids, id replace/collapse, refuse cases, rendered close instructions do not stage `HISTORY.md`. Do not run `changelog release` against this repo's real `HISTORY.md` in tests; use temp repos.

## Open questions

Accept means the recommended answer.

1. **`defer_changelog`.** Recommended: templates always use trailers, even when the knob is true. `apply-changelog` stays for a status file that already has `### Deferred changelog`, but cleanup/yolo stop calling it. The key stays in config so existing files still parse. Alternative: keep the knob as a second write path (status block + apply on default).
2. **`changelog release` scope.** Recommended: it only rewrites `HISTORY.md`. It does not bump `pyproject.toml`, create a tag, or run `gh release create`. Close and `docs/developing.md` keep the version bump. Tag-strategy projects stop promoting `HISTORY.md` inside the feature PR; the dated section appears when release runs on the default branch.
