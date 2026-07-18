# Status — Issue #168: fix GitHub Linguist skew

- [x] Done

## What's done

- Plan accepted (opt-in `linguist_attributes` + managed `.gitattributes`).
- Config plumbing: `DEFAULT_LINGUIST_ATTRIBUTES`, `read_linguist_attributes`,
  `Settings.resolve_linguist_attributes`, `seed_config_values`,
  `write_default_config` / `config add`.
- `ensure_linguist_gitattributes` + `maybe_ensure_linguist_gitattributes`;
  wired into `init` and `update`.
- Docs (`docs/configuration.md`) + design note
  (`.issueflows/04-designs-and-guides/linguist-gitattributes.md`).
- Dogfood: `.issueflows/config.toml` `linguist_attributes = true` + root
  `.gitattributes`.
- Tests: modes/config/cli + `tests/test_linguist_attributes.py` (512 passed).
- HISTORY.md Unreleased bullet; archived to `03-solved-issues/`.

## Remaining work

- None.
