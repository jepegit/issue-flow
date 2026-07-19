# Issue #181 — plan: create non-epic issue skill

## Goal

Add an off-path `/iflow-issue` skill (and mirrored slash command) that creates **one well-specified normal GitHub issue**, then optionally sets up the normal lifecycle branch + `/iflow-init` — filling the gap between `/iflow-fix` (iterative small-fixes bucket) and `/iflow-epic` (multi-issue staged work).

## Constraints

- Templates under `src/issue_flow/templates/` are source of truth; edit those, not already-rendered copies. Re-scaffold via `issue-flow update` / tests.
- Off-path: never auto-dispatched by `/iflow`.
- Never create a GitHub issue or branch without explicit confirmation (show title/body first).
- GitHub only (`gh`); same as fix/epic/pick.
- Comment mandate: **update the docs** (workflow doc + enumeration surfaces).
- Skill-authoring house rules (`.issueflows/04-designs-and-guides/skill-authoring.md`): user-invoked, `disable-model-invocation: true`, no trigger-bait sections.
- Coexist with `/iflow-pick fix` and `/iflow-fix` — do not merge them (same coexistence decision as issue-fix design doc).

### Prior art

| Hit | Role | Plan |
| --- | --- | --- |
| `skills/iflow_fix/SKILL.md.j2` + `commands/iflow-fix.md.j2` | Creates GH issue + branch + init; then stays in loop | **Mirror** Phase-1 setup shape; **do not** copy the fix loop |
| `skills/iflow_pick/SKILL.md.j2` (`fix` shortcut) | One-shot general-fixes issue → branch → init → handoff to plan | Closest lifecycle handoff; new skill is for a *named, well-specified* issue body, not a chore bucket |
| `skills/iflow_epic/SKILL.md.j2` | Needs an existing epic **anchor**; today asks user to create one manually | Point missing-anchor case at `/iflow-issue` |
| `templating.py` `COMMAND_NAMES` / `SKILL_DIRS` | Surface registration | Add new stems |
| `step_profiles.toml` | Per-step economy/reasoning | Add `iflow_issue` |
| `.issueflows/04-designs-and-guides/issue-fix-interactive.md` | Coexistence pattern for create-issue skills | Follow; add sibling design note under `04-designs-and-guides/` |
| Toolbox `verify_scaffold.py` | End-to-end scaffold marker checks | Extend only if it enumerates command/skill lists that would break |
| Graph | `graphify-out/graph.json` missing | Grep-only discovery |

## Approach

### Naming (recommended)

**`/iflow-issue`** (skill stem `iflow_issue`). Reads as the third creation mode next to fix / epic. Alternatives (`iflow-new`, `iflow-create`) left in Open questions.

### Behaviour

1. **Input** — free text after the command = draft seed (title hint and/or short description). Bare `/iflow-issue` → ask for a one-line intent.
2. **Preflight** — resolve project root; default branch; `git fetch --prune`; report branch + dirty/clean (same as fix/pick).
3. **Draft the issue** — propose title + body using a light structure (not a full `/iflow-plan`):
   - Problem / context
   - Spec (what to change)
   - Acceptance criteria
   - Out of scope (optional)
   Refine with the user until they confirm. If the draft is clearly over-large for one PR, **mention** epic / split (same note-only stance as pick Phase B) — do not auto-create sub-issues.
4. **Create** — `gh issue create --repo <owner/repo>` after one confirm showing final title/body (optional label/milestone only if the user asked for them in this turn; v1 does not invent labels).
5. **Start work? (default yes path)** — after create, offer the pick-style setup under one confirm:
   - branch `<N>-<short-slug>` off default (ask base if currently on non-default)
   - run `/iflow-init` for `N`
   - ask whether to continue with `/iflow-plan` (do **not** auto-run plan)
   - Allow **create-only** if the user declines the branch step (useful for epic anchors or parking work for later `/iflow-pick`).
6. **Cross-links**
   - `/iflow-epic`: when no anchor exists, tell user to run `/iflow-issue` (title prefix `Epic:`, optional `epic` label if present) then return.
   - `/iflow-review`, docs, `/iflow` off-path lists: mention `/iflow-issue` as the way to create a normal single issue.
   - `/iflow-fix` / pick-fix docs: one-line “for a single well-defined deliverable use `/iflow-issue`”.

### Registration & docs touchpoints

- Register in `COMMAND_NAMES` + `SKILL_DIRS`; profile default **reasoning** (drafting a good issue body).
- Enumerate in: `rules/_body.md.j2` chat-invocation table, `skills/iflow_iflow` + `commands/iflow.md.j2` off-path lists, `docs/issue-workflow.md.j2`, `README.md` if it lists helpers.
- Bump manifest/test expectations (+1 skill everywhere; +1 command for editors with `commands_dir`).
- Add `.issueflows/04-designs-and-guides/create-non-epic-issue.md` (decision record).
- Dogfood: after merge path, this repo’s own scaffold gets the skill via `issue-flow update` (close/start as usual).

### Out of scope (v1)

- CLI `issue-flow agent …` helper for create (skills call `gh` directly, like fix).
- Replacing `/iflow-pick fix` or folding `/iflow-fix` into this.
- Auto-labelling / auto-milestone.
- Local-only (no GitHub) issues.

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/templates/skills/iflow_issue/SKILL.md.j2` | **New** skill playbook |
| `src/issue_flow/templates/commands/iflow-issue.md.j2` | **New** slash-command mirror |
| `src/issue_flow/templating.py` | Add `iflow-issue` / `iflow_issue` to registries |
| `src/issue_flow/step_profiles.toml` | `iflow_issue = "reasoning"` |
| `src/issue_flow/templates/skills/iflow_epic/SKILL.md.j2` | Point missing-anchor → `/iflow-issue` |
| `src/issue_flow/templates/skills/iflow_iflow/SKILL.md.j2` | Off-path list |
| `src/issue_flow/templates/commands/iflow.md.j2` | Off-path list |
| `src/issue_flow/templates/skills/iflow_fix/SKILL.md.j2` (+ command) | Cross-ref coexistence |
| `src/issue_flow/templates/skills/iflow_review/SKILL.md.j2` (+ command) | “create issues via …” pointer |
| `src/issue_flow/templates/rules/_body.md.j2` | Invocation table row |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | Document the skill |
| `README.md` | Mention if helpers are listed |
| `tests/test_templating.py` | Manifest counts, membership, focused render test |
| `.issueflows/04-designs-and-guides/create-non-epic-issue.md` | Design decision |
| `.issueflows/00-tools/verify_scaffold.py` | Only if assertions enumerate surfaces |

## Test strategy

- `uv run pytest` — extend templating/manifest tests; add focused test that rendered `/iflow-issue` skill mentions confirmation, off-path, and handoff to `/iflow-init` / `/iflow-plan`.
- `uv run ruff check src/ tests/`
- Optional: `uv run .issueflows/00-tools/verify_scaffold.py` if markers need updating.

## Open questions

1. **Name:** accept **`iflow-issue`**, or prefer `iflow-new` / `iflow-create`?
2. **Default after create:** recommended **offer branch+init (confirm)** with create-only opt-out — or always create-only and leave setup to `/iflow-pick`?
3. **Body shape:** recommended light **Context / Spec / Acceptance** template — or freer prose only?
4. **Epic anchors:** should `/iflow-issue` accept a hint like `epic` that prefixes title with `Epic:` and applies the `epic` label when it exists?
