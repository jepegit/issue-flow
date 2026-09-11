# Plan — Issue #251: Support no-PR / ops work

## Goal

Add a first-class **ops / no-PR** path: mark and finish work that should not open a PR (staging→prod, flag flips, external deploys), with hard safeguards so product-code diffs cannot silently skip review.

## Constraints

- Templates under `src/issue_flow/templates/` are source of truth; re-render via `issue-flow update`.
- Mirror existing knob patterns (`yolo` token, `label_flows` / `yolo_label`) — bake at render time, not runtime agent TOML reads.
- Normal / yolo close behaviour unchanged when ops signal absent.
- No built-in CD/deploy product; issue-flow only owns workflow routing + close semantics.
- Off-path: never auto-dispatch ops from `/iflow`.

### Prior art

- **Yolo close token** — [`iflow_close/SKILL.md.j2`](../../src/issue_flow/templates/skills/iflow_close/SKILL.md.j2): `yolo` skips changelog confirm, merges PR, switchback. **Mirror:** new `ops` / `nopr` token that skips push/PR (and related sync) instead of auto-merging.
- **Label-driven pick routing** — [`label-driven-flows.md`](../04-designs-and-guides/label-driven-flows.md), pick/command templates, `config.resolve_yolo_label` / `resolve_label_flows`. **Mirror:** `ops_label` (default `"ops"`) under same `label_flows` gate.
- **Modes deferral** — [`modes.md`](../04-designs-and-guides/modes.md): “no-PR close variant” deferred; this issue delivers that behaviour via token + skill, not a separate mode id.
- **Dirty-tree nuance** — `issue-flow agent preflight` already reports `issueflows_only` dirty. **Reuse** for ops safeguard (`.issueflows/`-only dirt OK; product paths block).
- **Toolbox** — `verify_scaffold.py` asserts yolo routing markers; extend similarly for ops markers after scaffold.
- Graph: `graphify-out/graph.json` missing this session — grep-only.

## Approach

### 1. Recognition (three signals, one semantics)

| Signal | Behaviour |
| --- | --- |
| Close token `ops` / `nopr` / `no-pr` | Always takes no-PR close path for this run |
| Config `ops_label` (default `"ops"`) + existing `label_flows` | Pick announces ops route when issue carries label |
| `/iflow-ops` (new off-path skill + command) | Entry for “do ops now”: preflight → optional capture → checklist confirm → `close ops` |

When both `yolo` and `ops` labels present: **ops wins** (safer / more restrictive); announce conflict.

### 2. `/iflow-close` with `ops` token

Branch the close skill (and matching command) so `ops` changes the pipeline:

1. **Preflight / safeguard** — Run `agent preflight` (or equivalent). If dirty paths exist outside `.issueflows/` (and outside intentional ops-tracking-only files), **stop**: refuse silent no-PR; tell user to commit via normal close or stash/discard. `.issueflows/`-only dirty OK.
2. **Ops checklist confirm** (always, even if label-driven) — show short form: what ran / where (env) / result / residual risk. Require explicit yes before finishing.
3. **Skip** — version-bump prompt, HISTORY (default `nohistory` for ops; honour explicit `log "..."` if user insists), sync-branch, push, PR, yolo merge, cleanup reminder tied to PR.
4. **Skip or lighten tests** — if no product-code changes vs default (clean tree or issueflows-only), skip full pytest; if product files changed, **do not** take ops path (caught by step 1).
5. **Still do** — update `issue<N>_status.md` (`- [x] Done` when done), move group to `03-solved-issues` / `02-…`, optional local commit **only** if there are `.issueflows/` (or intentional doc) changes worth keeping — on default or issue branch; never invent a PR for them. Prefer: commit tracking files on current branch if already on an issue branch with no intent to PR; if on default and only tracking dirt, commit on default is allowed for ops (document this exception).
6. **GitHub** — `gh issue close <N> --repo …` after local archive (confirm once as part of checklist).
7. **Branch hygiene** — if on `<N>-*` issue branch with **no unique commits** vs `origin/<default>`, offer switch to default (no force-delete here; cleanup still optional). If unique commits exist, **abort ops path** — those commits need a normal PR or explicit discard.

Mutually exclusive with `yolo` / `draft` on the same invocation: if combined, stop and ask.

### 3. `/iflow-ops` skill

Thin skill (economy profile):

- Resolve root; require focus issue or number → capture.
- **No forced issue branch** — prefer current branch if already correct; allow work on default when tree clean / issueflows-only.
- Guide agent to execute the issue’s ops steps (external CLIs, deploys) with user confirms as needed.
- End by invoking close with `ops` (do not duplicate archive logic).

Register in `COMMAND_NAMES` / `DEFAULT_SKILL_DIRS`, modes `standard`/`all`, step profile, rules/workflow/dispatcher off-path lists, invocation table.

### 4. Pick routing

When `label_flows` and issue has `ops_label`: announce → fold confirm “run `/iflow-ops` (no PR)” into pick confirm. On yes: capture (branch optional — ask create `<N>-slug` vs stay on default) then hand to `iflow-ops`, not yolo / not Phase-3 plan-by-default. Ops issues may still use `/iflow-plan` if user asks, but pick default is ops skill.

### 5. Config / bake

- `DEFAULT_OPS_LABEL = "ops"` in `modes.py`; `read_ops_label` / `Config.resolve_ops_label`; persist on init/update like `yolo_label`; env `ISSUEFLOW_OPS_LABEL`.
- Template context: `ops_label`.
- `verify_scaffold.py` + templating tests assert ops close token + pick routing text when `label_flows` on.

### 6. Design doc + docs

- New `.issueflows/04-designs-and-guides/ops-no-pr.md` (decision, examples, rejected alts).
- Cross-links: label-driven-flows, modes (strike the “deferred” note), rules body, workflow doc, README if it lists commands.

### Out of this PR (follow-ups)

- `/iflow-review` kind `ops` + `/iflow-cycle ops` batch
- Auto-detect ops from issue body text
- Separate scaffolding **mode** that rewrites all close copy

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/modes.py` | `DEFAULT_OPS_LABEL`, read/write/persist `ops_label` |
| `src/issue_flow/config.py` | `resolve_ops_label` + template context |
| `src/issue_flow/templating.py` | register `iflow-ops` / `iflow_ops` |
| `src/issue_flow/step_profiles.py` | default profile for ops (economy) |
| `src/issue_flow/modes.toml` | include new stems in `standard` / `all` if not via `"all"` sentinel |
| `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2` (+ command twin) | `ops` token + branched steps |
| `src/issue_flow/templates/skills/iflow_ops/SKILL.md.j2` (+ `commands/iflow-ops.md.j2`) | new entry skill |
| `src/issue_flow/templates/skills/iflow_pick/…` (+ command) | ops label routing |
| `src/issue_flow/templates/skills/iflow_iflow/…`, rules `_body`, workflow doc, `_invocation_forms` | off-path lists / chat forms |
| `tests/test_modes.py`, `test_templating.py`, maybe `test_config.py` | config + render assertions |
| `.issueflows/00-tools/verify_scaffold.py` | ops marker checks |
| `.issueflows/04-designs-and-guides/ops-no-pr.md` | durable decision |
| dogfood: re-run `issue-flow update` on this repo after merge path | pick up surfaces |

## Test strategy

- `uv run pytest` — extend modes/config/templating tests for `ops_label` persistence/resolution and rendered strings (`ops` token, pick routing, new skill/command present when mode includes them).
- `uv run ruff check src/ tests/`
- Manual: `uv run .issueflows/00-tools/verify_scaffold.py` after marker extension.

## Open questions

1. **HISTORY** — Recommend default skip on ops (`nohistory`). OK, or always append an ops bullet?
2. **Default-branch commits** — Allow committing `.issueflows/` tracking updates on `main` during ops close? (Recommended yes, with confirm.) Or require a throwaway branch even for no-PR?
3. **`/iflow-review ops` in v1?** — Recommend defer; label applied manually or via `gh` for now.
4. **Token name** — Prefer primary `ops` with aliases `nopr` / `no-pr`. Prefer `nopr` as primary instead?
