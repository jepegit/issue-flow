# Grill-me skill

Context: issue #32 — ship mattpocock's `grill-me` design-review skill as an
issue-flow skill, tuned to our workflow. It should not be active in `standard`
mode by default, but a project should be able to turn it on during planning, and
custom modes should be able to include it.

## Decision

- The grilling behavior ships as a regular Agent Skill template at
  `src/issue_flow/templates/skills/grill_me/SKILL.md.j2`, registered as the
  `grill_me` stem in `SKILL_DIRS` (templating.py) -> output folder
  `skills/grill-me/` (underscores -> hyphens; matches the `name: grill-me`
  frontmatter).
- It is part of the `standard` mode (which selects `skills = "all"`) and excluded
  from `simple` (whose explicit skill list omits it). Mode membership — not a new
  CLI flag — gates whether it is scaffolded, mirroring `caveman`.
- Like `caveman` (and unlike the workflow skills), its frontmatter is
  **model-invocable** (no `disable-model-invocation: true`): it is dormant until
  the user asks for it ("grill me") and turns off via "stop grilling" /
  "normal mode".
- Adapted to issue-flow philosophy: it is a **planning** aid. One question at a
  time, each with a recommended answer; explore the code/issue/designs instead of
  asking when answerable; resolve the decision tree, then feed the agreed
  decisions into `issue<N>_plan.md`. It questions and aligns — it does not write
  code (that stays with `/iflow-start`).

## On-by-default toggle (mirrors caveman #91)

This directly mirrors the `caveman_default` mechanism from issue #91 (see
`caveman-skill.md`), per the request to "set it on by default in config.toml like
caveman".

- New **opt-in** config key `[issueflow].grill_me_default` (bool, default
  `false`), with an `ISSUEFLOW_GRILL_ME_DEFAULT` env fallback. Resolution order
  mirrors `mode` / `caveman_default`: persisted `config.toml` > env > default.
  The persisted value beats the env so a stray env var can't flip it on `update`
  (`Settings.resolve_grill_me_default`; reader `modes.read_grill_me_default`).
- Surfaced to templates as the `grill_me_default` context key. Two membership-
  gated surfaces branch on it (both gated on `"grill_me" in included_skills`):
  - `rules/_body.md.j2` — a "Planning aids" pointer (always-on vs available-on-
    request). The pointer reaching the `alwaysApply: true` rule is what arms
    grilling each session.
  - `skills/iflow_plan/SKILL.md.j2` — step 5a: when on, run a grilling pass
    before drafting the plan; when off, note that grilling is available on
    request.
- Default stays off-by-default, honoring the issue's "not active in standard by
  default" while still letting projects opt in and custom modes include it.

## Alternatives considered

- Keeping `grill_me` out of `standard` entirely (install only via custom mode) —
  rejected: a default-on flag needs the skill installed to point at, and caveman
  parity (dormant-in-standard + a `_default` flag) satisfies every clause of the
  issue without a new persisted "install" concept.
- A dedicated CLI flag (`--with-grill` / `--grill-default`) — rejected to match
  the existing config-key pattern (`mode`, `caveman_default`), editable in
  `config.toml` + re-`update` rather than re-`init`.

Link: https://github.com/jepegit/issue-flow/issues/32
