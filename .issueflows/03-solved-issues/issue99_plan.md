# Plan — Issue #99: Create pull request early

## Goal

Add an opt-in **early PR** path so agents can open a (draft) pull request during
`/iflow-build` after the first push, instead of only at `/iflow-close`. Close
stays the owner of HISTORY, final status, and yolo merge; it updates the
existing PR via the existing list-before-create contract.

## Constraints

- Templates under `src/issue_flow/templates/` are source of truth; edit those,
  not rendered `.cursor/` copies. Re-scaffold via `issue-flow update` / tests.
- Keep [changelog-timing.md](../04-designs-and-guides/changelog-timing.md):
  HISTORY/CHANGELOG still written in `/iflow-close` (step 3) and lands in the
  close commit that updates the PR. Early PR must **not** move history into
  build. The “never after PR open/merged” rule means no *post-close / post-merge*
  history ask — it does **not** forbid writing HISTORY while a draft PR already
  exists from early create.
- Reuse [gh-list-and-watch.md](../04-designs-and-guides/gh-list-and-watch.md):
  always `gh pr list --head <branch>` then create-or-update; never a second PR.
- New toggle follows [skill-behaviour-knobs.md](../04-designs-and-guides/skill-behaviour-knobs.md):
  `[issueflow]` key, bake at `issue-flow update`, no agent runtime reads of
  `config.toml`.
- No Python `gh pr create` helper required (creation stays agent-driven via
  skill text), unless wiring config needs `modes.py` / `config.py` / template
  context — same pattern as sibling knobs.
- Scope: early-PR option + formalize soft `draft` wording in close. Not a new
  slash command. Not Phase-B sub-issue tooling (#12).

### Prior art

- Close PR step (list → create/update, checks snapshot, yolo merge, `draft`
  skips merge): `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2`,
  `commands/iflow-close.md.j2`. **Mirror** that contract from build; close
  remains idempotent.
- Yolo chains to `/iflow-close yolo` and documents a soft `draft` token but
  close never spells `gh pr create --draft` — **fix gap as part of this issue**.
- Knobs plumbing: `src/issue_flow/config.py` (`resolve_*`),
  `src/issue_flow/modes.py` (`write_*` / defaults), template context bake —
  **mirror** for `early_pr`.
- Toolbox: `verify_scaffold.py` asserts close/yolo markers — **extend** with
  early-PR marker checks after template changes.
- Graph: `graphify-out/graph.json` missing this environment; grepped templates
  + design docs instead.

## Approach

1. **Config knob** — `[issueflow] early_pr = false` (default = today’s
   close-only create). Bake into build (+ close/yolo cross-refs) at update.
   Env override `ISSUEFLOW_EARLY_PR` if siblings use env; otherwise
   `config.toml` only is fine — match whatever `auto_close` uses.

2. **Trailing overrides on `/iflow-build`** — `early` / `pr` force on;
   `noearly` force off for this run. Precedence: trailing > baked config >
   default `false`.

3. **When to open** — In `/iflow-build`, after the **first successful push** of
   the issue branch (or at the start of the early-PR step if the branch already
   has a remote tip and no open PR). Require: on issue branch `^\d+-.+`, not
   default branch, remote tracking set. Prefer **draft**:
   `gh pr create --draft --repo <owner/repo> …` with WIP-friendly body +
   `Refs #N` (not `Closes #N` yet). Record `PR: <url> (#<n>, draft)` in
   `issue<N>_status.md`.

4. **Close remains authoritative** — Unchanged sequence for tests / bump /
   HISTORY / Done / commit / push. PR step already list-before-create →
   **update** title/body (may mark ready for review when closing non-draft /
   yolo). HISTORY stays in the close commit. Yolo merge: if PR still draft,
   mark ready then merge (unless user passed `draft`, which still skips merge).

5. **Formalize `draft` on close** — Document parsing of trailing `draft` and
   use of `--draft` on create when no PR exists yet; keep “draft ⇒ skip yolo
   merge”.

6. **Docs / design** — Short design note under
   `.issueflows/04-designs-and-guides/early-pr.md`; mention in workflow doc
   template; add row to knobs table.

7. **Tests** — Render/scaffold tests assert early-PR wording when
   `early_pr=true`, absence/default when false, list-before-create still on
   close, and `--draft` mentioned where expected. Extend
   `verify_scaffold.py` lightly if cheap.

## Files to touch

| Path | Change |
|------|--------|
| `src/issue_flow/config.py` | `early_pr` resolve helper + template context |
| `src/issue_flow/modes.py` | default / read / write / ensure table |
| `src/issue_flow/templates/skills/iflow_build/SKILL.md.j2` | early-PR step + trailing tokens |
| `src/issue_flow/templates/commands/iflow-build.md.j2` | same |
| `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2` | formalize `draft`; note update-existing when early PR |
| `src/issue_flow/templates/commands/iflow-close.md.j2` | same |
| `src/issue_flow/templates/skills/iflow_yolo/SKILL.md.j2` | cross-ref early PR + draft/ready-at-close |
| `src/issue_flow/templates/commands/iflow-yolo.md.j2` | same if needed |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | brief mention |
| `src/issue_flow/agent.py` (config guide) | document `early_pr` if guide lists knobs |
| `tests/test_templating.py` (+ config/modes tests if pattern exists) | bake + wording asserts |
| `.issueflows/00-tools/verify_scaffold.py` | optional marker for early-PR text |
| `.issueflows/04-designs-and-guides/early-pr.md` | decision record |
| `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md` | table row |

## Test strategy

- `uv run pytest` (focus: templating + config/modes coverage for `early_pr`).
- `uv run ruff check src/ tests/`.
- Optional: `uv run .issueflows/00-tools/verify_scaffold.py` after template edits.

## Open questions

Recommended answers below — **Accept** = take these; else say which to flip.

1. **Trigger moment?** → **After first successful push in `/iflow-build`**
   (not at plan confirm / not at init).
2. **Draft vs ready?** → **Always draft when creating early**; close may mark
   ready (yolo does before merge unless `draft` token).
3. **Config name?** → **`early_pr` bool**, default `false` (not an enum).
4. **Trailing tokens?** → **`early`/`pr` on, `noearly` off** on `/iflow-build`
   (and pass-through mention from yolo only if yolo runs build; no new yolo
   merge semantics beyond ready-from-draft).
5. **Min bar?** → Branch pushed; no requirement that tests already pass for
   draft open (close still runs tests).
6. **Issue link in early body?** → **`Refs #N`** early; close may upgrade to
   `Closes #N` when shipping.
7. **Formalize close `draft` in same PR?** → **Yes** (small, related).
