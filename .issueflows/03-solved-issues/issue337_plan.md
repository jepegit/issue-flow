# Plan: #337 — noob Recommended should follow epic session, not raw `next_command`

## Goal

When `noob` is on and there is no focus issue, the footer’s **Recommended**
line names the real next human command (ask `/iflow`, pick a candidate, or
publish the current stage) instead of echoing `next_command` (`/iflow-capture`
or `none`). `agent state` `next_command` stays unset in the epic gap.

## Constraints

- Do not change `#210` / `#333`: `next_command` remains unset when
  `epic_hint.epics` is non-empty; `/iflow` still does not auto-dispatch pick.
- Footer still never auto-dispatches.
- Do not turn `noob` on in this repo’s `config.toml`.
- Templates are the source of truth; re-run `issue-flow update` so scaffolded
  skills pick up the footer.
- House rules: [skill-authoring.md](../04-designs-and-guides/skill-authoring.md).
- Contract: [epic-start.md](../04-designs-and-guides/epic-start.md),
  [iflow-epic-awareness.md](../04-designs-and-guides/iflow-epic-awareness.md),
  [skill-behaviour-knobs.md](../04-designs-and-guides/skill-behaviour-knobs.md).

### Prior art

- `src/issue_flow/templates/skills/_noob_next.md.j2` — “print `next_command` as
  Recommended”; epic stem list is `/iflow`, `/iflow-pick`, `/iflow-status`
  (no publish). Line 63 forbids inventing steps outside that list plus
  `next_command` — that is why the batbase agent could not name publish.
- `issue_flow.agent.run_state` / `_collect_epic_hints` — no focus + empty
  `epic_hint.epics` → `next_command = /iflow-capture`; candidates present →
  `next_command` stays `null`. Session is reported but does not change
  `next_command` (`tests/test_cli.py` `#210` / `#333`).
- `issue-flow agent epic-status <N> --json` — already exposes unpublished
  specs (`state: "unpublished"`) and `next_candidates`. Existing payload
  from `state` alone cannot tell “unpublished stage” from “nothing to queue”.
- Toolbox: `verify_scaffold.py` — use after the footer change to confirm
  novice/noob scaffolds still render. No new `00-tools/` script.
- Graph: no `GRAPH_REPORT.md` hits for noob / `_noob_next`.

## Approach

Footer-first. Do **not** add a `noob_recommend` field or change
`next_command` in `run_state`.

Rewrite `_noob_next.md.j2` step 1 as a decision table (still run
`issue-flow agent state --json` first):

| Condition | **Recommended** |
| --- | --- |
| Focus exists | `next_command` (today: plan / build / close) |
| No focus + `epic_hint.epics` non-empty + session on | `/iflow` (one-and-ask; first candidate in the why line) |
| No focus + `epic_hint.epics` non-empty + no session | `/iflow-pick` (`#210`) |
| No focus + session + empty `epic_hint` | Run `epic-status <epic_session.epic> --json`. If the current stage has unpublished specs → `/iflow-epic <N> publish`. Else `/iflow-status` (do not capture). |
| Else | `next_command` (`/iflow-capture`) |

Why `/iflow` (not pick) when the session is on: `#333` one-and-ask. Why
pick when there is no session: `#210`. Chore branches (`chore/168-…`) have
no focus, so they use the same table — that is the “Recommended: none”
bug.

Widen the **epic** stem “relevant” list to include
`/iflow-epic <N> publish` (unpublished current stage). Update the
“never invent extra steps” line so the table above plus that list is the
allowed set.

Docs (one-line each): `docs/configuration.md`,
`skill-behaviour-knobs.md` (`noob` row), `epic-start.md` (noob footer
uses session + hint, not raw `next_command`).

After the template lands, `issue-flow update` in this worktree so
`.cursor/skills` match.

## Files to touch

- `src/issue_flow/templates/skills/_noob_next.md.j2` — decision table +
  publish on the epic stem list.
- `tests/test_templating.py` — assert the rendered noob footer contains
  the table phrases (session → `/iflow`, unpublished → publish, do not
  “print `next_command` as Recommended” as the only rule).
- `docs/configuration.md` — `noob` description.
- `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md`
- `.issueflows/04-designs-and-guides/epic-start.md`
- `.issueflows/04-designs-and-guides/test-registry.md` — row for the new
  templating assertions if we mark them essential.
- This repo’s rendered `.cursor/skills/**` via `issue-flow update` (not
  hand-edited).

## Test strategy

- `uv run pytest tests/test_templating.py tests/test_cli.py -q --tb=line`
  (footer render + existing `#210` / `#333` `next_command` contracts).
- `uv run ruff check src/ tests/`
- `uv run .issueflows/00-tools/verify_scaffold.py` if the footer change
  is easy to miss in a novice scaffold.
- No new `agent state` tests unless a regression shows `next_command`
  drifted (it must not).

## Open questions

None that block coding. `/iflow` vs `/iflow-pick` when the session is on
is called in Approach (`/iflow`). Say **Revise** if you want pick instead.
