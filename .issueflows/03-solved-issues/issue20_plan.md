# Plan for issue #20: status of issues

## Goal

Add a new **read-only, off-path** slash command (plus its paired Agent Skill)
that prints a consolidated **status overview of the repository's issues** — both
the local `.issueflows/` tracking state (focus / parked / solved) and open GitHub
issues — without modifying anything. It answers "where do all my issues stand?"
at a glance, complementing `/iflow` (which acts on the single focus issue).

## Constraints

- **Read-only.** The command/skill writes nothing and moves no files. It only
  reads `.issueflows/` and runs read-only `git` / `gh` queries.
- **Off-path.** Like `/issue-pick`, `/graphify`, `/issue-fix`, it must never be
  auto-dispatched by `/iflow`, `/issue-start`, or `/issue-close`. The user opts in.
- **`gh`-optional, degrade gracefully.** If `gh` is missing/unauthenticated,
  still produce the local-only report and note that GitHub data was skipped.
- **Editor-neutral templates.** Per `04-designs-and-guides/editor-profiles.md`,
  templates must use `{{ ... }}` context vars (folder names, `{{ agent_dir }}`,
  `{{ editor_name }}`) and contain **no literal "Cursor"** — `test_build_manifest_no_cursor_leakage_in_non_cursor_outputs` enforces this. The command is emitted only for profiles with a `commands_dir` (Codex gets the skill only); this is automatic via `build_manifest`.
- Follow the project `uv` toolchain for running tests (`uv run pytest`).

### Prior art

- `iflow` command + `issueflow_iflow` skill (`src/issue_flow/templates/...`) — convention: lifecycle **state detection** from file presence (states A–D: `_original.md` → `_plan.md` → status without `- [x] Done` → `- [x] Done`) and branch-derived focus `N` via `^(\d+)-.+`. New work: **mirror** this stage-detection logic to label the focus issue's lifecycle stage.
- `issue-pick` command (`templates/commands/issue-pick.md.j2`) — convention: sources candidates from parked work under `{{ partly_solved_folder }}/` **and** `gh issue list --state open --json number,title,labels,milestone,updatedAt`, cross-referencing local folders to drop already-captured issues. New work: **mirror** the sourcing/cross-reference logic, but read-only (report instead of rank/branch).
- `graphify` command + `issueflow_graphify` skill — convention: a **non-`issue-` off-path** command with a distinctly-named paired skill (`/graphify` ↔ `issueflow-graphify`). New work: mirror the off-path + paired-skill registration pattern.
- `COMMAND_NAMES` / `SKILL_DIRS` lists in `src/issue_flow/templating.py` — convention: a command + paired skill is registered by appending a stem to each list; `build_manifest` derives output paths. New work: **mirror** by appending the new stems.

## Approach

Add one new slash-command template and one new paired skill template, register
both in `templating.py`, and update the tests/docs that enumerate commands.

**Naming (CONFIRMED):** command **`issue-status`** (invoked `/issue-status`)
paired with skill **`issueflow_issue_status`** (invoked `/issueflow-issue-status`).
This keeps the established pattern where each `issue-*` command has a distinct
`issueflow-issue-*` skill, and avoids a command/skill name collision. (The issue
text said `/issueflow-status`, but we use the consistent name.)

**What the report contains** (concise, sectioned, read-only):

1. **Context / preflight** — current branch, detected default branch, clean/dirty
   tree, ahead/behind vs `origin/<default>`; focus `N` derived from the branch.
2. **Focus issue** (`{{ current_issues_folder }}/`) — the active group, its title
   from `_original.md`, and its lifecycle stage using the `/iflow` A–D logic
   (init / plan / start / close), plus the next-step hint.
3. **Parked work** (`{{ partly_solved_folder }}/`) — list each `issue<n>_*` group:
   number, title, one-line status if a status file exists.
4. **Solved archive** (`{{ solved_folder }}/`) — count, with the most recent few.
5. **Open GitHub issues** — `gh issue list` cross-referenced against local folders,
   tagging each as in-progress / parked / solved-locally / not-yet-started.
   Skipped gracefully if `gh` is unavailable.
6. **Summary line** — e.g. "1 focus, 2 parked, N solved, M open on GitHub".

## Files to touch

- `src/issue_flow/templates/commands/issue-status.md.j2` — **new** command template
  (mirror the structure/tone of `iflow.md.j2` and `issue-pick.md.j2`: Input,
  Steps, Constraints, Output, Example invocations). Editor-neutral.
- `src/issue_flow/templates/skills/issueflow_issue_status/SKILL.md.j2` — **new**
  paired skill (frontmatter `name: issueflow-issue-status`, `description`, likely
  `disable-model-invocation: true` as in `issueflow_iflow`), pointing at
  `{{ agent_dir }}/commands/issue-status.md`.
- `src/issue_flow/templating.py` — append `"issue-status"` to `COMMAND_NAMES` and
  `"issueflow_issue_status"` to `SKILL_DIRS`.
- `tests/test_templating.py` — bump counts and lists:
  - `test_manifest_entry_count` / `test_build_manifest_cursor_matches_default`: 27 → **29** (12 commands + 1 rule + 1 doc + 15 skills); update the explanatory comment.
  - `test_build_manifest_codex_*`: skills 14 → **15**, `len(manifest)` 15 → **16**.
  - `test_manifest_has_expected_commands_and_skills`: add `"issue-status"` and `"issueflow_issue_status"`.
- `tests/test_init.py` — if any expected skill/command enumeration or count is
  affected, extend it (and consider a small `test_init_creates_status_command_and_skill` mirroring the graphify test).
- `README.md` — add the command to the scaffold tree listing and the skill to the
  Agent Skills sentence.
- `src/issue_flow/templates/docs/issue-workflow.md.j2` — mention the new off-path
  command in the command overview (source of truth; rendered `docs/*.md` are
  regenerated by `issue-flow update`, not hand-edited here).
- `src/issue_flow/templates/rules/_body.md.j2` — **(CONFIRMED)** add a brief
  line under the command lifecycle noting the off-path `/issue-status` command.
  This feeds `AGENTS.md` / `.mdc` / `CLAUDE.md`.

> Note: this issue does not require a new design-and-guides doc; the editor-profiles
> guide already covers the multi-editor mechanics. `HISTORY.md` is updated at
> `/issue-close`, not here.

## Test strategy

- `uv run pytest` — full suite; focus on `tests/test_templating.py` and
  `tests/test_init.py` after the count/list bumps.
- `uv run ruff check src/ tests/` — lint.
- Render check: confirm the new command + skill templates render with the default
  cursor context and the non-cursor leakage test still passes (no literal "Cursor").
- Manual: scaffold into a temp dir (or inspect rendered output) and eyeball the
  status report wording.

## Open questions (resolved)

1. **Command/skill name** — RESOLVED: use `/issue-status` (command) + `issueflow-issue-status` (skill) for consistency.
2. **Scope of the report** — RESOLVED: the 6-section design above is approved as-is.
3. **Rules/AGENTS.md mention** — RESOLVED: yes, add the brief `_body.md.j2` line documenting the new off-path command.
