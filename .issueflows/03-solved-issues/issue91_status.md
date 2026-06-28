# Issue #91 status: add config-driven always-on caveman style (caveman_default)

Interactive `/iflow-fix` session. Individual fixes are recorded below and landed
together via `/iflow-close`.

- [x] Done

## Iterative fixes log

- 2026-06-28 — Added opt-in config-driven always-on caveman style
  (`[issueflow].caveman_default`, default `false`; `ISSUEFLOW_CAVEMAN_DEFAULT`
  env fallback; persisted config beats env).
  - `modes.read_caveman_default()` reader; `Settings.resolve_caveman_default()`
    + new `caveman_default` template-context key (`config.py`, with `_env_flag`).
  - `rules/_body.md.j2`: caveman block now branches on `caveman_default`
    (always-on pointer vs. existing off-by-default wording), still gated on
    `"caveman" in included_skills`. The always-on text reaching the
    `alwaysApply: true` rule is what re-arms caveman each session.
  - `init.py`: commented `ISSUEFLOW_CAVEMAN_DEFAULT=false` hint in the starter
    `.env`.
  - Docs: README Modes note + config-table row; design guide
    `04-designs-and-guides/caveman-skill.md` updated with the #91 decision.
  - Tests: `test_config.py` (context key + resolution order), `test_modes.py`
    (reader), `test_templating.py` (pointer wording switch).
  - Verified: `uv run pytest` -> 258 passed; `uv run ruff check src/ tests/`
    clean; smoke test of `config.toml caveman_default = true` renders the
    always-on pointer.
