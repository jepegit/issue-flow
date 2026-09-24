# Issue #353: docs: fix dead external links found by the docs link check

Source: https://github.com/jepegit/issue-flow/issues/353

## Original issue text

## Context and spec

Found by the Stage 1 adversarial review of epic #341. The new `docs-links` CI job (#344) reports 6 dead **external** links. That check is non-blocking, but the epic goal is that readers never hit a 404:

- `https://iflow-graphify.net/` does not resolve. It is a mangled `https://graphify.net/`, left over from the #74 `issue-*` → `iflow-*` rename. There are 16 occurrences, including templates that ship to every scaffolded project: `templates/rules/_body.md.j2`, `templates/commands/iflow-graphify.md.j2`, `templates/skills/iflow_graphify/SKILL.md.j2`, `templates/docs/issue-workflow.md.j2`, plus `docs/graphify.md`, `README.md` and the rendered copies (`AGENTS.md`, `docs/issue-workflow.md`, `.cursor/…`).
- `https://github.com/safishamsi/graphify/blob/main/LICENSE` → 404. The default branch is `v8`: use `https://github.com/safishamsi/graphify/blob/v8/LICENSE` (200).
- `https://lychee.cli.rs/installation/` → 404. Added by #344 in `docs/developing.md` and `scripts/check_doc_links.sh`. Use `https://lychee.cli.rs/guides/getting-started/` (200).
- `https://packaging.python.org/en/latest/specifications/pep-0440/` → 404 (`docs/developing.md`). Use `https://packaging.python.org/en/latest/specifications/version-specifiers/` (200).

Fix the templates first, then re-render this repo's scaffold (`uv run scripts/update_issueflow_setup.py`). Extend `tests/test_doc_links.py` to reject `iflow-graphify.net`.

**Goal:** the non-blocking external step of the `docs-links` job reports 0 errors (or only transient ones), and `grep -rn 'iflow-graphify\.net' docs src README.md AGENTS.md` returns nothing.

**Model:** deep

Depends on: #344

Part of epic #341.
