# Issue #81 plan: add caveman skill

Full plan of record: `.cursor/plans/caveman_skill_1e8ca36e.plan.md`.

## Goal
Ship a "caveman" terse-response Agent Skill that `issue-flow init` scaffolds as
part of the **standard** mode. Full mode only, English only. Registered as a
membership-gated pointer in the rules/`AGENTS.md` managed block; dormant until
the user activates it ("caveman" / "token greedy"), off via "stop caveman" /
"normal mode".

## Approach
1. New skill template `src/issue_flow/templates/skills/caveman/SKILL.md.j2`
   (model-invocable frontmatter; full intensity only; English only).
2. Register `caveman` stem in `SKILL_DIRS` (templating.py) -> in `standard`
   (`"all"`), excluded by the explicit `simple` list; auto-pruned on switch.
3. Gated pointer in `rules/_body.md.j2` (`{% if "caveman" in included_skills %}`).
4. Docs: README note + `04-designs-and-guides/caveman-skill.md`.
5. Tests: bump manifest counts; add caveman coverage (templating + modes).

## Decisions
- In `standard` mode (per clarification), not behind a CLI flag.
- Stem `caveman` -> folder `skills/caveman/` (behavior skill, no `iflow_` prefix).
- Rules body carries a *pointer only* (not the always-on ruleset) so the
  always-applied `.mdc` rule never forces caveman on.
