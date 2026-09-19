# Plan: #303 Default-branch diverge (ff-only + unpushed home commits)

## Goal

Starting work via a worktree must not require a fast-forward of home
default. When `git pull --ff-only` fails on default (pick / cleanup /
switchback), the agent classifies unique commits and names a safe
recovery — never rebase, force-push, or push default to skip CI.

## Constraints

- Templates under `src/issue_flow/templates/` are the source of truth.
- `issue-flow agent default-sync` is **classify-only** (no mutate), as
  the issue specifies.
- Never rebase default, `push --force` default, or treat “pull and push”
  as a substitute for ff-only.
- Out of scope: squash-merge policy, auto-push to default, HISTORY
  multi-PR conflicts (#260 / #288).
- Related but different: #255 (home stays on default), #243 (cleanup
  `-d` vs squash), #260 (changelog PR conflicts).

### Prior art

- `gitutils._worktree_start_point` / `add_worktree` already prefer
  `origin/<default>` (then local default, then `HEAD`). The cellpy
  incident already created the issue branch from `origin/master`. Pain
  is **home default hygiene**, not the issue-branch start point.
- `gitutils.ahead_behind`, `issueflows_only_dirty`, `fetch_prune`,
  `pull_ff_only` — reuse for classification; do not invent a second
  dirty-path helper.
- `agent switchback` already refuses a dirty tree and surfaces an
  ff-only refusal, but the note is only the raw git fatal.
- `agent preflight` reports ahead/behind but does not classify unique
  commit paths.
- `agent local-branches` is the bucket-pattern to mirror (read-only
  JSON, skills decide what to do).
- Skill dead-end: `_worktree_start.md.j2` and pick/cleanup/close still
  **require** `git pull --ff-only` on home before continuing.
- Epic `Published: #<M>` writes are not told where to commit
  (`iflow_epic` publish step 4). Doctor housekeeping already prefers a
  commit on the *current* branch (`dirty-issueflows.md`).
- Toolbox (`00-tools/`): nothing for default-sync. Graph: skipped
  (`graphify-out/graph.json` absent in this worktree); grep used
  instead.

## Approach

### 1. CLI: `issue-flow agent default-sync --json` (no mutate)

New read-only command. After `git fetch --prune` on the given `-C`
(home checkout):

- Compare `HEAD` to `origin/<default>` (`ahead_behind`).
- List `origin/<default>..HEAD`: short SHA, subject, `is_merge`, paths
  (`git log` + `git diff-tree --no-commit-id --name-only -r`).
- Classify the **tree** `origin/<default>…HEAD` (`git diff --name-only`):
  - **tracking** — every path is under `.issueflows/` (honour
    `ISSUEFLOW_DIR`).
  - **product** — any other path, including `HISTORY.md` / lockfiles /
    source.
  - **obsolete_merge** — tree is tracking-only **and** at least one
    unique commit is a merge (the “merge origin to keep the chore”
    stack). Prefer reset/replay over another merge.

Recommended `action` (skills print this; CLI never runs it):

| Situation | `action` |
| --- | --- |
| ahead 0, behind 0 | `even` |
| ahead 0, behind > 0 | `ff_only` (safe pull) |
| ahead > 0, behind 0, tracking | `report_ahead` (oneline + paths; do not silent-push) |
| diverge + tracking | `tracking_pr` — merge `origin/<default>` **or** cherry-pick onto a chore branch, then **open a tiny PR**. Never push default. |
| diverge + obsolete_merge | `replay_tracking` — replay the tracking commit onto `origin/<default>` (chore branch + PR). Do not stack another merge. |
| any product unique work | `stop_product` — user decides. Do not merge onto default. |

Always include `never`: no rebase of default, no force-push, no
CI-skipping push to default.

Wire it in `cli.py` `agent_app` help as read-only (same sentence as
`local-branches`).

### 2. `worktree-add` does not depend on home FF

- `run_worktree_add` / `add_worktree`: `fetch_prune` before resolving
  the start point so `origin/<default>` is current. Existing
  `_worktree_start_point` already picks the remote-tracking ref when
  present.
- Skills (`_worktree_start.md.j2`, pick / issue / fix commands):
  1. Home stays on default. `git fetch --prune`. No `git switch -c` on
     home.
  2. If `default-sync` says `even` or `ff_only`, pull `--ff-only`.
  3. If home is ahead or diverged, **print** `default-sync` and
     **still** `worktree-add`. Starting work must not wait for home to
     be ff-able.
  4. `inplace` / ops-stay-on-default unchanged.

### 3. Recover text on pick / cleanup / switchback / close

- **`switchback`:** on ff-only failure, attach `default-sync` fields
  (ahead/behind, commit onelines + paths, `action`) to `notes`. Keep
  exit 1. Do not merge/reset.
- **`/iflow-cleanup` A1:** if pull fails, print SHAs + the issue’s
  recovery table (from `default-sync.action`). Stop A1 steps that
  assume default is current (apply-changelog, release tag). Do not
  only dump `fatal: Not possible to fast-forward`.
- **`/iflow-close` step 9 / yolo post-merge pull:** same — report
  unique commits when home default is ahead; yolo must **not** recover
  by merging + pushing default.
- Close/switchback when ff **succeeds** but home is still ahead
  (ahead-only tracking): report onelines + paths (`report_ahead`).

### 4. Prevent unique commits on default (skill text only)

- **`/iflow-epic` publish:** after writing `Published: #<M>`, if the
  working tree is on default, commit on a chore/issue branch (or a
  tiny PR), never leave that line unpushed on home default.
- **`/iflow-doctor` / init scaffold:** same rule — housekeeping or
  scaffold commits do not sit unpushed on default.
- Do **not** relocate `apply-changelog` (writes `HISTORY.md` on default
  after merge). That is the #260/#288 class. `default-sync` will
  classify a leftover HISTORY commit as `product` if origin has also
  moved.

### 5. Design note

Add `.issueflows/04-designs-and-guides/default-branch-diverge.md`
(context, classify table, never-list, link to #303).

## Files to touch

- `src/issue_flow/gitutils.py` — fetch-before-start; classify helpers
  (unique commits, tree paths, class).
- `src/issue_flow/agent.py` — `run_default_sync`; switchback notes on
  ff refusal / ahead-only; `worktree-add` fetch.
- `src/issue_flow/cli.py` — `agent default-sync` + help text.
- `src/issue_flow/templates/skills/_worktree_start.md.j2`
- `src/issue_flow/templates/skills/iflow_{pick,issue,fix,cleanup,close,epic,doctor,init}/SKILL.md.j2` (and matching `commands/*.md.j2` / `_body.md.j2` / `docs/issue-workflow.md.j2` / `docs/how-to/worktrees.md` where they still require home FF).
- `tests/test_gitutils.py`, `tests/test_cli.py`, `tests/test_templating.py`
- `.issueflows/04-designs-and-guides/default-branch-diverge.md`

## Test strategy

`uv run pytest` (and `uv run ruff check src/ tests/`).

New / extended cases:

- `default-sync`: even; behind-only → `ff_only`; tracking diverge →
  `tracking_pr`; tracking + merge commit → `replay_tracking`; product
  path (e.g. `HISTORY.md` or `src/…`) → `stop_product`.
- `worktree-add` with local default **ahead** of a mocked
  `origin/<default>` still creates the branch at the **origin** tip
  (and home stays on default).
- `switchback` ff refusal includes classification fields, not only the
  git fatal.
- Templating: worktree-start no longer *requires* home FF; cleanup A1
  mentions `default-sync` / the recovery table; never-list present
  (no rebase / no force-push default).

Use real temp repos for classify / worktree-add (same style as
`test_agent_worktree_add_*`); monkeypatch is fine for switchback
wiring.

## Open questions

1. **`apply-changelog` on default** after cleanup/yolo is the same
   “unique commit on default” class once origin squash-moves. **Leave
   it in place** this issue (out of scope / #260). Confirm?
2. **Worktree start still FF when `ahead == 0`?** Recommended **yes**
   (keeps home tidy when it is safe). Diverge never blocks
   `worktree-add`.
3. **`HISTORY.md` as product** (issue table): a leftover changelog
   commit on default + origin moved → `stop_product`, not a tiny
   tracking PR. Confirm?
