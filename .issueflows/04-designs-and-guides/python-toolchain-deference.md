# Python toolchain deference (don't hard-mandate uv)

Context: issue #58 — issue-flow scaffolds rules that hard-mandated `uv`
("Use `uv` exclusively, never pip/poetry"). When scaffolded into a project that
uses a different toolchain (notably **conda**), those rules fight the project's
real setup: conda projects need Python and `pytest` run inside the **activated
conda environment**, not via `uv run`.

## Decision

The scaffolded rules **defer to the project's existing, documented toolchain**.
`uv` remains the *default/example* (issue-flow itself is uv-managed, and it's the
assumption for freshly scaffolded projects), but it is framed as one option,
conditional on what the project documents.

- Source of truth: the "Running python" section of
  [`templates/rules/_body.md.j2`](../../src/issue_flow/templates/rules/_body.md.j2),
  which feeds `AGENTS.md`, `CLAUDE.md`, and the Cursor `.mdc` (one body, three
  outputs — see [editor-profiles.md](editor-profiles.md)).
- Structure: a "respect existing tooling first" preamble + one tool-neutral
  principle (never bare `python ...`), then branches for **conda** (activate the
  env / `conda run -n <env>`), **uv** (the default), and **other** (venv/pip/
  poetry).
- The prescriptive `uv run` / `uv add …` phrasings in the `issue-start` and
  `issue-plan` command/skill templates were softened to "the project's documented
  toolchain (e.g. `uv run`, or inside the activated conda env)".

## Alternatives considered

- **`ISSUEFLOW_PYTHON_RUNNER` config toggle** (uv|conda|pip) driving rendered
  examples — rejected: more machinery than the issue warranted, and deference is
  a *runtime* concern (the agent reads the project's rules) rather than a
  scaffold-time switch. Wording-only keeps one editor-neutral body.
- **Genericising `uv version --bump`** in the version-bump templates — left
  as-is: it's genuinely uv-specific, gated behind an opt-in `bump` argument, and
  already skips when there's no bumpable `pyproject.toml`.

## Notes

- The body is intentionally editor-neutral (no `{{ editor_name }}`) so shared
  `AGENTS.md` content stays identical across editors.
- This repo dogfoods its own scaffold; after template edits, regenerate via
  `scripts/update_issueflow_setup.py` (≈ `issue-flow update .`) so the root
  `AGENTS.md` managed block and `.cursor/rules/issueflow-rules.mdc` match.
