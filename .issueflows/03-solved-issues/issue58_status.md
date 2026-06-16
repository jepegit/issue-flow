# Status — issue #58: Allow for not using uv

- [x] Done

## What landed

Made the scaffolded issue-flow rules **defer to a project's existing, documented
Python toolchain** instead of hard-mandating `uv`, with explicit conda handling.

### Templates (source of truth)

- `src/issue_flow/templates/rules/_body.md.j2` — rewrote the "Running python" /
  "Package Management with `uv`" sections into a deferential block: a "respect
  the project's existing toolchain first" preamble, one tool-neutral principle
  (never bare `python ...`), then branches for **conda** (run scripts and
  `pytest` inside the activated conda env; `conda activate` / `conda run -n`),
  **uv** (the default/example), and **other** (venv/pip/poetry). The old
  "Use `uv` exclusively" mandate is gone.
- `src/issue_flow/templates/skills/issueflow_issue_start/SKILL.md.j2` — softened
  the "Project conventions" bullet and the frontmatter description to defer to
  the documented toolchain (uv **or** activated conda env).
- `src/issue_flow/templates/commands/issue-start.md.j2` — softened the step-2
  toolchain parenthetical.
- `src/issue_flow/templates/commands/issue-plan.md.j2` and
  `src/issue_flow/templates/skills/issueflow_issue_plan/SKILL.md.j2` — softened
  the "Test strategy" example to "the project's documented test command".

### Regenerated (dogfooded scaffold)

- Ran `scripts/update_issueflow_setup.py` (≈ `issue-flow update .`). Refreshed
  the root `AGENTS.md` managed block, `.cursor/rules/issueflow-rules.mdc`, all
  `.cursor/commands/*` and `.cursor/skills/*`, and `docs/issue-workflow.md`.

### Docs & tests

- `.issueflows/04-designs-and-guides/python-toolchain-deference.md` — new design
  note recording the decision and the rejected `ISSUEFLOW_PYTHON_RUNNER` toggle.
- `tests/test_templating.py` — new
  `test_rules_body_defers_to_project_toolchain_and_covers_conda` asserting all
  three rules outputs defer to the project, cover conda, keep `uv run` as the
  default, and no longer say "use uv exclusively".

## Verification

- `uv run pytest` → **141 passed**.
- `uv run ruff check src/ tests/` → clean.

## Decisions (per plan open questions)

1. Wording-only deference (no `ISSUEFLOW_PYTHON_RUNNER` config var). 
2. Left `uv version --bump` references untouched (uv-specific, opt-in, already
   skippable when there's no bumpable `pyproject.toml`).
3. Added the regression test.

## Remaining

- None. Ready for `/issue-close`.
