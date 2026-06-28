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
