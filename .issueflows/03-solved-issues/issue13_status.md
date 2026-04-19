# Issue #13 status: Rename environment variable

## Status

- [x] Done

## What was done

Renamed the vendor-specific `ISSUEFLOW_CURSOR_DIR` environment variable (and the related internal identifiers) to the IDE-agnostic `ISSUEFLOW_AGENT_DIR`.

### Code / config

- `src/issue_flow/config.py`: `Settings.cursor_dir` -> `Settings.agent_dir`; env lookup switched to `ISSUEFLOW_AGENT_DIR`; `template_context()` now emits the key `"agent_dir"`.
- `src/issue_flow/init.py`: `_DOTENV_KEYS` entry updated so new or amended `.env` files document `ISSUEFLOW_AGENT_DIR`.
- `src/issue_flow/templating.py`: every `{cursor_dir}` placeholder in `TEMPLATE_MANIFEST` (and the `resolve_output_path` docstring) is now `{agent_dir}`.

### Jinja templates

Replaced `{{ cursor_dir }}` with `{{ agent_dir }}` in:

- `src/issue_flow/templates/skills/issueflow_issue_init/SKILL.md.j2`
- `src/issue_flow/templates/skills/issueflow_issue_start/SKILL.md.j2`
- `src/issue_flow/templates/skills/issueflow_issue_close/SKILL.md.j2`
- `src/issue_flow/templates/docs/cursor-issue-workflow.md.j2`
- `src/issue_flow/templates/commands/issue-close.md.j2`

### Docs

- `README.md`: env-var table row renamed and description made IDE-agnostic.

### Tests

- `tests/test_config.py`, `tests/test_init.py`, `tests/test_templating.py`: updated assertions, context keys, and path-template strings to match the new names.

## Verification

- `uv run pytest` -> 30 passed.
- `rg "cursor_dir|ISSUEFLOW_CURSOR_DIR"` across `src/` and `tests/` -> no matches (only the original issue markdown under `.issueflows/` still mentions the old name, which is expected and gets archived with the issue).

## Behavioural notes / migration

- The default directory value is still `.cursor`; only the env-var and internal identifier names changed.
- No backwards-compat fallback was added: projects that explicitly set `ISSUEFLOW_CURSOR_DIR` in their `.env` will silently revert to the default `.cursor` until they rename it to `ISSUEFLOW_AGENT_DIR`. Worth calling out in release notes for the next version.

## Remaining work

None.
