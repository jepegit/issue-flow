# Issue #113 — plan

## Goal

Add a **`### MODEL & EXECUTION DIRECTIVE`** section to each packaged iflow skill (and matching command templates where they exist) so agents know whether to prioritize **economy/speed** or **reasoning depth** for that step. Ship **packaged defaults**, optional **per-step overrides** in `.issueflows/config.toml`, and a master toggle — mirroring existing knobs like `caveman_default` / `label_flows`.

## Constraints

- **Templates are source of truth** — edit `src/issue_flow/templates/`, not rendered `.cursor/skills/`.
- **Bake at render time** — like `yolo_label` and `caveman_default`, config values flow through `Settings.template_context()`; agents do not read `config.toml` at runtime.
- **Advisory only** — Cursor SKILL.md frontmatter has no supported `model:` field (only `name`, `description`, `paths`, `disable-model-invocation`, `metadata`). Directives instruct the human/agent to pick a model; they cannot force a switch programmatically.
- **Editor-neutral base, Cursor hint** — economy/reasoning wording works everywhere; add a Cursor-specific line (Auto vs thinking model) only when `editor == "cursor"`, per [editor-profiles.md](../04-designs-and-guides/editor-profiles.md).
- **CLI fast-path unchanged** — mechanical `issue-flow agent *` steps stay as-is; directives are for the agent skill layer.
- **Back-compat** — default `step_directives = true`; existing projects get sensible directives on next `issue-flow update`.

### Prior art

- **`caveman_default` / `grill_me_default` / `label_flows` / `yolo_label`** — `config.py` resolvers + `modes.py` read/write + `template_context()` injection ([label-driven-flows.md](../04-designs-and-guides/label-driven-flows.md)).
- **`modes.toml` + `modes.py`** — packaged defaults with project override tables; good pattern for per-step profiles.
- **`rules/_body.md.j2` include** — shared Jinja partial across multiple surfaces; reuse for one `_model_directive.md.j2` partial.
- **`disable-model-invocation: true`** — all lifecycle skills already explicit-invocation only ([issue79 design](../03-solved-issues/issue79_original.md)).
- **`verify_scaffold.py`** — regression guard for template rendering after config/skill changes.
- **Graph communities 446, 462, 466** — config resolution, `template_context()`, skill/command templating.
- **None found** for existing model-directive or step-profile machinery (toolbox + grep + graph checked).

## Approach

### 1. Step profiles (packaged defaults)

Add packaged data — e.g. `src/issue_flow/step_profiles.toml` — mapping each **skill stem** to `economy` or `reasoning`:

| Profile | Skills (initial defaults) |
|---------|---------------------------|
| **economy** | `iflow_init`, `iflow_close`, `iflow_cleanup`, `iflow_pause`, `iflow_status`, `iflow_comments`, `iflow_version_bump`, `iflow_history_update`, `iflow_graphify`, `iflow_iflow` |
| **reasoning** | `iflow_plan`, `iflow_start`, `iflow_pick`, `iflow_yolo`, `iflow_fix`, `iflow_archive` |

Rationale: init/close/cleanup/status are checklists + `gh`/`git`; plan/start/pick/fix need judgment. Yolo chains plan+start so stays **reasoning** despite “fast” name. `iflow_iflow` is lightweight dispatch → economy.

New module `step_profiles.py`: load packaged table, merge optional `[issueflow.step_profiles]` overrides from project `config.toml` (project wins on key clash), validate stems against `SKILL_DIRS`.

### 2. Config knobs

Under `[issueflow]` (same persistence/env pattern as other flags):

| Key | Default | Purpose |
|-----|---------|---------|
| `step_directives` | `true` | Master toggle — when `false`, omit the directive block entirely |
| `model_label_flows` | `false` | *(optional v1 — see Open questions)* Enable label-based session profile hints |
| `deep_model_label` | `"deep"` | Label name that bumps session toward **reasoning** |
| `fast_model_label` | `"fast"` | Label name that bumps session toward **economy** |

Env mirrors: `ISSUEFLOW_STEP_DIRECTIVES`, `ISSUEFLOW_MODEL_LABEL_FLOWS`, etc.

Resolution order unchanged: persisted `config.toml` > env > default.

### 3. Shared Jinja partial

Create `src/issue_flow/templates/skills/_model_directive.md.j2`:

- Rendered only when `step_directives` is true.
- Takes `step_profile` (`economy` | `reasoning`) from context (per-skill render pass).
- **Economy** text: prioritize speed/token economy; Cursor → prefer **Auto** or a fast model.
- **Reasoning** text: prioritize design judgment; Cursor → switch to a thinking-capable model.
- Short, identical header: `### MODEL & EXECUTION DIRECTIVE`.

Each lifecycle skill template `{% include %}` the partial **after `## When to use`** (visible early, before Instructions). Mirror into matching `commands/*.md.j2` files for editors that still ship commands.

Pass `step_profile` into each skill render in `templating.py` / `init.py` loop (lookup by skill stem).

### 4. Label-driven hints (lightweight)

If `model_label_flows` is enabled, extend **`iflow_pick`** (only) to check issue labels (same `gh` JSON already fetched) and, when `deep_model_label` / `fast_model_label` matches, announce a **session profile override** in the pick report. Individual skill directives stay baked defaults; pick's note tells the agent to honour the label for the whole issue. No new auto-dispatch — announcement only (parallel to yolo routing pattern but simpler).

Defer wiring into `/iflow-init` when issue is given by number directly without pick.

### 5. Docs & design memory

- Short entry in `04-designs-and-guides/step-model-directives.md` (decision, limitations, link #113).
- Paragraph in `docs/issue-workflow.md.j2` under skills section.
- Update `issue-flow config add` / `agent.py` config guide strings for new keys.
- `AGENTS.md` / `rules/_body.md.j2`: one-line pointer under optional features (gated on `step_directives`).

## Files to touch

| Path | Change |
|------|--------|
| `src/issue_flow/step_profiles.toml` | **New** — packaged stem → profile map |
| `src/issue_flow/step_profiles.py` | **New** — load, merge overrides, validate |
| `src/issue_flow/config.py` | Resolvers + `template_context()` keys |
| `src/issue_flow/modes.py` | `read_*` / `write_config` for new keys + `[issueflow.step_profiles]` |
| `src/issue_flow/cli.py` | `config add` seed new keys |
| `src/issue_flow/agent.py` | Config guide text |
| `src/issue_flow/templating.py` | Thread `step_profile` per skill stem into render context |
| `src/issue_flow/templates/skills/_model_directive.md.j2` | **New** shared partial |
| `src/issue_flow/templates/skills/iflow_*/SKILL.md.j2` | Include partial (all 16 lifecycle skills) |
| `src/issue_flow/templates/commands/iflow-*.md.j2` | Mirror include where command twins exist |
| `src/issue_flow/templates/skills/iflow_pick/SKILL.md.j2` | Label announcement block (gated) |
| `src/issue_flow/templates/rules/_body.md.j2` | Optional pointer |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | Document feature |
| `tests/test_config.py` | Resolution / precedence tests |
| `tests/test_templating.py` | Directive present/absent; economy vs reasoning text |
| `tests/test_init.py` | Scaffold smoke for new section |
| `.issueflows/00-tools/verify_scaffold.py` | Assert markers if useful |
| `.issueflows/04-designs-and-guides/step-model-directives.md` | **New** design note |

**Out of scope this PR:** `caveman` / `grill_me` directives (not iflow steps); runtime model enforcement; Codex/Claude model-picker APIs.

## Test strategy

```bash
uv run pytest tests/test_config.py tests/test_templating.py tests/test_init.py -q
uv run ruff check src/ tests/
```

Add tests for:

- `step_directives = false` → no `MODEL & EXECUTION DIRECTIVE` in rendered `iflow-plan` skill.
- Default `iflow_init` → economy wording; `iflow_plan` → reasoning wording.
- `[issueflow.step_profiles]` override flips a stem.
- Config beats env for `step_directives`.
- `iflow_pick` template includes label hint block when `model_label_flows` true (if shipped in v1).

## Open questions

1. **Label overrides in v1?** Plan includes optional `model_label_flows` + pick announcement (low cost). OK to ship, or defer to follow-up?
2. **Tier names** — `economy` / `reasoning` vs `fast` / `deep`? Recommendation: **economy / reasoning** (matches issue wording).
3. **Per-step override table name** — `[issueflow.step_profiles]` vs `[issueflow.step_models]`? Recommendation: **step_profiles** (profile is the concept, not a model id).
4. **Yolo default** — keep **reasoning** (plan+start inside chain) or downgrade whole yolo to **economy** because issues are small? Recommendation: **reasoning** — yolo still plans and implements.

---

**Confirm:** Accept → `/iflow-start` · Revise → say what to change · Abort
