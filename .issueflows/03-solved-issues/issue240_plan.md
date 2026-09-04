# Plan — Issue #240: Changelog conflicts

## Goal

Stop `/iflow-close` (and everything built on it — `/iflow-yolo`, `/iflow-cycle`,
`/iflow-auto`) from dying when the default branch moves under an in-flight issue
and the **only** conflict is additive changelog bullets. Close gains an explicit
"sync with the default branch" step backed by a deterministic CLI helper that
auto-resolves changelog-only additive conflicts and refuses everything else.

## Constraints

- **Templates are the source of truth.** All agent-facing behaviour changes go
  into `src/issue_flow/templates/` (skills *and* commands — they are kept in
  parity), never into the rendered `.cursor/` copies. Re-render this repo's own
  copies with `issue-flow update .` during build.
- **Conservative by default.** Anything not "two additive bullet sets under the
  same `## [Unreleased]` heading" stays a stop condition, exactly as
  `/iflow-cycle` step 6b treats it today.
- **Never paper over a red/blocked merge:** no `gh pr merge --admin`, no
  skipping CI. After a resolve the PR needs a fresh check run (watch-then-merge,
  `--auto` last resort) — unchanged from today's close step 8a.
- **Force-push only ever touches the issue branch** (`--force-with-lease`).
  The default branch is never rewritten, and the CLI helper itself never pushes.
- Changelog timing rules from
  [changelog-timing.md](../04-designs-and-guides/changelog-timing.md) stay
  intact: the bullet lands in the close commit, never after merge. This issue
  changes *conflict handling*, not *timing*.
- Python 3.13 / `uv`; `uv run pytest` + `uv run ruff check src/ tests/`.

### Prior art

- **`agent switchback`** (`src/issue_flow/agent.py` ~L417, `run_switchback` +
  `_render_switchback_text`) — the exact pattern to mirror for the new
  subcommand: JSON-or-text payload, `notes` list, exit 1 = "refuse, don't
  force". The new command is its sibling. **Mirror.**
- **`gitutils.py`** already has `git_available`, `current_branch`,
  `default_branch`, `dirty_paths`, `fetch_prune`, `switch_branch`,
  `pull_ff_only`, `ahead_behind`. Missing: rebase/merge/unmerged-path helpers.
  **Extend** in the same `_run`/`_stdout` style, no new subprocess idiom.
- **`iflow_history_update/SKILL.md.j2`** mode A already defines append
  semantics ("append the bullet to the end of the Unreleased bullet list").
  The keep-both ordering rule must match it rather than invent a new order.
  **Coexist** — the resolver is a new section in that same skill.
- **`tests/test_template_cli_consistency.py`** parses every template for
  `issue-flow agent <sub>` and asserts the Typer command exists — the new
  subcommand is auto-covered by it once referenced in a template.
- **`.issueflows/00-tools/`** — only `verify_scaffold.py`; nothing reusable here.
- **`parallel-cycle.md`** already says the coordinator (not workers) owns
  `HISTORY.md` in parallel mode. That design gets a pointer at the new resolver,
  no change of stance.
- **Graph:** `graphify query` returns only doc-level nodes for HISTORY/changelog
  (community 31 = `HISTORY.md` sections, 33 = README) — no code edges into
  close/agent, so nothing to reuse from the graph.
- **No new config knob planned** (see Open questions) — knob plumbing would
  touch `config.py`, `modes.py`/`modes.toml`, `docs/configuration.md`,
  `skill-behaviour-knobs.md`, and tests for behaviour that should always be on.

## Approach

### A. Pure resolver — `src/issue_flow/history.py` (new)

Text-in/text-out, no git, no I/O, fully unit-testable:

- `parse_conflicts(text)` → conflict blocks from `<<<<<<<` / `=======` /
  `>>>>>>>` markers (ours-side lines, theirs-side lines, span, preceding
  `## …` heading).
- `resolve_changelog_conflict(text, *, in_flight_side)` →
  `ResolveResult(text | None, reason)`.

Resolvable **only** when every conflict block satisfies all of:

1. the nearest preceding heading is `## [Unreleased]`;
2. both sides are non-empty and contain **only** bullet lines (`-` / `*`, plus
   indented continuation lines) and blank lines — any `#` heading, or any
   non-bullet content, refuses;
3. the union preserves every line from both sides (nothing dropped).

Refusal reasons are explicit strings (`not_unreleased_section`,
`non_bullet_content`, `heading_conflict`, `empty_side`) so the caller can report
*why* it stopped.

**Ordering (documented, deterministic):** already-landed bullets keep their
positions and the in-flight issue's bullet(s) are appended **last**, matching
`iflow-history-update` mode A's append semantics. Byte-identical duplicate
bullets collapse to one.

### B. CLI helper — `issue-flow agent sync-branch [--strategy rebase|merge] [--json]`

`agent.py: run_sync_branch` (mirrors `run_switchback`), registered on
`agent_app` in `cli.py`:

1. Refuse (exit 1) when git is missing, the tree is dirty (list paths), or the
   current branch **is** the default branch.
2. `git fetch --prune`; read `ahead_behind` vs `origin/<default>`. Not behind →
   `action: "none"`, exit 0 (no-op, cheap to call unconditionally).
3. Behind → `git rebase origin/<default>` (or `git merge` with
   `--strategy merge`).
4. On conflict, read unmerged paths (`git diff --name-only --diff-filter=U`).
   - Unmerged set == exactly the changelog file (`Settings.history_file`,
     i.e. `ISSUEFLOW_HISTORY_FILE`, default `HISTORY.md`) → run the resolver.
     Success → write, `git add`, `git -c core.editor=true rebase --continue`;
     loop for further conflicts under a small bounded retry.
   - Anything else, or a resolver refusal → `git rebase --abort` (or
     `merge --abort`), exit 1, report unmerged paths + refusal reason.
5. Exit 0 payload: `branch`, `default_branch`, `strategy`, `ahead`, `behind`,
   `action` (`none` / `fast-forward` / `rebased` / `merged`),
   `changelog_resolved`, `resolved_paths`, `needs_force_push`, `notes`.

The helper **never pushes** — pushing (`--force-with-lease`, issue branch only)
stays in the skill so it remains inside close's token / confirm surface.

New `gitutils` helpers: `rebase_onto`, `rebase_continue`, `rebase_abort`,
`merge_ref`, `merge_abort`, `unmerged_paths`, `stage_paths`.

### C. Skill + command wiring (templates)

- **`iflow_close`** step 6 becomes *"Sync with the default branch before push"*:
  CLI fast path (`issue-flow agent sync-branch --json`), manual fallback
  (`git fetch --prune` → rebase onto `origin/<default>` → keep-both changelog
  resolve → abort + stop on anything else), then push with `--force-with-lease`
  when the branch was rewritten.
- **`iflow_close` step 8a** gains a conflict retry: if `gh pr merge` is refused
  with `mergeable: CONFLICTING` / `mergeStateStatus: DIRTY`, re-run
  `sync-branch`; if it resolved, force-with-lease push, re-watch checks under
  the existing `checks_watch_minutes` budget, retry the merge **once**;
  otherwise stop hands-off with the PR left open. No `--admin`, no CI skip.
- **`iflow_history_update`** gains a *Conflict resolution (keep both)* section:
  the ordering rule, the three-part shape guard, the refuse cases, and a pointer
  at `agent sync-branch` so agents stop inventing their own keep-both order.
- **`iflow_cycle`** — step 6b reworded: a merge refusal is a stop **only after**
  the changelog resolver declines; the "All yolo issues + merge conflicts"
  section gains the external-merge case (the default branch moving during one
  issue's test/CI window is not covered by single-writer sequencing); the
  parallel coordinator's `HISTORY.md` append points at the same resolver.
- **`iflow_yolo`** + `commands/iflow-yolo.md.j2`, `commands/iflow-close.md.j2`,
  `docs/issue-workflow.md.j2` — mirror the close changes to keep parity.

### D. Docs + design record

- New `.issueflows/04-designs-and-guides/changelog-conflicts.md`: context (the
  cellpy field report), the decision, the ordering choice + why, refuse cases,
  alternatives considered (merge vs rebase, config knob), link to #240.
- Cross-links from `changelog-timing.md` and `parallel-cycle.md`.
- `docs/cli.md`: document `agent sync-branch` alongside `agent switchback`.
- Regenerate this repo's rendered copies (`issue-flow update .`) and add the
  `HISTORY.md` bullet at close.

## Files to touch

| Path | Change |
|---|---|
| `src/issue_flow/history.py` | **new** — conflict parsing + keep-both resolver, pure text |
| `src/issue_flow/gitutils.py` | add rebase/merge/unmerged-path/stage helpers |
| `src/issue_flow/agent.py` | **new** `run_sync_branch` + text renderer (mirrors `run_switchback`) |
| `src/issue_flow/cli.py` | register `agent sync-branch` (`--strategy`, `--json`) |
| `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2` | step 6 sync-with-default; step 8a conflict retry; constraints |
| `src/issue_flow/templates/commands/iflow-close.md.j2` | parity with the skill |
| `src/issue_flow/templates/skills/iflow_history_update/SKILL.md.j2` | keep-both conflict section + ordering rule |
| `src/issue_flow/templates/skills/iflow_cycle/SKILL.md.j2` | step 6b wording, conflict stance, parallel coordinator pointer |
| `src/issue_flow/templates/skills/iflow_yolo/SKILL.md.j2`, `templates/commands/iflow-yolo.md.j2` | mirror close's merge-retry wording |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | close step 5/6 description |
| `tests/test_history.py` | **new** — resolver unit tests (keep-both, order, dedupe, all refusals) |
| `tests/test_cli.py` (or new `tests/test_agent_sync_branch.py`) | `agent sync-branch` on temp git repos: no-op, resolved rebase, refuse on code conflict, refuse when dirty / on default branch |
| `.issueflows/04-designs-and-guides/changelog-conflicts.md` | **new** design record |
| `.issueflows/04-designs-and-guides/changelog-timing.md`, `parallel-cycle.md` | cross-links |
| `docs/cli.md` | document `agent sync-branch` |
| `HISTORY.md` | `[Unreleased]` bullet (at close) |
| `.cursor/**`, `docs/issue-workflow.md` | regenerated via `issue-flow update .` |

## Test strategy

- `uv run pytest` — full suite; `tests/test_template_cli_consistency.py` already
  pins the new `agent sync-branch` reference against the Typer app.
- `uv run ruff check src/ tests/`.
- **Resolver units** (no git): keep-both ordering, duplicate collapse, multiple
  conflict blocks, and each refusal path (heading conflict, non-bullet content,
  conflict outside `[Unreleased]`, empty side).
- **Integration on temp git repos** reproducing the reported scenario: branch
  off `main`, land an unrelated `[Unreleased]` bullet on `main`, add our bullet
  on the branch, run `agent sync-branch` → rebased, both bullets present, ours
  last, exit 0. Same setup with a conflicting **code** hunk → exit 1, rebase
  aborted, tree clean at the original commit.
- Manual smoke: scaffold a throwaway project
  (`uv run --project . issue-flow init . --skip-dep-check`) and confirm the
  rendered close/cycle skills carry the new steps.

## Open questions

1. **Rebase or merge as the default sync strategy?** *Recommend rebase*
   (matches the issue's ask and the manual precedent, keeps history linear,
   squash-merge makes branch shape irrelevant on `main`), with
   `--strategy merge` available. Cost: rewrites the PR head, so close must
   `push --force-with-lease`. Merge would avoid force-push entirely at the price
   of a merge commit on the issue branch.
2. **Keep-both ordering.** *Recommend appending the in-flight bullet last*
   (consistent with `iflow-history-update` mode A). Note this is the **opposite**
   of the manual resolve in the field report, which put ours first — the issue
   says "pick one and document it", so this is a deliberate deviation.
3. **Config knob?** *Recommend none in v1*: always auto-resolve, guarded by the
   shape check. A `changelog_autoresolve` knob costs six plumbing touchpoints
   for behaviour whose "off" state is a known-bad stop.
4. **One command or two?** *Recommend one* (`agent sync-branch`), with the pure
   resolver importable from `history.py`. The comment floated a separate
   `agent history-resolve`; it has no second caller today (the parallel
   coordinator *appends* bullets rather than resolving markers), so adding it
   now would be speculative surface.
5. **Scope.** This is one cohesive PR (~1 new module + 1 subcommand + template
   wiring + tests). It could split into "resolver + CLI" and "skill wiring", but
   each half is inert alone. *Recommend keeping it single.*
