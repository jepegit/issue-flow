# Plan — Issue #228: Allow picking based on label

## Goal

Let `/iflow-pick` take a first-class `label:<L>` filter so the shortlist is
issues carrying that GitHub label (not only a soft ranking hint). Confirm
`/iflow-cycle label:<L>` already covers the batch side; tighten docs so both
paths are discoverable.

## Constraints

- Templates under `src/issue_flow/templates/` are source of truth; re-render
  via `issue-flow update` for local `.cursor/` copies.
- Keep pick interactive: never auto-pick even when the filtered shortlist has
  one entry.
- Do not weaken cycle safeguards or invent a second queue planner.
- Free-form topic/milestone hints stay soft bias; `label:<L>` is hard filter.
- Back-compat: bare `/iflow-pick` and `/iflow-pick fix` unchanged.

### Prior art

- **Cycle already filters by label** — `/iflow-cycle label:<L>` and alias
  `yolo` → `label:<yolo_label>` via `issue-flow agent queue --label`
  (`agent.run_queue`, `gitutils.gh_issue_list_meta(..., label=)`). Docs:
  `iflow_cycle` skill/command, `docs/issue-workflow.md`,
  `.issueflows/04-designs-and-guides/label-driven-flows.md` (#106, #175).
- **Pick only soft-biases** — Input says “a hint (milestone / label / topic) —
  bias the candidate ranking”; Phase 1 ranks by labels but does not hard-filter
  (`iflow_pick` skill + `commands/iflow-pick.md.j2`). Workflow doc omits
  `label:` syntax for pick.
- **Listing helper** — `gh_issue_list_meta(cwd, repo, label=)` already wraps
  `gh issue list --label`. No new CLI required for pick if the skill calls
  `gh` / documents the same filter; optional thin reuse only if tests want a
  deterministic agent surface (prefer not unless needed).
- **Toolbox** — `verify_scaffold.py` checks label-driven yolo routing text;
  extend only if scaffold markers should assert pick `label:` docs.

## Approach

1. **Pick input** — Add explicit token `label:<L>` (case-insensitive label name
   after the colon; strip whitespace). Compatible with `noplan` /
   `root:` / `repo:` tokens. Keep free-form hints as soft bias only when
   `label:` is absent.
2. **Phase 1 sourcing when `label:<L>` present**
   - GitHub: `gh issue list --state open --label <L> --json
     number,title,labels,milestone,updatedAt` (or equivalent via existing
     helper). Drop locally captured issues as today.
   - Parked / epic candidates: include only if they carry `<L>` (check via
     `gh issue view <n> --json labels` when unclear). Announce the active
     filter in the shortlist header.
   - Empty after filter → stop: “no open issues with label `<L>`.”
3. **Ranking** — Same rank rules inside the filtered set; still ask confirm.
4. **Cycle** — No behaviour change. Cross-link from pick docs/examples to
   `/iflow-cycle label:<L>` and `/iflow-cycle yolo`. Optionally one line in
   `label-driven-flows.md` that pick filters + cycle queues share the same
   GitHub label selection idea.
5. **Docs / templates to edit**
   - `templates/skills/iflow_pick/SKILL.md.j2`
   - `templates/commands/iflow-pick.md.j2` (Input + Phase 1 + examples)
   - `templates/docs/issue-workflow.md.j2` (pick “What you pass” + example)
   - Design note in `label-driven-flows.md` (durable decision)
6. **Tests** — Extend templating/init assertions so rendered pick skill/command
   mention `label:<L>` as a hard filter (mirror #175 cycle-alias style checks
   in `tests/test_templating.py` / `tests/test_init.py`). No new runtime CLI
   unless we choose to expose one (default: skill-only).

## Files to touch

| Path | Change |
|------|--------|
| `src/issue_flow/templates/skills/iflow_pick/SKILL.md.j2` | Document `label:<L>`; hard-filter steps |
| `src/issue_flow/templates/commands/iflow-pick.md.j2` | Same + example `/iflow-pick label:enhancement` |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | Pick accepts `label:<L>`; point at cycle |
| `.issueflows/04-designs-and-guides/label-driven-flows.md` | Note pick filter vs cycle queue |
| `tests/test_templating.py` (and/or `test_init.py`) | Assert `label:<` / hard-filter wording |
| Local scaffold (post-change) | `uv run issue-flow update` so `.cursor/` matches |

## Test strategy

- `uv run pytest tests/test_templating.py tests/test_init.py -k pick` (and any
  new focused test for the `label:` token).
- Full `uv run pytest` before close.
- Manual sanity: read rendered skill; confirm cycle docs still accurate (no
  regression expected).

## Open questions

1. **Hard filter vs soft bias for `label:<L>`** — Recommend **hard filter**
   (issue wording: “selects among”). Soft bias stays for free-form hints only.
2. **Cycle gap?** — Recommend **docs-only** for cycle (already supports
   `label:<L>` / `yolo`). Say if you wanted something else (e.g. intersection
   `yolo` ∧ `label:foo`).
3. **New CLI?** — Recommend **no** (`gh issue list --label` in the skill is
   enough). Say yes if you want `issue-flow agent pick-candidates --label`.
