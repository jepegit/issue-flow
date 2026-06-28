# Caveman skill

Context: issue #81 — ship an optional "caveman" response-style skill (terse,
token-greedy; keep technical substance, drop filler). Full mode only, English
only — no intensity table, no multi-language.

## Decision

- The caveman behavior ships as a regular Agent Skill template at
  `src/issue_flow/templates/skills/caveman/SKILL.md.j2`, registered as the
  `caveman` stem in `SKILL_DIRS` (templating.py).
- It is part of the `standard` mode (which selects `skills = "all"`) and is
  excluded from `simple` (whose explicit skill list omits it). Mode membership —
  not a new CLI flag — gates whether it is scaffolded. `_prune_excluded_surfaces`
  already iterates `SKILL_DIRS`, so switching `standard -> simple` removes it.
- Stem name is `caveman` (no `iflow_` prefix) -> output folder `skills/caveman/`,
  because it is a behavior skill, not a workflow command.
- Unlike the workflow skills, its frontmatter is **model-invocable** (no
  `disable-model-invocation: true`): it is dormant until the user asks for it
  ("caveman" / "token greedy") and turns off via "stop caveman" / "normal mode".
- It is **registered in the rules managed block** (`rules/_body.md.j2`, shared by
  `AGENTS.md`, `CLAUDE.md`, and the always-applied `.mdc` rule) as a short,
  membership-gated *pointer* (`{% if "caveman" in included_skills %}`). The
  pointer documents existence + toggle words only; the always-on behavior text
  lives in the skill, so the always-applied rule never forces caveman on.

## Alternatives considered

- A dedicated CLI flag (`--with-caveman`) or a separate built-in caveman mode —
  rejected in favor of "in standard mode" per issue clarification (simpler, no
  new persisted concept).
- Inlining the full caveman ruleset into `AGENTS.md` — rejected: the shared body
  feeds an `alwaysApply: true` rule, so it would force caveman on by default.

Link: https://github.com/jepegit/issue-flow/issues/81

## Follow-up: opt-in always-on default (issue #91)

Context: users wanted a per-project way to make caveman the default style,
without re-asking every session.

### Decision

- New **opt-in** config key `[issueflow].caveman_default` (bool, default
  `false`), with an `ISSUEFLOW_CAVEMAN_DEFAULT` env fallback. Resolution order
  mirrors `mode`: persisted `config.toml` > env > default. The persisted value
  beats the env so a stray env var can't flip it on `update`
  (`Settings.resolve_caveman_default`; reader `modes.read_caveman_default`).
- Surfaced to templates as the `caveman_default` context key. The caveman block
  in `rules/_body.md.j2` now branches: when `caveman_default` is true (and
  `caveman` is in `included_skills`) it renders an **always-on** pointer; the
  pointer reaching the `alwaysApply: true` rule is exactly what re-arms caveman
  each session. Default stays off-by-default, preserving #81 behavior.
- This intentionally revisits the #81 rejection of "force caveman on by default":
  it is no longer the default — it only happens when a project explicitly opts in,
  so the always-applied rule stays inert unless the user asked for it.

### Alternatives considered

- A `--caveman-default` CLI flag — rejected to match the existing config-key
  pattern (`mode`) and keep the toggle editable in `config.toml` + re-`update`,
  not re-`init`.
- A paste-in snippet for the user's unmanaged `AGENTS.md` — viable but not
  discoverable; the config key plus managed-block rendering keeps it consistent
  across `AGENTS.md` / `CLAUDE.md` / `.mdc`.

Link: https://github.com/jepegit/issue-flow/issues/91
