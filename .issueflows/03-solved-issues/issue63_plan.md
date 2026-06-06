# Plan for issue #63: Pick next issue

## Goal

Add a new `/issue-pick` slash command (plus its mirror Agent Skill) that helps the user
**choose** the next issue to work on, create the right branch, and hand off into the
existing linear lifecycle. It is the missing "front door" that runs *before* `/issue-init`.

## Confirmed decisions (from user, 2026-06-06)

1. **Name:** `/issue-pick`.
2. **Scope:** **split** — this PR ships **Phase A** only (pick → clean-tree → branch →
   auto-`/issue-init` → handoff, incl. the `fix` shortcut). The automated sub-issue
   breakdown + GitHub sub-issue creation + parking siblings becomes a **follow-up issue
   (Phase B)** — `/issue-pick` will *mention* the option but not implement it yet.
3. **Relevance ranking:** milestone **and** labels **and** topical similarity to recently
   solved issues (`03-solved-issues/`) / recent branches.
4. **`fix` shortcut:** **create a new** "general fixes" GitHub issue each time (no reuse of
   an existing open one).

## Constraints

- Commands/skills/docs in this repo are **Jinja2 templates** under `src/issue_flow/templates/`,
  rendered into `.cursor/` + `docs/` by `issue-flow init`/`update`. Every new command must be added
  to `TEMPLATE_MANIFEST` in [`src/issue_flow/templating.py`](src/issue_flow/templating.py) or it
  ships to nobody.
- Each slash command has a paired skill template (`skills/issueflow_<name>/SKILL.md.j2`) with
  frontmatter `name:` + `disable-model-invocation: true`. Mirror that convention.
- The hard manifest-count test (`test_manifest_entry_count`, currently `== 23`) and
  `test_manifest_has_expected_commands_and_skills` must be updated, or they fail.
- Templates use `{{ issueflows_dir }}`, `{{ current_issues_folder }}`, `{{ partly_solved_folder }}`,
  `{{ agent_dir }}` etc. — never hard-code `.issueflows`/`.cursor` in template bodies.
- Follow existing safety norms: never force-push, never `-D` branches, branch off the detected
  default (`main`/`master`), one consolidated confirm for multi-step git actions.
- Respect Cursor command/skill style: numbered Steps, Input, Output, Constraints sections; reuse the
  branch-preflight pattern from `issue-init`/`issue-plan`.
- `gh` is the GitHub interface already assumed by `issue-init`/`issue-close`; reuse it
  (`gh issue list`, `gh issue view`, `gh issue create`).

### Prior art

- `issue-init.md.j2` (`templates/commands/`) — convention: resolves `owner/repo` from `git remote`,
  uses `gh issue view ... --json`, branch-status preflight, archive sweep of `01-current-issues`.
  New work: **reuse/delegate** — Phase 2 of `/issue-pick` explicitly *runs the `/issue-init` flow*
  for the chosen number rather than re-implementing it.
- `issue-yolo.md.j2` + `skills/issueflow_issue_yolo` — convention: a **chaining** command with
  up-front preflight (clean tree, default-branch refusal) and a single consolidated confirm, then
  it follows the other commands' playbooks. New work: **mirror** this structure closely — `/issue-pick`
  is also a chaining/front-door command (pick → branch → init → handoff).
- `iflow.md.j2` — convention: an off-path-aware dispatcher that documents which commands are NOT
  auto-dispatched. New work: **coexist** — add `/issue-pick` to the "off-path / explicit only" lists
  (it is interactive and creates GitHub issues, so `/iflow` must not auto-run it).
- `templating.TEMPLATE_MANIFEST` — convention: `(template, "{agent_dir}/.../out")` tuples; skill
  output dirs use **hyphenated** names (`issueflow-issue-pick`) while template source dirs use
  **underscores** (`issueflow_issue_pick`). New work: mirror exactly.
- Docs/rules listing every command (`docs/cursor-issue-workflow.md.j2`, `rules/issueflow-rules.mdc.j2`)
  — convention: a command table + per-command section + lifecycle prose. New work: extend (migrate the
  "nine slash commands" wording to ten).

## Approach

Add one new command template + one new skill template, register them, and thread references through
the docs/rules/iflow so the new command is discoverable and correctly marked off-path. Suggested
command name: **`/issue-pick`** (alternative: `/issue-next`; see Open questions).

The command body documents three phases (straight from the issue):

**Phase 1 — choose the issue.**
1. Preflight: detect default branch, `git fetch --prune`, report current branch / clean-or-dirty.
2. **Source selection (precedence):**
   - If `{{ partly_solved_folder }}/` contains `issue<n>_*` groups → list them as the primary
     candidates (these are already-started work) and ask which to resume.
   - Else pull candidates from GitHub via `gh issue list` (open, not yet captured locally), ranked by
     **relevance**: same milestone as recent work, and/or topical similarity to the most recently
     closed/worked issues (infer from `03-solved-issues/` + recent branches). Present a short ranked
     shortlist with numbers/titles/labels/milestone.
   - Always **ask the user to confirm** the selected issue; allow free-form override.
3. **`fix` shortcut:** if the user types `fix`, create **a new** "general fixes" GitHub issue via
   `gh issue create` (small bug/typo bucket) every time, and use it as the chosen issue.
4. **Over-large issue (Phase B, deferred):** if the chosen issue looks too involved, the command
   *notes* that it could be broken into sub-issues and points the user at the Phase B follow-up. The
   automated `gh issue create` breakdown + parking siblings under `{{ partly_solved_folder }}/` is
   **out of scope for this PR**.

**Phase 2 — create the branch.**
1. Refuse / require a clean tree (`git status --porcelain`); guide the user to commit/stash if dirty.
2. Branch off the detected default using GitHub's numeric convention `git switch -c <N>-<short-slug>`.
3. Auto-run the `/issue-init` flow for the now-known issue number (delegate to the issue-init
   playbook; do not duplicate its logic).

**Phase 3 — handoff.**
1. Land the user in the standard flow and **ask** whether to continue with `/issue-plan` next
   (don't auto-run it).

The skill mirrors the command (same phases, condensed), with frontmatter
`name: issueflow-issue-pick` + `disable-model-invocation: true`.

## Files to touch

- `src/issue_flow/templates/commands/issue-pick.md.j2` — **new** command body (3 phases above).
- `src/issue_flow/templates/skills/issueflow_issue_pick/SKILL.md.j2` — **new** mirror skill.
- `src/issue_flow/templating.py` — add the command + skill entries to `TEMPLATE_MANIFEST`.
- `src/issue_flow/templates/docs/cursor-issue-workflow.md.j2` — add `/issue-pick` to the command table,
  the skills table, a dedicated section, and the end-to-end flow notes; bump "nine slash commands" → ten.
- `src/issue_flow/templates/rules/issueflow-rules.mdc.j2` — mention `/issue-pick` in the lifecycle prose
  (front-door before `/issue-init`).
- `src/issue_flow/templates/commands/iflow.md.j2` + `skills/issueflow_iflow/SKILL.md.j2` — add
  `/issue-pick` to the "not auto-dispatched / explicit only" lists.
- `tests/test_templating.py` — bump `test_manifest_entry_count` (23 → 25) and extend
  `test_manifest_has_expected_commands_and_skills`; add a focused test that the new command documents
  its three phases and the `fix` shortcut.
- `tests/test_init.py` — (optional) assert the `/issue-pick` command + skill are scaffolded by `run_init`.
- `README.md` — (optional) if it enumerates commands, add `/issue-pick`.
- Regenerate local `.cursor/` copies (run `issue-flow update`/`init`) so this repo dogfoods the command.

## Test strategy

- `uv run pytest` — full suite; specifically the templating + init tests touched above.
- After editing the manifest, confirm `test_all_templates_render_without_error` still passes (new
  templates render with the default context, no leftover `{{ ... }}`).
- Manual: run `issue-flow update .` (or `init`) in a scratch dir and eyeball
  `.cursor/commands/issue-pick.md` + `.cursor/skills/issueflow-issue-pick/SKILL.md`.

## Open questions

_All resolved — see **Confirmed decisions** above._ `/issue-pick` stays strictly off-path
(never auto-dispatched by `/iflow`), matching `/issue-yolo`.

## Follow-up (Phase B)

After this PR lands, open a follow-up issue: "automated sub-issue breakdown in `/issue-pick`" —
propose sub-issues for over-large issues, create them on GitHub (cross-linking the parent), start the
first, and park siblings under `{{ partly_solved_folder }}/` as lightweight stubs.
