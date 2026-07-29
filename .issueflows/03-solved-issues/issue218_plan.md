# Issue #218 — Plan

## Goal

After `/iflow-doctor` repairs (and whenever `/iflow-pick` hits a dirty tree that
is **only** `.issueflows/` housekeeping), make **commit those leftovers** the
default next step so pick/branch is not blocked by doctor moves.

## Constraints

- **Templates are source of truth** — edit `src/issue_flow/templates/`, not
  rendered `.cursor/` copies; re-dogfood with `issue-flow update` in this repo.
- **Doctor stays filesystem-only in Python** — `doctor --fix` / `agent repair`
  must **not** auto-`git commit`. Commits stay agent-side behind one confirm
  ([agentic-cli.md](.issueflows/04-designs-and-guides/agentic-cli.md)).
- **Safe path filter** — “issueflows-only dirty” means every
  `git status --porcelain` path is under `{{ issueflows_dir }}/` (default
  `.issueflows/`). Any other path → keep today’s hard stop (commit/stash/abort).
- **No silent commits** — show paths + proposed message; one yes/no. “Yes”
  is the **recommended default** in the prompt wording.
- **No auto-push** — local commit clears the tree; push only if user asks.
- **Back-compat** — unrelated dirty trees behave as today.

### Prior art

- `tracking.audit_issueflows` / `plan_repairs` / `apply_repairs` —
  [`src/issue_flow/tracking.py`](src/issue_flow/tracking.py); doctor repair moves
  only lifecycle groups. **Coexist** — do not teach repair to commit.
- Design contract —
  [`.issueflows/04-designs-and-guides/dirty-issueflows.md`](.issueflows/04-designs-and-guides/dirty-issueflows.md)
  (#47). **Extend** with post-repair git housekeeping.
- `gitutils.dirty_paths` / `working_tree_clean` —
  [`src/issue_flow/gitutils.py`](src/issue_flow/gitutils.py). **Extend** with a
  pure classifier over path lists.
- `/iflow-doctor` + `/iflow-pick` templates —
  `src/issue_flow/templates/skills/iflow_doctor/SKILL.md.j2`,
  `…/iflow_pick/SKILL.md.j2` (+ command twins). **Primary change surface.**
- `issue-flow agent preflight` — [`src/issue_flow/agent.py`](src/issue_flow/agent.py);
  today reports `clean` bool only. **Optional enrich** with `dirty_paths` +
  `issueflows_only` so agents do not re-parse porcelain.
- Toolbox: `verify_scaffold.py` only — no commit helper. **None to reuse** for
  git commit (stays in skill instructions).

## Approach

### 1. Classify “issueflows-only” dirty

Add `gitutils.issueflows_only_dirty(paths, issueflows_dir) -> bool`:

- Empty paths → `True` (vacuously clean / nothing outside).
- Every path (normalize `\` → `/`, strip) must equal `issueflows_dir` or start
  with `issueflows_dir + "/"`.
- Handle porcelain rename lines if `dirty_paths` ever surfaces `old -> new`
  (split on ` -> `, both sides must pass). Prefer fixing `dirty_paths` to emit
  both paths cleanly if rename parsing is currently lossy — keep behaviour
  documented in tests.

Optionally enrich `agent preflight --json` with:

```json
"dirty_paths": [...],
"issueflows_only": true|false|null
```

(`null` when git unknown). Text output can stay short; JSON is the agent API.

### 2. `/iflow-doctor` — commit as default after repair

After successful repair + re-audit, if the tree is dirty and
`issueflows_only`:

1. List the dirty paths.
2. Propose message:
   `chore: doctor housekeeping — archive/sweep .issueflows groups`
   (allow a short edit).
3. **One confirm** (recommended: yes). On yes: `git add` only those paths,
   commit, report hash. On no: leave dirty and note that `/iflow-pick` will
   offer the same commit again.
4. Never push. Never stage paths outside `issueflows_dir`.

If dirty but **not** issueflows-only: report mixed dirty; do not offer the
housekeeping default (user must sort code changes separately).

Mirror the same steps in the command twin
(`templates/commands/iflow-doctor.md.j2`).

### 3. `/iflow-pick` — Phase 2 dirty-tree smart gate

Replace the blunt “stop and ask commit/stash” when dirty with:

| Dirty shape | Behaviour |
| --- | --- |
| Clean | Continue (unchanged). |
| Issueflows-only | **Default offer:** commit housekeeping on the **current** branch (same message pattern as doctor), then proceed to branch + init. Alternatives: stash / abort. One consolidated prompt; recommended = commit. |
| Mixed / code dirty | **Stop** as today — list non-issueflows paths; ask commit/stash/abort. Do not auto-offer “commit everything”. |

Prefer `issue-flow agent preflight --json` (once enriched) or
`git status --porcelain` + the classifier rule as manual fallback.

Update command twin + workflow doc blurb if it restates the clean-tree gate
(`templates/docs/issue-workflow.md.j2` pick section).

### 4. Design doc

Append a short section to `dirty-issueflows.md`:

- Doctor repair does not commit.
- Agents treat issueflows-only leftovers as **default-commit** after doctor and
  at pick Phase 2.
- Still one confirm; no push; never fold `src/` into that commit.

### 5. Out of scope

- Config knob (`doctor_commit_default`) — bake into skills for v1; knob only
  if we later need opt-out.
- Auto-commit inside `doctor --fix` CLI.
- Changing yolo / cycle clean-tree rules beyond pick/doctor (yolo already
  refuses *unrelated* dirt; leave alone unless a shared helper falls out
  naturally).

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/gitutils.py` | `issueflows_only_dirty`; harden `dirty_paths` for renames if needed |
| `src/issue_flow/agent.py` | preflight JSON: `dirty_paths`, `issueflows_only` |
| `src/issue_flow/templates/skills/iflow_doctor/SKILL.md.j2` | post-repair default commit step |
| `src/issue_flow/templates/commands/iflow-doctor.md.j2` | same |
| `src/issue_flow/templates/skills/iflow_pick/SKILL.md.j2` | Phase 2 smart dirty gate |
| `src/issue_flow/templates/commands/iflow-pick.md.j2` | same |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | pick clean-tree wording (if present) |
| `.issueflows/04-designs-and-guides/dirty-issueflows.md` | post-repair commit convention |
| `tests/test_gitutils.py` | classifier (+ rename) cases |
| `tests/test_cli.py` | preflight JSON fields when dirty/clean |
| dogfood `.cursor/skills|commands` via `issue-flow update` | after template edits |

## Test strategy

- `uv run pytest` — unit tests for `issueflows_only_dirty` (empty, only
  `.issueflows/…`, mixed with `src/…`, nested dir name that is *not* a prefix
  false-positive, rename both-sides).
- Preflight `--json` assertions for new fields (monkeypatch `dirty_paths`).
- No need for live `git commit` in unit tests; skill text covered by existing
  scaffold/template tests if any assert doctor/pick markers — extend
  `verify_scaffold` / template tests only if the suite already greps those
  skills for phrases.

## Open questions

1. **Confirm vs silent?** Plan assumes **one confirm** with commit as
   recommended default (never silent). OK?
2. **Push after housekeeping on `main`?** Plan assumes **no** (local only).
   Want optional “commit + push” on default branch?
3. **Preflight JSON enrich in this issue?** Recommended yes (small, helps
   pick). Drop if you want skill-only minimal diff.
