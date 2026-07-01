# Status: Issue #22

- [x] Done

## What's done

- Plan confirmed
- Added `--skill-level` CLI option to `init` command
- Added `ISSUEFLOW_SKILL_LEVEL` env var support in _DOTENV_KEYS
- Implemented `resolve_skill_level()` in config.py
- Added skill level read/write helpers in modes.py (read_skill_level, write_skill_level)
- Updated write_default_config and _commented_issueflow_table to include skill_level
- Updated template_context to accept and pass skill_level
- Updated run_init and run_update to validate/persist/pass skill_level
- Created python-quality-tools.md.j2 template
- Updated build_manifest to conditionally include quality doc when skill_level == "advanced"
- Added comprehensive tests (test_init_skill_level.py with 7 tests)
- Updated README with skill levels section and env var docs
- All tests pass (281 tests)
- Lint checks pass

## Remaining work

None
