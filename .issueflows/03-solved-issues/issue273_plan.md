# Issue #273 plan — worktree tweak

## Goal

Stop offering Cursor “open a new window” from the worktree-first start path.
After `/iflow-close` lands a PR (and, when `yolo`, after that PR merges), remove the sibling issue worktree without a trip through `/iflow-cleanup`. Gate that remove with `auto_remove_worktree` (default `true`).

## Constraints

- Templates under `src/issue_flow/templates/` are source of truth; rendered `.cursor/` copies are not edited by hand.
- `/iflow-close` still **never deletes branches**. Worktree remove ≠ branch delete. Cleanup keeps its existing `worktree-remove` before `-d`/`-D` for leftovers.
- `git worktree remove` must run from **home** (`-C <home>`). Existing `issue-flow agent worktree-remove` already refuses a dirty tree.
- Do not remove the worktree the agent is standing in while `stay` is in effect (cwd would vanish).
- Knob naming follows `[issueflow]` `auto_*` + underscore: `auto_remove_worktree` (issue’s `auto-remove-worktree`). Env: `ISSUEFLOW_AUTO_REMOVE_WORKTREE`. Bake at `init` / `update` like `auto_switchback`.
- CLI `--open` stays for manual use. Skills never ask and never pass it.

### Prior art

- `issue_flow.gitutils.remove_worktree` / `add_worktree` / `worktree_path_for_issue` — CLI already wraps add/list/remove.
- `issue_flow.agent` `open-workspace` + `--open` (issue #253); print-only default.
- Shared start include `src/issue_flow/templates/skills/_worktree_start.md.j2` (pick / issue / fix).
- Cycle + command stubs also mention confirm-then-`--open`.
- Knob wiring twin: `auto_switchback` — `DEFAULT_*` + `read_*` in `modes.py`, `resolve_*` + env in `config.py`, `ConfigKeySpec` in `config_ops.py`, `write_default_config` / novice seed, Jinja context, close/yolo templates.
- Cleanup already removes reachable worktrees before branch delete (`iflow_cleanup` skill).
- Design docs: `separate-workspaces.md`, `skill-behaviour-knobs.md`, `docs/how-to/worktrees.md`.
- Tests: `tests/test_init.py` (`--open` / `Never auto --open` assertions), `tests/test_cli.py` (open-workspace + worktree-remove).

## Approach

### Task 1 — drop the open-window option

Change the start contract from “create worktree + open window?” to **worktree only**.

1. `_worktree_start.md.j2`: after `worktree-add`, print the path (keep `open-workspace --json` print-only so the agent has a concrete folder). **Do not** fold an open-window question into the confirm. **Never** pass `--open`.
2. Same wording in pick / issue / fix / cycle **commands**, cycle skill parallel-dispatch, `issue-workflow.md.j2`, `docs/how-to/worktrees.md`.
3. Update `separate-workspaces.md`: skills never launch a window. CLI `--open` remains a manual escape hatch, not a skill step. Soften “prefer a separate window” so it is not a lifecycle prompt.
4. Flip scaffold tests: start skills must **not** mention `--open` / “open window”. Cycle test drops the `--open` assertion; print-only `open-workspace` may stay.

### Task 2 — remove worktree from close

New baked knob `auto_remove_worktree` default **`true`**.

**When it runs** (new close step after switchback, before the cleanup reminder):

- A linked worktree exists for the focus issue (`worktree-list` / `../<repo>-<N>`).
- Working tree in that worktree is clean (else report and leave it; no `--force`).
- Input did **not** include `stay`.
- Close actually finished the PR step: PR opened/updated, **or** `yolo` merge succeeded. Skip on `draft`, failed/queued-only `--auto` merge (folder still needed), ops-without-worktree, and inplace sessions (no folder).

**What it does:**

- Knob **on** (default): `issue-flow agent worktree-remove <N> -C <home> --json` with no prompt. Tell the user the path is gone; continue from **home**.
- Knob **off**: one YES/NO (“delete worktree folder `<path>`?”). Yes → same CLI. No → leave folder; cleanup still can take it later.
- Never `git branch -d` / `-D` here.

Wire the knob through the same stack as `auto_switchback` (modes / config / config_ops / Jinja / `config show` list / HISTORY later at close). Add a one-line row to `skill-behaviour-knobs.md`. Mention the new close step in `docs/how-to/worktrees.md` (“After the PR” no longer means “must run cleanup just to drop the folder”).

Cleanup’s worktree-remove stays as the safety net for leftovers and squash-landed branches.

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/templates/skills/_worktree_start.md.j2` | Drop open-window confirm; print path only |
| `src/issue_flow/templates/skills/iflow_cycle/SKILL.md.j2` | Drop `--open` ask |
| `src/issue_flow/templates/commands/iflow-{pick,issue,fix,cycle}.md.j2` | Same |
| `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2` | New post-switchback worktree-remove step, gated by knob |
| `src/issue_flow/templates/commands/iflow-close.md.j2` | Mirror the step |
| `src/issue_flow/templates/skills/iflow_yolo/SKILL.md.j2` + `commands/iflow-yolo.md.j2` | Note auto-remove after successful merge |
| `src/issue_flow/modes.py` | `DEFAULT_AUTO_REMOVE_WORKTREE = True`, read/write/novice (novice can stay `true` — no extra confirm when on) |
| `src/issue_flow/config.py` / `config_ops.py` | resolve + env + `ConfigKeySpec` |
| `src/issue_flow/cli.py` / `agent.py` | List the key in config help if those strings are enumerated |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | Worktree start no longer opens a window |
| `docs/how-to/worktrees.md` | Start + close-remove |
| `.issueflows/04-designs-and-guides/separate-workspaces.md` | Skills never `--open` |
| `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md` | New `auto_*` row |
| `tests/test_init.py` | Drop `--open` / “Never auto `--open`”; assert close skill has `worktree-remove` + knob name |
| `tests/test_config.py` (or sibling) | Default / env / persist for the new key — follow existing `auto_switchback` tests |

No new CLI command. Reuse `worktree-remove`.

## Test strategy

- `uv run pytest` (project default) plus `uv run ruff check src/ tests/`.
- Extend existing init-surface tests rather than a live `git worktree` integration unless one already exists (`test_cli.py` already covers `worktree-remove` dirty/by-number).
- `verify_scaffold.py` only if a rendered-marker check already looks for `--open` (update that marker if so).

## Open questions

1. **Non-yolo close (PR open, not merged): remove the folder too?** **Recommended: yes**, when the tree is clean and not `stay`. The stated pain is leftover `../<repo>-<N>` after close, not only after merge. Remote PR branch remains. Say **no** if you want the folder kept until merge for review checkouts.
2. **Delete CLI `--open` entirely?** **Recommended: keep.** Only the skill/command option goes away. Say **strip** if you never want the flag either.
