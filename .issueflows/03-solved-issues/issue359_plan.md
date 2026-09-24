# Plan — Issue #359: docs: reorder the configuration page around common changes

(Epic #341 stage 3, via the resumed /iflow-drive run 2; yolo chain, auto-confirmed. Planned as yolo: no. The scope turned out to be a docs reorganisation plus one small test file, so I went ahead.)

## Goal

The page starts with Common changes, every `config.toml` key appears exactly once in a full table (checked by a test), and the prose has no bare issue numbers.

## Approach

- New top: a short intro (`config set` + `update` + `config show`), then **Common changes** (9 rows with `config set` examples).
- **All settings:** one table of all 38 `config_ops.CONFIG_KEYS` (key · type · default · effect). Defaults taken from `issue-flow config show --json` on a fresh project. It replaces the old "Skill-behaviour knobs" table, its TOML sample and the env-fallback list; one sentence documents the `ISSUEFLOW_<KEY>` pattern instead (verified: every key has it).
- The topical sections (Modes … Linguist) stay word for word, minus the issue numbers.
- **How settings are resolved** moves to the end: precedence, user-global, the `ISSUEFLOW_LOCKED` exception, environment-only variables (the five folder/editor vars), and creating `config.toml`.
- Test `tests/test_doc_configuration.py`: keys vs `CONFIG_KEYS` (essential), Common changes comes first, no bare issue numbers.

## Deviation from the spec

- **No "modes" column.** Where a knob only applies with certain commands installed, the Effect text says so (e.g. `label_flows`, `model_label_flows`). A per-knob modes column would mostly read "all".
