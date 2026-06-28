# Issue #96 status — `issue-flow config add`

- [x] Done

## What's done

- Plan confirmed (`issue96_plan.md`): 3 live keys only, `config add`, orchestrator in `agent.py`.
- `modes.write_default_config` — tomlkit writer; create-with-comments when missing, upsert 3 keys preserving content on `--force`, no-op (`False`) otherwise. Plus `_commented_issueflow_table` helper.
- `Settings.seed_config_values` (`config.py`) — env→default for `mode`/`caveman_default`/`grill_me_default`, ignores persisted config.
- `agent.run_config_add` + `_print_config_guide` — orchestrator with exists/`--force` handling, `--json`, manual-edit guide.
- `config` Typer sub-app + `add` command wired in `cli.py` (`-C`, `--force`, `--json`).
- Tests: 6 new in `tests/test_cli.py` (help, defaults, env-read, no-clobber, `--force` upsert+preserve). Full suite green: 274 passed, ruff clean.
- README Configuration section: "Creating `config.toml`" subsection.

## Remaining work

- None. Closed via `/iflow-close`: version bumped `0.4.1b1` → `0.4.1b2`, HISTORY promoted, committed/pushed, PR opened.
