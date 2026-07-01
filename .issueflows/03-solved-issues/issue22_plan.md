# Plan: Issue #22 — Modern python best practices and init options

## Goal

Add `--skill-level` parameter to `issue-flow init` (plus `ISSUEFLOW_SKILL_LEVEL` env var) so users can control scaffolding complexity. Advanced users get opinionated quality gates (type checking, strict linting config recommendations) in the project brief and/or separate design docs; casual users get the current minimal scaffold unchanged.

## Constraints

### Scope limits

- Skill level *only* affects what **reference guidance** is written into `.issueflows/04-designs-and-guides/` during `init`. It does **not** auto-install tools, modify `pyproject.toml`, or create pre-commit hooks — those remain user actions the guidance describes.
- The parameter controls *documentation content*, not code behavior. Tests, commands, and skills remain identical across skill levels.
- Back-compat: the default (`standard`) matches current behavior — no new mandatory steps for existing users.

### Prior art

- None found (toolbox + grep + graph checked).

## Approach

### 1. Define skill levels

Three levels in ascending complexity order (open to bikeshed):

- **`basic`** — current minimal scaffold, no quality tooling recommendations.
- **`standard`** (default) — same as `basic` (preserves back-compat).
- **`advanced`** — adds a design doc (`.issueflows/04-designs-and-guides/python-quality-tools.md`) with opinionated recommendations: type checking (mypy/pyright), strict ruff config, pre-commit hooks, pytest coverage reporting. The doc is *advisory*: agents read it during planning/implementation but must still ask the user before installing anything.

(Alternatively: name them `casual`, `standard`, `advanced` to match the issue wording.)

### 2. CLI and config plumbing

- **CLI:** add `--skill-level` option to `issue-flow init` (accepts `basic` | `standard` | `advanced`, defaults to `standard`).
- **Env var:** `ISSUEFLOW_SKILL_LEVEL` (same values, same default).
- **Persisted config:** write `[issueflow].skill_level` to `.issueflows/config.toml` so `update` honours the init-chosen level (mirrors `mode` and `caveman_default` patterns).
- **Resolution order:** CLI `--skill-level` > persisted `config.toml` > env `ISSUEFLOW_SKILL_LEVEL` > default (`standard`).

### 3. Conditional scaffolding

- **Template context:** add `skill_level` to `Settings.template_context()` (derived via new `resolve_skill_level(project_root)` helper).
- **Python quality-tools doc:** new template `src/issue_flow/templates/designs/python-quality-tools.md.j2`, gated on `{% if skill_level == 'advanced' %}` in the design manifest builder.
- **Project brief extension (optional):** alternatively, branch the existing `this-project.md.j2` to inject an **Optional quality tools** section when `skill_level == 'advanced'` (cleaner UX: one file to read). Open question.

### 4. Content of the advanced quality doc

Terse markdown bullets with:

- **Type checking:** recommend mypy or pyright; show `pyproject.toml` snippet for strict config.
- **Linting/formatting:** recommend ruff with strict rule selection (e.g. `extend-select = ["I", "N", "UP"]`); link to ruff docs.
- **Pre-commit:** show `.pre-commit-config.yaml` stanza for ruff + mypy; remind to `pre-commit install`.
- **Testing:** recommend pytest with coverage (`--cov`); show `pyproject.toml` snippet for coverage config.
- **Guidance for agents:** "Before making code changes, ask the user whether to add/configure these tools. Never auto-install without confirmation."

### 5. `.env` doc update

Add the new env var to `_DOTENV_KEYS` tuple so it appears in commented form in fresh `.env` files.

### 6. Docs and tests

- Update README to document `--skill-level`.
- Test: `test_init_advanced_skill_level_creates_quality_doc()` — run `init(..., skill_level="advanced")`, assert `.issueflows/04-designs-and-guides/python-quality-tools.md` exists + contains "mypy" / "ruff" / "pre-commit".
- Test: `test_init_standard_skill_level_omits_quality_doc()` — run `init()` (default), assert the quality doc is **not** created.
- Test: `test_init_skill_level_persisted_in_config()` — `init(..., skill_level="advanced")`, read `config.toml`, assert `skill_level = "advanced"`.

## Files to touch

1. **`src/issue_flow/cli.py`** — add `--skill-level` option to the `init` command, pass to `run_init`.
2. **`src/issue_flow/init.py`** — add `skill_level` param to `run_init()` signature; pass to `Settings.template_context()`.
3. **`src/issue_flow/config.py`** — add `resolve_skill_level(project_root)` method (mirrors `resolve_caveman_default` pattern); add `skill_level` to `seed_config_values()` and `template_context()`.
4. **`src/issue_flow/modes.py`** — add `read_skill_level(config_path)` / `write_skill_level(config_path, level)` helpers (mirrors caveman/grill-me pattern); update `write_default_config()` to include the new key.
5. **`src/issue_flow/templates/designs/python-quality-tools.md.j2`** — new template with the advanced quality guidance.
6. **`src/issue_flow/templating.py`** — add `"designs/python-quality-tools.md.j2"` to the design manifest when `context["skill_level"] == "advanced"`.
7. **`tests/test_init.py`** — add 3 new tests (see above).
8. **`README.md`** — document the new `--skill-level` option + env var.
9. **`.env` (in scaffolded projects)** — update `_DOTENV_KEYS` in `init.py` to include `ISSUEFLOW_SKILL_LEVEL`.

## Test strategy

Use `uv run pytest tests/test_init.py` (the project's documented test command). Add tests for:

- Advanced skill level creates `python-quality-tools.md` with expected content.
- Standard/basic skill levels omit the quality doc.
- Skill level is persisted in `config.toml`.
- `.env` includes the commented `ISSUEFLOW_SKILL_LEVEL` line.
- `update` honours the persisted skill level (no new doc creation when re-running update on a basic-level project).

Run full suite after edits to catch regressions.

## Open questions

1. **Skill level names:** `basic` / `standard` / `advanced` (matches code conventions) vs `casual` / `standard` / `advanced` (matches issue wording)? Recommend **`basic` / `standard` / `advanced`** for consistency with other tool ecosystems.

2. **Doc location:** separate `python-quality-tools.md` (cleaner separation, easier to extend with non-Python quality tools later) vs branch the existing `this-project.md` to inject a section when advanced (one file to read, less clutter)? Recommend **separate file** for extensibility (future: `js-quality-tools.md` for TypeScript projects).

3. **Other quality dimensions:** should advanced also recommend commit message linting, changelog automation, or CI config templates? For scope control, recommend **punting to a future issue** — start with Python type/lint/test tooling only.
