# Plan — Issue #308: publish on success

## Goal

The publish-on-success feature already merged in PR #378. This branch only
records it in `HISTORY.md` and closes GitHub issue #308. No new feature code.

## Constraints

- Do not reimplement `publish_label`, `publish-intent`, or the close/cleanup
  wiring. Those landed on `main` via #378.
- Changelog belongs to `/iflow-close` (`iflow-history-update`), in the PR
  commit. Do not bump the version: the code is already in the released tree;
  the missing line goes under `## [Unreleased]`.
- No `nohistory`. The whole point of this follow-up is the bullet the merge
  dropped.
- Ops stays no-PR / no-publish (already shipped; out of scope here).

### Prior art

- Shipped implementation: `src/issue_flow/publishintent.py`,
  `issue-flow agent publish-intent`, close/cleanup templates, design note
  `.issueflows/04-designs-and-guides/label-driven-flows.md` (“Publish on
  success”). Mirror / leave in place.
- Changelog writer: `.cursor/skills/iflow-history-update/SKILL.md` — append
  `- <summary>. (#N)` under `## [Unreleased]` when there is no bump. Default
  summary is the issue title (“publish on success”), which is too vague;
  close must use the bullet below (`log` / `note` override).
- Toolbox: none. Graph: not needed (no code change).

## Approach

1. **Build** — no product edits. Refresh `issue308_status.md`: #378 merged,
   Done still unchecked, remaining work is the changelog bullet plus close.
2. **Close** — no version bump. Append this bullet to `## [Unreleased]`:

   ```markdown
   - A `publish` label (`publish_label`, default `publish`; payloads `publish:<level>` or `publish:<version>`) bumps the version at close (default patch) and creates a GitHub release after merge. An illogical explicit version stops and asks. (#308)
   ```

   Then the usual close: tests, status `- [x] Done`, move the group to
   `03-solved-issues/`, commit, push, PR. Closing the GitHub issue is part
   of close.

## Files to touch

| Path | Change |
| --- | --- |
| `HISTORY.md` | One `[Unreleased]` bullet, written at close |
| `.issueflows/01-current-issues/issue308_status.md` | Note #378 merged; mark Done at close |

## Test strategy

No new tests. `/iflow-close` still runs `uv run pytest`.

## Open questions

None.
