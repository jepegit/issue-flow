# Plan — Issue #210: Iflow in epics

## Goal

Make plain `/iflow` (slash-less `iflow`) epic-aware when there is no focus
issue — so typing `iflow` mid-epic surfaces the stage’s next candidates
instead of a blind `/iflow-init` ask. Mirror what #139 did for `/iflow-pick`.

## Constraints

- `/iflow` stays a dispatcher only; **never** auto-dispatch to `/iflow-pick`,
  `/iflow-epic`, `/iflow-cycle`, or `/iflow-auto`.
- Epic preference is advisory when focus cannot be resolved; branch-derived
  `N` and an existing `01-current-issues/` group still win.
- Templates under `src/issue_flow/templates/` are source of truth; bake via
  `issue-flow update` after ship (dogfood optional).
- Keep scope to dispatcher + docs/tests; no change to epic publish / cycle /
  auto orchestration.

### Prior art

- `/iflow-pick` already prefers active-epic `next_candidates` via
  `issue-flow agent epic-status <N> --json`
  ([`iflow_pick/SKILL.md.j2`](../../src/issue_flow/templates/skills/iflow_pick/SKILL.md.j2);
  shipped in #139).
- Stage-gate offer lives on close/cleanup (#139) — leave alone.
- Dispatcher: [`iflow_iflow/SKILL.md.j2`](../../src/issue_flow/templates/skills/iflow_iflow/SKILL.md.j2)
  + [`commands/iflow.md.j2`](../../src/issue_flow/templates/commands/iflow.md.j2);
  CLI `issue-flow agent state --json` ([`agent.py`](../../src/issue_flow/agent.py))
  has **no** epic fields today.
- Toolbox: none needed.
- Graph: absent.

## Approach

### Interpretation (issue body is one line)

**“Writing iflow should also work inside epic flows”** → the slash-less /
slash dispatcher `iflow` / `/iflow` should understand active epics the way
pick already does, so agents between epic child-issues are not stuck on a
blank init prompt.

### Behaviour

When `/iflow` would enter **state A with no resolvable focus** (no
`^\d+-.+` branch, empty `01-current-issues/`):

1. Scan `{{ issueflows_dir }}/{{ epics_folder }}/epic*_plan.md` (or use
   known epic numbers). For each, run `issue-flow agent epic-status <N>
   --json` when CLI available; collect non-empty `next_candidates` (+
   epic/stage title).
2. If **any** candidates:
   - **Stop** (do not dispatch `/iflow-init` yet).
   - Print epic + stage + candidate numbers/titles.
   - Recommend **`/iflow-pick`** (or `iflow pick`) as the front door;
     allow the user to reply with an explicit `N` and then dispatch
     `/iflow-init <N>` on that answer / trailing number if already given.
3. If **no** epic candidates → keep today’s state A → `/iflow-init` (ask
   for a number).

When focus **is** resolved (branch or single current group), behaviour
unchanged — normal A/B/C/D dispatch. Optional one-line report hint when
an active epic still has other `next_candidates` after close (state D
report): “epic #E stage still has #… — `/iflow-pick` when ready”. Soft
only; no auto-pick.

### CLI (optional but recommended)

Extend `issue-flow agent state --json` with something like:

```json
"epic_hint": {
  "epics": [{"epic": 169, "stage": 2, "next_candidates": [201, 202]}]
}
```

Populated only when focus is missing / state would be A-with-no-N.
Skills prefer this field; manual scan is the fallback.

### Docs

- Workflow doc + rules lifecycle blurb: `/iflow` mentions epic gap-fill
  (suggest pick; never auto).
- Short note in a design doc (extend epic #139 notes or add
  `iflow-epic-awareness.md`) linking #210.

## Files to touch

- `src/issue_flow/templates/skills/iflow_iflow/SKILL.md.j2`
- `src/issue_flow/templates/commands/iflow.md.j2`
- `src/issue_flow/templates/docs/issue-workflow.md.j2` (dispatcher section)
- `src/issue_flow/templates/rules/_body.md.j2` (one sentence if needed)
- `src/issue_flow/agent.py` — `run_state` / state payload `epic_hint`
- `tests/test_cli.py` and/or `tests/test_templating.py` — state JSON +
  template contract (“epic-status” / `next_candidates` / stop-before-init)
- `.issueflows/04-designs-and-guides/` — brief design note
- `docs/` only if workflow template does not cover it

## Test strategy

- `uv run pytest` — template asserts dispatcher skill/command mention epic
  `next_candidates` + never auto-dispatch pick; CLI test that empty-focus
  fixture with an epic plan yields `epic_hint.next_candidates`.
- `uv run ruff check src/ tests/`

## Open questions

1. **Intent confirmation:** treat this as “`/iflow` epic-aware when no
   focus” (recommended, parallel to #139)? Alternatives if wrong:
   (a) `/iflow-issue` creating mid-epic children outside publish,
   (b) only docs that slash-less forms work during epic sessions.
2. **On epic candidates with no focus: stop vs auto-init the single
   candidate?** **Recommended: always stop and ask** (even if one
   candidate) — matches pick’s “never pick silently”.
3. **CLI `epic_hint` in this PR?** **Recommended: yes** — keeps the
   skill’s fast path deterministic like pick’s `epic-status` use.
