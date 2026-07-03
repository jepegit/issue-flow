# Step model directives

**Context.** Issue #113: different iflow steps benefit from different model
trade-offs (speed vs reasoning depth).

**Decision.**

- Each lifecycle skill/command carries an advisory
  `### MODEL & EXECUTION DIRECTIVE` section baked at `issue-flow update`.
- Profiles: **`economy`** (speed/token savings) or **`reasoning`** (design depth).
  Packaged defaults live in `src/issue_flow/step_profiles.toml`; projects override
  per stem in `[issueflow.step_profiles]`.
- Config knobs under `[issueflow]` (persisted > env > default):
  `step_directives` (master toggle, default `true`), `model_label_flows`
  (default `false`), `deep_model_label` / `fast_model_label` (defaults
  `"deep"` / `"fast"`). `/iflow-pick` announces label-based session overrides
  only — no auto-dispatch.
- Cursor-specific hint when `editor == "cursor"`: Auto/fast vs thinking model.
  No SKILL.md `model:` frontmatter — Cursor does not support forcing a model
  from skills.

**Alternatives considered.**

- Runtime `config.toml` reads by agents — rejected; bake at render like other knobs.
- Per-issue model enforcement — rejected; advisory only.

**Link.** Issue #113.
