# Issue #32 status: add grill-me skill

- [x] Done

## Summary

Added mattpocock's `grill-me` as an issue-flow Agent Skill (a relentless planning
interview), tuned to the issue-flow workflow, with a config-driven on-by-default
toggle that mirrors the `caveman` / `caveman_default` mechanism (issue #91).

## What was done

- **New skill** `src/issue_flow/templates/skills/grill_me/SKILL.md.j2` —
  model-invocable planning interview: one question at a time, each with a
  recommended answer; explore the code/issue instead of asking when answerable;
  fold the resolved decisions into `issue<N>_plan.md`. Off via "stop grilling" /
  "normal mode".
- **Mode membership** — registered `grill_me` in `SKILL_DIRS` (`templating.py`).
  Part of `standard` (`skills = "all"`), omitted from `simple`. Output folder
  `skills/grill-me/`.
- **Config flag** mirroring caveman — `[issueflow].grill_me_default` (default
  `false`) + `ISSUEFLOW_GRILL_ME_DEFAULT` env fallback. Resolution order
  `config.toml` > env > `false`; persisted wins.
  - `modes.read_grill_me_default()` reader.
  - `Settings.resolve_grill_me_default()` + new `grill_me_default` template
    context key (`config.py`).
  - `ISSUEFLOW_GRILL_ME_DEFAULT` hint added to the starter `.env` (`init.py`).
- **Templates** — `rules/_body.md.j2` gained a membership-gated "Planning aids"
  pointer that branches on `grill_me_default` (always-on vs on-request);
  `iflow_plan` SKILL gained step 5a (grill before drafting when on; available on
  request when off).
- **Docs** — README modes note + env-table row; new design guide
  `04-designs-and-guides/grill-me-skill.md`; HISTORY.md `[Unreleased]` entry.
- **Tests** — mirrored the caveman tests across `test_modes.py`, `test_config.py`,
  and `test_templating.py`; bumped skill-count assertions (16->17 skills; cursor
  18->19; codex manifest 17->18).

## Verification

- `uv run pytest` — 269 passed.
- `uv run ruff check src/ tests/` — clean.

## Remaining work

None. Fully resolved.
