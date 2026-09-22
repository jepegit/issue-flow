# Plan: #329 worktree_first knob

## Goal

Add a **`worktree_first`** knob (default **on**). When off, `/iflow-pick`,
`/iflow-issue`, and `/iflow-fix` start inplace on home (`git switch -c`)
instead of `worktree-add`. Per-run tokens still win.

## Constraints

- Distinct from **`auto_remove_worktree`** (close deletes the folder) and
  from **#328** (where the folder lives). This issue only chooses
  worktree vs home at **start**.
- Bake at `issue-flow update`. Agents do not runtime-parse `config.toml`.
- Default **true**: no config file still creates `../<repo>-<N>`.
- `issue-flow agent worktree-add` CLI stays as-is; skills decide whether
  to call it.
- Out of scope: cycle parallel worktrees, worktree location, novice seed
  change (leave `true` — novice is surface size, not start style).
- No new helper in `00-tools/`.

### Prior art

- `remind_cleanup` / `noob` / `auto_remove_worktree` — bool knobs:
  `DEFAULT_*`, `read_*`, `Settings.resolve_*`, `config_ops`, seed +
  template context (`skill-behaviour-knobs.md`).
- `templates/skills/_worktree_start.md.j2` — shared include used by pick /
  issue / fix. Gate the include here; command twins
  (`commands/iflow-pick.md.j2` etc.) still have a shorter prose copy.
- Tokens `inplace` / `no worktree` already documented in
  `docs/how-to/worktrees.md` (“There is **no** `config.toml` switch”).
- `tests/test_init.py` start-work assertions require `worktree-add` and
  `inplace` in rendered pick/issue/fix (default context stays true).
- `gitutils._worktree_start_point` — CLI start-point only; do not change
  for this knob.

## Approach

1. **Knob.** `[issueflow] worktree_first = true`. Env
   `ISSUEFLOW_WORKTREE_FIRST`. Wire `Settings.resolve_worktree_first`,
   `modes.read_worktree_first`, `config_ops`, default `config.toml`
   comment, `issue-flow config show|set|add`.
2. **Shared start include.** Rewrite `_worktree_start.md.j2`:
   - `worktree_first` true (today): worktree-add unless `inplace` /
     `no worktree` / ops stay-on-default.
   - `worktree_first` false: `git switch -c <N>-<slug>` on home unless
     token `worktree`.
   - Tokens always override. Worktree-add failure still **stop and ask**
     (never silent inplace).
3. **Command twins.** Same gate in `commands/iflow-{pick,issue,fix}.md.j2`
   so slash-command text matches the baked skill.
4. **Docs.** `docs/how-to/worktrees.md` (drop “no config.toml switch”;
   document knob + `worktree` token). `docs/configuration.md` table.
   `skill-behaviour-knobs.md` + `separate-workspaces.md` one-line.
   Workflow one-liner if it still says start is always a sibling worktree.
5. **This repo.** Leave `worktree_first` unset/true in issue-flow’s own
   `config.toml`.

## Files to touch

- `src/issue_flow/config.py`, `modes.py`, `config_ops.py`, `cli.py`,
  `agent.py` — resolve / persist / help.
- `src/issue_flow/templates/skills/_worktree_start.md.j2` — gated start.
- `src/issue_flow/templates/commands/iflow-pick.md.j2`,
  `iflow-issue.md.j2`, `iflow-fix.md.j2` — matching prose.
- `docs/how-to/worktrees.md`, `docs/configuration.md`,
  `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md`,
  `separate-workspaces.md`.
- `tests/test_config.py`, `test_modes.py`, `test_templating.py`,
  `test_init.py` — default true; false → inplace wording + `worktree`
  token; tokens still mentioned either way.

## Test strategy

`uv run pytest` and `uv run ruff check src/ tests/`. New tests: default
`resolve_worktree_first` is true; config/env flip; rendered pick skill
contains `worktree-add` iff `worktree_first` is true, and contains
`git switch -c` / token `worktree` when false; existing start-work
assertions keep passing on default context.

## Open questions

1. **Name `worktree_first`** (issue text) vs `auto_worktree`? Recommended:
   `worktree_first` — not an `auto_*` chain.
2. **Inverse token `worktree`** vs `use worktree` / `sibling`?
   Recommended: `worktree` as specified.
3. **Seed `worktree_first = false` on first-time `--mode novice`?**
   Recommended: **no** — keep default on.
