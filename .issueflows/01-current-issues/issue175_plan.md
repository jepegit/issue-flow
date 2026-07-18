# Plan — Issue #175: auto process all yolo issues

## Goal

Make “process every open yolo-labelled issue hands-off” an obvious, one-token
path — without inventing a parallel batch engine. Reuse `/iflow-cycle`, which
already does this via `label:<L>`, and close the discoverability / config gap.

## Constraints

- **Do not** ship a second batch runner. `/iflow-cycle` + `agent queue` already
  process labelled queues, merge each PR, return to default, then continue
  (the merge-conflict mitigation the issue asks for). Parallel dispatch
  ([parallel-cycle.md](../04-designs-and-guides/parallel-cycle.md)) further
  serializes merges when opted in.
- Honour configured `yolo_label` (not a hardcoded `"yolo"` string) —
  same contract as pick / review ([label-driven-flows.md](../04-designs-and-guides/label-driven-flows.md),
  [issue-review-labelling.md](../04-designs-and-guides/issue-review-labelling.md)).
- Off-path only; never auto-dispatch from `/iflow`.
- #172 dependency satisfied (checks watch on yolo close) — no rework there.
- Keep scope to docs + thin cycle UX; no new CLI subcommand unless a test
  needs a pure string helper (prefer skill-side alias).

### Prior art

| Hit | Module / path | Stance |
| --- | --- | --- |
| `/iflow-cycle label:<L>` | `templates/skills/iflow_cycle/SKILL.md.j2` | **Reuse** — this *is* “all issues with label L” |
| `issue-flow agent queue --label` | `agent.py` `run_queue` | **Reuse** as the deterministic queue source |
| Sequential merge-to-default between issues | cycle skill step 5 + yolo close | **Reuse** as conflict strategy (document, don’t reinvent) |
| `yolo_label` config | `config.py` / modes / pick / review | **Honour** in the new `yolo` queue-spec alias |
| `/iflow-review yolo` | issue #174 | **Coexist** — labels first; cycle consumes; optional recipe in docs |
| Parallel cycle merge serialization | `parallel-cycle.md` | **Cite** for conflict notes; no change required |

**Strong overlap decision (for Open questions):** merge into cycle (alias +
docs) vs new `/iflow-yolo-all` skill. Default recommendation: **merge into
cycle** — a twin skill would duplicate confirm/state/onfail machinery.

## Approach

1. **Document the existing path** in cycle skill/command, rules blurb, and
   `issue-workflow.md`:
   - Primary recipe: `/iflow-cycle yolo` (after alias lands) or today
     `/iflow-cycle label:<yolo_label>`.
   - Conflict stance (short): sequential cycle merges each PR and returns to
     a clean default before the next issue; HISTORY/shared files stay
     single-writer; stop-on-fail leaves the tree clean. Point at
     `parallel-cycle.md` for experimental parallel.
2. **Queue-spec alias** in `/iflow-cycle` (and command twin):
   - Bare token **`yolo`** (case-insensitive) expands to
     `label:<resolved yolo_label>` from config (via render-time
     `{{ yolo_label }}` and/or reading `config.toml` at run time — prefer
     baking `{{ yolo_label }}` into the skill text like pick/review, plus an
     instruction to re-read config if the agent has `issue-flow` CLI /
     `config.toml` handy).
   - Keep `label:<L>` for arbitrary labels.
   - Chat forms already work: `iflow cycle yolo`.
3. **Cross-links**
   - `/iflow-review` report step: one-line hint “to run them:
     `/iflow-cycle yolo`”.
   - Design note update or tiny addendum under
     `issue-review-labelling.md` / new
     `yolo-batch-cycle.md` (prefer **short addendum** on the cycle side or
     label-driven-flows — one file, not three).
4. **Tests** — template contracts: cycle skill mentions `yolo` alias +
     `label:{{ yolo_label }}` / configured label; review skill mentions
     `/iflow-cycle yolo`; rules/workflow mention the recipe. No new agent
     CLI required if the alias is skill-side only.
5. **Out of scope**
   - Auto-running review then cycle in one command.
   - Auto-dispatch from pick/status.
   - Changing merge/conflict machinery or parallel cycle.
   - Filtering the queue by re-judging fitness (label is the signal; per-issue
     yolo scope abort already stops unfit specs).

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/templates/skills/iflow_cycle/SKILL.md.j2` | `yolo` alias in Input; conflict/doc recipe |
| `src/issue_flow/templates/commands/iflow-cycle.md.j2` | Mirror |
| `src/issue_flow/templates/skills/iflow_review/SKILL.md.j2` | Post-apply hint → `/iflow-cycle yolo` |
| `src/issue_flow/templates/commands/iflow-review.md.j2` | Mirror hint |
| `src/issue_flow/templates/rules/_body.md.j2` | One-line “all yolo issues” recipe on cycle blurb |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | Same in cycle section / detours |
| `.issueflows/04-designs-and-guides/label-driven-flows.md` or small sibling | Document alias + sequential conflict stance |
| `tests/test_templating.py` / `tests/test_init.py` | Contract asserts for alias + hint |
| Dogfood via `issue-flow update` | After templates land |

## Test strategy

- `uv run pytest` — template/init asserts:
  - cycle surfaces document `yolo` → `label:<yolo_label>` (or baked default).
  - review surfaces mention `/iflow-cycle yolo`.
  - rules/workflow mention the all-yolo recipe.
- `uv run ruff check src/ tests/` (likely no Python changes).
- Manual smoke (optional): `issue-flow agent queue --label yolo --json` on a
  repo that has labelled issues.

## Open questions

_Resolved 2026-07-18 — plan accepted with recommended defaults:_

1. **Alias + docs on `/iflow-cycle`** (no new `/iflow-yolo-all` skill) — confirmed.
2. **Alias token:** bare **`yolo`** — confirmed.
3. **Compose with `/iflow-review`:** hint only — confirmed.
4. **Empty queue:** keep as-is — confirmed.

**Status:** accepted — ready for `/iflow-start`.
