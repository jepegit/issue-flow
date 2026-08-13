# Plan — Issue #12: Create linked (sub) issues for over-ambitious issues

## Goal

Give agents a **confirm-gated way to split one over-large GitHub issue into
linked child issues** (GitHub native sub-issues), plus a reusable skill for
*how* to create that link — closing the Phase B gap that `/iflow-pick` has
only mentioned since #63.

## Constraints

- Templates under `src/issue_flow/templates/` are the source of truth; edit
  those, not already-rendered `.cursor/` copies. Re-scaffold via
  `issue-flow update` / tests.
- Off-path: `/iflow` never auto-dispatches the new surface. Never create
  GitHub issues or parent/child links without one consolidated confirm
  (show titles + bodies first).
- GitHub only (`gh` / `gh api`). GitLab is out of scope.
- Skill-authoring house rules
  ([skill-authoring.md](../04-designs-and-guides/skill-authoring.md)):
  user-invoked, `disable-model-invocation: true`, no trigger-bait sections.
- Coexist with `/iflow-epic` and `/iflow-issue` — do **not** merge them.
  Epic remains the staged, dependency-aware program. Split is the *flat*
  parent/child cut when one issue is too big for one PR but is not a
  multi-stage epic.
- Do not auto-create children from `/iflow-pick` / `/iflow-issue` /
  `/iflow-plan`. Those surfaces **offer** `/iflow-split` (or `/iflow-epic`
  when stages/deps are needed) and stop.
- Parent issue stays **open** as the tracker. Do not close it from split.
- No parking of generated children under `02-partly-solved-issues/` in v1
  (they are new GitHub issues; pick them later). Parent local group, if
  present in `01-current-issues/`, moves to `02-partly-solved-issues/`.

### Prior art

| Hit | Role | Plan |
| --- | --- | --- |
| `skills/iflow_issue/SKILL.md.j2` | Draft + confirm + `gh issue create`; over-large → mention epic only | **Mirror** draft body shape; **replace** the note-only line with an offer to `/iflow-split` |
| `skills/iflow_epic/SKILL.md.j2` | Staged specs + `publish` + markdown task list on the anchor | **Coexist.** Split does not invent stages/`Depends on`/`Published:` |
| `skills/iflow_pick/SKILL.md.j2` step 6 + constraint | Phase B of #63: mention-only, no auto-create | **Lift** Phase B: offer `/iflow-split` / `/iflow-epic`; still no silent create |
| `commands/iflow-pick.md.j2` + `docs/issue-workflow.md.j2` | Same Phase B wording | Update in lockstep |
| `create-non-epic-issue.md` | Over-large drafts: mention epic, no auto-split | Amend: mention split **or** epic |
| `templating.py` `COMMAND_NAMES` / `SKILL_DIRS` | Surface registration | Add `iflow-split` / `iflow_split` |
| `step_profiles.toml` | Economy / reasoning | `iflow_split = "reasoning"` |
| `00-tools/verify_scaffold.py` | Scaffold marker checks | Extend if it enumerates command/skill lists |
| Graph | `graphify-out/graph.json` missing | Grep-only |

## Approach

### Naming

**`/iflow-split`** (skill stem `iflow_split`). Reads as “cut this issue into
children.” Rejected: folding into `/iflow-issue` (that skill creates *one*
issue), `/iflow-sub` (opaque), auto-running from pick (pick stays a chooser).

### When to split vs epic

- **Split** — 2–5 flat children, each one branch / one PR, no staged
  dependencies. Parent becomes the tracker.
- **Epic** — sequential stages, `Depends on`, yolo-fitness, publish
  idempotency. If a proposed split needs that, **stop** and point at
  `/iflow-epic` (create an anchor with `/iflow-issue epic` when missing).

### `/iflow-split` behaviour

1. **Resolve parent `N`.** Trailing number, else focus issue in
   `01-current-issues/`, else issue-style branch `^\d+-.+`. Ambiguous → ask.
2. **Preflight.** Same root / default-branch / fetch / dirty report as
   pick/issue. Creating children does not require a clean tree; branching
   onto a child later does.
3. **Draft children.** Propose 2–5 titles + light bodies (Problem /
   context, Spec, Acceptance, optional Out of scope). Each body ends with
   `Sub-issue of #<N>.` Refine until the user confirms the set.
4. **Size gate.** If the cut wants stages or explicit deps → recommend
   epic and **do not create**.
5. **Consolidated confirm** (normal prose). One prompt: parent `#N`,
   child titles, that each will be created then linked as a GitHub
   sub-issue, and that a `- [ ] #<M>` task-list block will be appended on
   the parent. No yes → stop.
6. **Create + link (idempotent).** For each unpublished child:
   - `gh issue create --repo <owner/repo>` (labels/milestones only if the
     user asked this turn).
   - Link as a **native sub-issue** via REST. `sub_issue_id` is the
     child’s numeric **database id**, not the issue number. `gh api -f`
     stringifies and 422s — send JSON:

     ```bash
     CHILD_ID=$(gh api repos/<owner>/<repo>/issues/<M> --jq .id)
     echo "{\"sub_issue_id\": ${CHILD_ID}}" | \
       gh api repos/<owner>/<repo>/issues/<N>/sub_issues -X POST --input -
     ```

   - Append `- [ ] #<M>` under a `## Sub-issues` heading on the parent
     (`gh issue edit --body-file`, append/patch only). Task list is the
     fallback if the sub-issue API is unavailable (plan, 404, permission).
   - Record created numbers in the parent’s local status (or a short note
     in the parked status file) so re-runs skip already-linked children
     (`GET .../issues/<N>/sub_issues`).
7. **Local parent.** If `issue<N>_*` is in `01-current-issues/`, move the
   group to `02-partly-solved-issues/` (parent is now a tracker, not the
   focus). Status checkbox stays `- [ ] Done`.
8. **Handoff.** Ask whether to start the first child (`/iflow-pick`-style
   branch + `/iflow-init`). Do **not** auto-run plan/build.

### Shared “how to link” fragment

Put the REST id/`--input` recipe in the split skill (single source). Other
skills point at it; they do not inline a second copy. Optional thin CLI
`issue-flow agent sub-issue-add <parent> <child> -C <root>` wraps the
gotcha (recommended — see Open questions). Skills still work with raw
`gh api` if the CLI is missing.

### Wire existing surfaces (offer only)

- **`/iflow-pick`** step 6: drop “Phase B of #63 / out of scope”. If the
  chosen issue is over-large, **mention** `/iflow-split` (flat) or
  `/iflow-epic` (staged) and ask; default remains “proceed with the whole
  issue.” Never create children inside pick.
- **`/iflow-issue`** + **`/iflow-plan` scope check:** same offer.
- **`/iflow` dispatcher:** add `/iflow-split` to the never-auto-dispatch
  list (command + skill + rules + workflow doc + slash-less table).
- **README** helper list.

### Out of scope (v1)

- Retrofitting `/iflow-epic publish` to also call the sub-issues API
  (follow-up; epic keeps task lists).
- Auto-split without confirm; silent pick routing.
- Closing the parent; converting the parent into an epic plan file.
- Parking child `issue<M>_*` groups under `02-` at create time.
- GitLab; GraphQL `addSubIssue` (REST is enough).

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/templates/skills/iflow_split/SKILL.md.j2` | **New** skill |
| `src/issue_flow/templates/commands/iflow-split.md.j2` | **New** command mirror |
| `src/issue_flow/templating.py` | Register stems |
| `src/issue_flow/step_profiles.toml` | `iflow_split = "reasoning"` |
| `src/issue_flow/agent.py` (or sibling) | Optional `sub-issue-add` CLI |
| `src/issue_flow/templates/skills/iflow_pick/SKILL.md.j2` | Phase B → offer split/epic |
| `src/issue_flow/templates/commands/iflow-pick.md.j2` | Same |
| `src/issue_flow/templates/skills/iflow_issue/SKILL.md.j2` | Over-large → offer split/epic |
| `src/issue_flow/templates/commands/iflow-issue.md.j2` | Same |
| `src/issue_flow/templates/skills/iflow_plan/SKILL.md.j2` | Scope-check offer |
| `src/issue_flow/templates/skills/iflow_iflow/SKILL.md.j2` | Off-path list |
| `src/issue_flow/templates/commands/iflow.md.j2` | Off-path list |
| `src/issue_flow/templates/rules/_body.md.j2` | Chat table + lifecycle blurb |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | Replace Phase B “out of scope”; document `/iflow-split` |
| `README.md` | Helper bullet |
| `.issueflows/04-designs-and-guides/linked-sub-issues.md` | Decision record |
| `.issueflows/04-designs-and-guides/create-non-epic-issue.md` | Amend over-large note |
| `tests/test_templating.py` | Manifest + render + off-path asserts |
| `tests/test_modes.py` | Standard mode picks up new stems via `all` |
| `HISTORY.md` | Unreleased bullet (at `/iflow-close`) |

`modes.toml` `[modes.standard]` is `all` — no edit. `[modes.simple]` stays
without split (create-on-GitHub surface, same as issue/epic).

## Test strategy

- `uv run pytest` — extend `test_templating.py` like `/iflow-issue`:
  skill/command templates exist; rendered skill has confirm + REST
  `--input` / `sub_issue_id` warning; pick/issue no longer say
  “Phase B is out of scope”; dispatcher/rules list `/iflow-split`.
- If CLI helper lands: unit-test JSON body (integer id) and “already
  linked” skip with mocked `gh api`.
- `uv run ruff check src/ tests/`
- Optional: `uv run .issueflows/00-tools/verify_scaffold.py` if marker
  lists need the new stem.

## Open questions

1. **Name.** `/iflow-split` (recommended) vs `/iflow-sub` vs
   `/iflow-issue split <N>` token. **Recommend split** — new off-path
   surface, same pattern as issue/epic/fix.
2. **CLI helper.** Ship `issue-flow agent sub-issue-add` in this PR
   (recommended) vs skill-only `gh api`. **Recommend the helper** — the
   id/`-f` 422 is a known agent footgun.
3. **Epic publish.** Leave task-list-only (recommended for v1) vs also
   attach native sub-issues on publish. **Recommend follow-up.**
4. **Parent close.** Leave open as tracker (recommended) vs close after
   children exist. **Recommend leave open** — GitHub sub-issue progress
   lives on the parent.
