# Status for issue #63: Pick next issue

- [x] Done

(Phase A complete. Phase B — automated sub-issue breakdown — intentionally deferred to a
separate follow-up issue, per the confirmed plan.)

## Done so far

Shipped the new **`/issue-pick`** front-door slash command (Phase A) plus its mirror Agent Skill,
and wired it through the whole scaffold:

- **New command template** `src/issue_flow/templates/commands/issue-pick.md.j2` — three phases:
  1. **Choose** — parked work in `02-partly-solved-issues/` first, else open GitHub issues
     (`gh issue list`) ranked by milestone + labels + topical similarity to recently solved issues,
     presented as a confirmable shortlist; `fix` shortcut creates a **new** `chore: general fixes`
     issue every time.
  2. **Branch** — clean-tree gate, branch off the default with `git switch -c <N>-<slug>`, then
     delegate to the `/issue-init` flow.
  3. **Hand off** — ask whether to continue with `/issue-plan` (never auto-run).
- **New skill template** `src/issue_flow/templates/skills/issueflow_issue_pick/SKILL.md.j2` —
  mirrors the command, frontmatter `name: issueflow-issue-pick` + `disable-model-invocation: true`.
- **Manifest** `src/issue_flow/templating.py` — registered both new templates
  (24th/25th entries; output dirs use hyphenated skill name).
- **Off-path wiring** — added `/issue-pick` to the "never auto-dispatched" lists in
  `commands/iflow.md.j2` and `skills/issueflow_iflow/SKILL.md.j2`.
- **Docs** `templates/docs/cursor-issue-workflow.md.j2` — bumped "nine → ten" commands, added the
  command + skill table rows, a dedicated `## 0a. /issue-pick` section, and updated the end-to-end
  flow diagram.
- **Rules** `templates/rules/issueflow-rules.mdc.j2` — front-door paragraph in the lifecycle section.
- **README.md** — command tree, skill tree, off-path list, and the Agent Skills sentence.
- **Tests** — `tests/test_templating.py` (manifest count 23 → 25, added `issue-pick`/
  `issueflow_issue_pick` to the expected lists, three new focused tests) and `tests/test_init.py`
  (new scaffolding assertion).
- Regenerated the local `.cursor/` scaffold via `uv run issue-flow update .` so this repo dogfoods
  the new command.

## Verification

- `uv run pytest -q` → **110 passed**.
- `uv run ruff check src/ tests/` → **All checks passed**.

## Remaining work

- None for this issue. **Phase B** (automated sub-issue suggestion + GitHub creation + parking
  siblings under `02-partly-solved-issues/`) is tracked as a separate follow-up issue.

## Next step

Run `/issue-close` (optionally with `bump`/`patch`/`minor`/`major`) to land the work, and open the
Phase B follow-up issue.
